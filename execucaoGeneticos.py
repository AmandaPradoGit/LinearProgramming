import random
from typing import List, Optional, Tuple
import argparse
import sys
import logging


def _gerar_populacao_com_matriz(tamanho: int, pop_size: int,
                                matriz_distancias) -> List[List[int]]:
    """Gera população mista: metade aleatória, metade por heurística nearest
    neighbor usando a matriz de distâncias real.

    Isso acelera a convergência sem perder diversidade inicial.
    """
    populacao = []
    metade = pop_size // 2

    # Metade aleatória
    for _ in range(metade):
        individuo = list(range(tamanho))
        random.shuffle(individuo)
        populacao.append(individuo)

    cidades_inicio = random.sample(range(tamanho), min(pop_size - metade, tamanho))
    for inicio in cidades_inicio: 
        visitados = [False] * tamanho
        rota = [inicio]
        visitados[inicio] = True
        for _ in range(tamanho - 1):
            atual = rota[-1]
            melhor_dist = float('inf')
            melhor_cidade = -1
            for c in range(tamanho):
                if not visitados[c] and matriz_distancias[atual][c] < melhor_dist:
                    melhor_dist = matriz_distancias[atual][c]
                    melhor_cidade = c
            rota.append(melhor_cidade)
            visitados[melhor_cidade] = True
        populacao.append(rota)

    while len(populacao) < pop_size:
        individuo = list(range(tamanho))
        random.shuffle(individuo)
        populacao.append(individuo)

    return populacao


# ---------------------------------------------------------------------------
# Métodos de seleção
# ---------------------------------------------------------------------------
def _selecionar_por_roleta(populacao: List[List[int]], fitness: List[float]) -> List[int]:
    """Seleção por roleta usando ranking linear (retorna cópia).

    Ordena por fitness CRESCENTE: o pior recebe rank 1, o melhor recebe rank N.
    Fitness = 1/(1+distancia), portanto maior fitness = menor distância = melhor.
    """
    n = len(populacao)
    if n == 0:
        return []
    
    indices_ordenados = sorted(range(n), key=lambda i: fitness[i])
    ranks = [0] * n
    for rank, idx in enumerate(indices_ordenados, start=1):
        ranks[idx] = rank  

    total = float(sum(ranks))
    escolha = random.uniform(0.0, total)
    acumulado = 0.0
    for idx, rank in enumerate(ranks):
        acumulado += rank
        if acumulado >= escolha:
            return populacao[idx][:]  # Fatiamento rápido para List[int]

    return populacao[indices_ordenados[-1]][:]


def _selecionar_por_torneio(populacao: List[List[int]], tournament_size: int,
                            distancias: List[float]) -> List[int]:
    """Seleção por torneio — escolhe o indivíduo com menor distância entre os amostrados."""
    n = len(populacao)
    if n == 0:
        return []
    k = min(tournament_size, n)
    indices = random.sample(range(n), k)
    melhor_idx = min(indices, key=lambda i: distancias[i])
    return populacao[melhor_idx][:]  # Fatiamento rápido para List[int]


def _selecionar_pais(populacao, fitness, distancias, metodo_selecao, tournament_size):
    ms = metodo_selecao.upper()
    if ms in ('TOURNAMENT', 'TORNEIO'):
        return _selecionar_por_torneio(populacao, tournament_size, distancias)
    if ms == 'DETERMINISTIC':
        melhor_idx = min(range(len(populacao)), key=lambda i: distancias[i])
        return populacao[melhor_idx][:]
    return _selecionar_por_roleta(populacao, fitness)


# ---------------------------------------------------------------------------
# Operadores genéticos
# ---------------------------------------------------------------------------

def _crossover_ordem(pai1: List[int], pai2: List[int]) -> List[int]:
    """Order Crossover (OX) — preserva a ordem relativa das cidades sem repetições."""
    n = len(pai1)
    filho = [-1] * n
    i, j = sorted(random.sample(range(n), 2))
    filho[i:j + 1] = pai1[i:j + 1]

    pos = (j + 1) % n
    for gene in pai2[j + 1:] + pai2[:j + 1]:
        if gene not in filho:
            filho[pos] = gene
            pos = (pos + 1) % n
    return filho


def _crossover_pmx(pai1: List[int], pai2: List[int]) -> List[int]:
    """Partially Mapped Crossover (PMX) — Versão Corrigida.

    Preserva mapeamentos de fatias e resolve colisões seguindo as cadeias corretamente.
    """
    n = len(pai1)
    filho = [None] * n
    i, j = sorted(random.sample(range(n), 2))

    # Copia o segmento do pai1 para o filho
    filho[i:j + 1] = pai1[i:j + 1]

    # Cria o mapeamento das relações entre o segmento de pai1 e pai2
    mapeamento = {pai1[k]: pai2[k] for k in range(i, j + 1)}

    # Preenche o restante das posições fora do segmento
    for k in range(n):
        if i <= k <= j:
            continue
        
        gene = pai2[k]
        # Se o gene do pai2 colidir com o segmento já copiado (pai1), segue a cadeia
        while gene in pai1[i:j + 1]:
            gene = mapeamento[gene]
            
        filho[k] = gene

    return [int(x) for x in filho]


def _mutacao_troca(individuo: List[int], taxa_mutacao: float) -> List[int]:
    """Mutação swap — troca dois genes. Opera sobre cópia (sem side-effect)."""
    resultado = individuo[:]
    if len(resultado) < 2:
        return resultado
    if random.random() < taxa_mutacao:
        i, j = random.sample(range(len(resultado)), 2)
        resultado[i], resultado[j] = resultado[j], resultado[i]
    return resultado


def _mutacao_inversao(individuo: List[int], taxa_mutacao: float) -> List[int]:
    """Mutação por inversão de segmento (2-opt local).

    Inverte a ordem dos genes entre duas posições aleatórias.
    Muito eficaz para TSP — desfaz cruzamentos de arestas.
    """
    resultado = individuo[:]
    if random.random() < taxa_mutacao:
        i, j = sorted(random.sample(range(len(resultado)), 2))
        resultado[i:j + 1] = resultado[i:j + 1][::-1]
    return resultado


def _mutacao_adaptativa(individuo: List[int], taxa_base: float,
                        geracoes_sem_melhora: int, patience: int) -> List[int]:
    """Mutação adaptativa — aumenta a taxa quando a população está estagnada."""
    if patience >= 1 and geracoes_sem_melhora > 0:
        fator = 1.0 + (geracoes_sem_melhora / patience) * 2.0
        taxa_efetiva = min(taxa_base * fator, 0.5)  # cap em 50%
    else:
        taxa_efetiva = taxa_base
    return _mutacao_inversao(individuo, taxa_efetiva)


# ---------------------------------------------------------------------------
# Otimização local: 2-opt
# ---------------------------------------------------------------------------

def _dois_opt(rota: List[int], cv, max_iter: int = 50) -> Tuple[List[int], float]:
    """Busca local 2-opt aplicada a uma rota.

    Tenta melhorar a rota trocando pares de arestas.
    Aplicado apenas ao elite para não encarecer demais o loop principal.
    """
    melhor = rota[:]
    melhor_dist = cv._calcular_distancia(melhor)
    melhorou = True
    iteracao = 0

    while melhorou and iteracao < max_iter:
        melhorou = False
        iteracao += 1
        for i in range(1, len(melhor) - 1):
            for j in range(i + 1, len(melhor)):
                nova = melhor[:i] + melhor[i:j + 1][::-1] + melhor[j + 1:]
                nova_dist = cv._calcular_distancia(nova)
                if nova_dist < melhor_dist:
                    melhor = nova
                    melhor_dist = nova_dist
                    melhorou = True
    return melhor, melhor_dist


def _validate_and_normalize_individuo(individuo: List[int], n: int) -> List[int]:
    """Garante que o indivíduo é uma permutação válida de 0..n-1.

    Se não for (duplicatas ou valores fora do intervalo), corrige removendo
    duplicatas e adicionando os genes faltantes ao final.
    """
    if len(individuo) != n or set(individuo) != set(range(n)):
        seen = set()
        novo = []
        for g in individuo:
            if 0 <= g < n and g not in seen:
                novo.append(g)
                seen.add(g)
        for g in range(n):
            if g not in seen:
                novo.append(g)
        return novo
    return individuo


# ---------------------------------------------------------------------------
# Resolução do método de seleção
# ---------------------------------------------------------------------------

def _resolver_metodo_selecao(selection: Optional[str], tournament_size: int,
                             pop_size: int, elitism: int) -> str:
    """Determina o método de seleção a usar.

    Prioridade: parâmetro explícito > inferência por heurística.
    """
    if selection:
        return selection.upper()
    if tournament_size >= 3:
        return 'TOURNAMENT'
    if elitism >= max(1, int(0.2 * pop_size)):
        return 'DETERMINISTIC'
    return 'ROULETTE'


# ---------------------------------------------------------------------------
# Algoritmo Genético principal — versão melhorada
# ---------------------------------------------------------------------------

def algoritmos_geneticos(cv, pop_size=50, generations=200,
                         selection='ROULETTE',
                         crossover_rate=0.9, mutation_rate=0.1,
                         tournament_size=3, elitism=1,
                         patience=50,
                         crossover_op='OX',
                         usar_2opt=True,
                         usar_mutacao_adaptativa=True,
                         **kwargs):
    
    if not getattr(cv, 'distancias', None):
        return "Gere o problema primeiro!"

    alias_map = {
        'tp': ('pop_size',       int),
        'tc': ('crossover_rate', float),
        'tm': ('mutation_rate',  float),
        'ng': ('generations',    int),
    }
    for alias, (param, tipo) in alias_map.items():
        if alias in kwargs and kwargs[alias] is not None:
            try:
                val = tipo(kwargs[alias])
                if param == 'pop_size':         pop_size       = val
                elif param == 'crossover_rate': crossover_rate = val
                elif param == 'mutation_rate':  mutation_rate  = val
                elif param == 'generations':    generations    = val
            except (ValueError, TypeError):
                pass

    report_interval = None
    if 'ig' in kwargs and kwargs['ig'] is not None:
        try:
            report_interval = int(kwargs['ig'])
        except (ValueError, TypeError):
            pass

    # --- Sanidade nos valores ---
    n = len(cv.distancias)
    pop_size    = max(10, pop_size)
    generations = max(1, generations)
    elitism     = max(0, min(elitism, pop_size // 2))

    selection_method = _resolver_metodo_selecao(
        selection, tournament_size, pop_size, elitism
    )
    crossover_fn = _crossover_pmx if crossover_op.upper() == 'PMX' else _crossover_ordem

    # --- População Inicial (Geração 0) ---
    pop = _gerar_populacao_com_matriz(n, pop_size, cv.distancias)
    pop = [_validate_and_normalize_individuo(ind, n) for ind in pop]

    valor_inicial_puro = min(cv._calcular_distancia(ind) for ind in pop)

    melhor_global        = None
    melhor_valor_global  = float('inf')
    geracoes_sem_melhora = 0
    gen_final = 0                 

    for gen in range(generations):
        gen_final = gen + 1

        # --- Avaliação ---
        distancias = [cv._calcular_distancia(ind) for ind in pop]

        # --- 2-opt no melhor da geração ---
        melhor_gen_idx = min(range(len(pop)), key=lambda i: distancias[i])
        if usar_2opt:
            candidato_2opt, dist_2opt = _dois_opt(pop[melhor_gen_idx], cv, max_iter=30)
            if dist_2opt < distancias[melhor_gen_idx]:
                pop[melhor_gen_idx] = candidato_2opt
                distancias[melhor_gen_idx] = dist_2opt

        # --- Atualiza melhor global ---
        melhor_geracao = min(range(len(pop)), key=lambda i: distancias[i])
        if distancias[melhor_geracao] < melhor_valor_global:
            melhor_valor_global  = distancias[melhor_geracao]
            melhor_global        = pop[melhor_geracao][:]
            geracoes_sem_melhora = 0
        else:
            geracoes_sem_melhora += 1

        # --- Log periódico ---
        if report_interval and gen % report_interval == 0:
            print(f"  Gen {gen:4d} | Melhor: {melhor_valor_global:.4f} "
                  f"| Sem melhora: {geracoes_sem_melhora}")

        # --- Critério de parada antecipada ---
        if patience > 0 and geracoes_sem_melhora >= patience:
            break

        # --- Fitness para roleta ---
        fitness = [1.0 / (1.0 + d) for d in distancias]

        # --- Nova geração ---
        nova_pop: List[List[int]] = []

        # Elitismo
        if elitism > 0:
            indices_ordenados = sorted(range(len(pop)), key=lambda i: distancias[i])
            for idx in indices_ordenados[:elitism]:
                nova_pop.append(pop[idx][:])

        # Cruzamento + mutação
        patience_seguro = patience or 1
        while len(nova_pop) < pop_size:
            pai1 = _selecionar_pais(pop, fitness, distancias,
                                    selection_method, tournament_size)
            pai2 = _selecionar_pais(pop, fitness, distancias,
                                    selection_method, tournament_size)

            pai1 = _validate_and_normalize_individuo(pai1, n)
            pai2 = _validate_and_normalize_individuo(pai2, n)

            if random.random() < crossover_rate:
                filho1 = crossover_fn(pai1, pai2)
                filho2 = crossover_fn(pai2, pai1)
            else:
                filho1 = pai1[:]
                filho2 = pai2[:]

            if usar_mutacao_adaptativa:
                nova_pop.append(_mutacao_adaptativa(
                    filho1, mutation_rate, geracoes_sem_melhora, patience_seguro))
                if len(nova_pop) < pop_size:
                    nova_pop.append(_mutacao_adaptativa(
                        filho2, mutation_rate, geracoes_sem_melhora, patience_seguro))
            else:
                nova_pop.append(_mutacao_troca(filho1, mutation_rate))
                if len(nova_pop) < pop_size:
                    nova_pop.append(_mutacao_troca(filho2, mutation_rate))

        pop = nova_pop

    if melhor_global is None:
        melhor_global       = pop[0][:]
        melhor_valor_global = cv._calcular_distancia(melhor_global)

    if usar_2opt:
        melhor_global, melhor_valor_global = _dois_opt(melhor_global, cv, max_iter=100)

    # --- Atualiza estado do objeto cv ---
    cv.solucao_atual  = melhor_global[:]
    cv.valor_atual    = melhor_valor_global
    cv.melhor_solucao = melhor_global[:]
    cv.melhor_valor   = melhor_valor_global

    # === CÁLCULO DO GANHO PERCENTUAL (100 * (vi - vf) / vi) ===
    melhora_total = 100 * (valor_inicial_puro - melhor_valor_global) / valor_inicial_puro

    relatorio  = "=" * 60 + "\n"
    relatorio += "  ALGORITMO GENÉTICO — versão melhorada\n"
    relatorio += "=" * 60 + "\n"
    relatorio += f"  Seleção         : {selection_method}\n"
    relatorio += f"  Crossover       : {crossover_op.upper()} (taxa={crossover_rate})\n"
    relatorio += f"  Mutação         : {'Adaptativa (inversão)' if usar_mutacao_adaptativa else 'Swap'} (base={mutation_rate})\n"
    relatorio += f"  Busca local     : {'2-opt ativado' if usar_2opt else 'desativado'}\n"
    relatorio += f"  Pop / Gerações  : {pop_size} / {generations}\n"
    relatorio += f"  Torneio / Elit  : {tournament_size} / {elitism}\n"
    relatorio += f"  Patience        : {patience}\n"
    relatorio += "-" * 60 + "\n"
    relatorio += f"  Gerações exec.  : {gen_final}\n"
    relatorio += f"  Distância Inicial: {valor_inicial_puro:.4f}\n"
    relatorio += f"  Melhor distância: {melhor_valor_global:.4f}\n"
    relatorio += f"  Ganho (Melhora) : {melhora_total:.2f}%\n"
    relatorio += f"  Melhor rota     : {' -> '.join(map(str, melhor_global))} -> {melhor_global[0]}\n"
    relatorio += "=" * 60 + "\n"
    return relatorio


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

    parser = argparse.ArgumentParser(
        description='Executa um teste rápido do algoritmo genético (TSP)')
    parser.add_argument('--size',          type=int,   default=10,    help='Tamanho do problema (n)')
    parser.add_argument('--pop-size',      type=int,   default=50,    help='Tamanho da população')
    parser.add_argument('--generations',   type=int,   default=200,   help='Número máximo de gerações')
    parser.add_argument('--tournament',    type=int,   default=5,     help='Tamanho do torneio')
    parser.add_argument('--elitism',       type=int,   default=2,     help='Elitismo')
    parser.add_argument('--patience',      type=int,   default=40,    help='Patience (parada antecipada)')
    parser.add_argument('--crossover-op',  choices=['OX', 'PMX'], default='OX', help='Operador de crossover')
    parser.add_argument('--mutation-rate', type=float, default=0.1,   help='Taxa de mutação base')
    parser.add_argument('--seed',          type=int,   default=None,  help='Semente PRNG (opcional)')
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    try:
        from execucaoMetodos import CaixeiroViajante
    except Exception as e:
        logging.error("Não foi possível importar CaixeiroViajante: %s", e)
        logging.info("Verifique se execucaoMetodos.py está no mesmo diretório ou no PYTHONPATH.")
        sys.exit(1)

    try:
        cv = CaixeiroViajante(tipo_execucao='FIXO')
        try:
            cv.gerar_problema(size=args.size)
        except TypeError:
            cv.gerar_problema()

        logging.info('Problema gerado. Executando GA com %d cidades...', args.size)
        resumo = algoritmos_geneticos(
            cv,
            pop_size=args.pop_size,
            generations=args.generations,
            selection='TOURNAMENT',
            tournament_size=args.tournament,
            elitism=args.elitism,
            patience=args.patience,
            crossover_op=args.crossover_op,
            usar_2opt=True,
            usar_mutacao_adaptativa=True,
            mutation_rate=args.mutation_rate,
        )
        print(resumo)
    except Exception as e:
        logging.exception('Erro durante execução do teste rápido: %s', e)
        sys.exit(1)