import random
import math
from copy import deepcopy

# Matriz de distâncias fixa
DISTANCIAS_FIXO = [
    [0,  10, 20, 5,  15, 20, 20, 10],
    [10, 0,  5,  15, 13, 5,  15, 25],
    [20, 5,  0,  19, 10, 18, 17, 20],
    [5,  15, 19, 0,  25, 11, 10, 5 ],
    [15, 13, 10, 25, 0,  14, 12, 18],
    [20, 5,  18, 11, 14, 0,  8,  12],
    [20, 15, 17, 10, 12, 8,  0,  7 ],
    [10, 25, 20, 5,  18, 12, 7,  0 ]
]

class CaixeiroViajante:
    def __init__(self, tamanho=8, tipo_execucao='FIXO'):
        self.tipo_execucao = tipo_execucao
        self.tamanho = tamanho
        self.distancias = None
        self.solucao_atual = None
        self.valor_atual = None
        self.melhor_solucao = None
        self.melhor_valor = float('inf')

    def gerar_problema(self):
        """Gera a matriz de distâncias (fixa ou aleatória)"""
        if self.tipo_execucao == 'FIXO':
            self.distancias = deepcopy(DISTANCIAS_FIXO)
        else:
            # Gera matriz aleatória simétrica
            self.distancias = [[0] * self.tamanho for _ in range(self.tamanho)]
            for i in range(self.tamanho):
                for j in range(i + 1, self.tamanho):
                    dist = random.randint(5, 50)
                    self.distancias[i][j] = dist
                    self.distancias[j][i] = dist

        return self._matriz_para_string()

    def _matriz_para_string(self):
        """Converte a matriz de distâncias para string formatada"""
        if not self.distancias:
            return "Nenhum problema gerado"

        s = "Matriz de Distâncias:\n"
        s += "     "
        for j in range(len(self.distancias)):
            s += f"{j:3d} "
        s += "\n"
        for i in range(len(self.distancias)):
            s += f"{i:2d}: "
            for j in range(len(self.distancias[i])):
                s += f"{self.distancias[i][j]:3d} "
            s += "\n"
        return s

    def solucao_inicial(self):
        """Gera uma solução inicial aleatória"""
        if not self.distancias:
            return "Gere o problema primeiro!"

        n = len(self.distancias)
        self.solucao_atual = list(range(n))
        random.shuffle(self.solucao_atual)
        self.valor_atual = self._calcular_distancia(self.solucao_atual)
        self.melhor_solucao = deepcopy(self.solucao_atual)
        self.melhor_valor = self.valor_atual

        return self._solucao_para_string()

    def _calcular_distancia(self, rota):
        """Calcula a distância total de uma rota (ciclo completo)"""
        dist = 0
        for i in range(len(rota)):
            dist += self.distancias[rota[i]][rota[(i + 1) % len(rota)]]
        return dist

    def _solucao_para_string(self):
        """Converte a solução atual para string formatada"""
        if not self.solucao_atual:
            return "Nenhuma solução inicial"

        s = f"Rota: {' -> '.join(map(str, self.solucao_atual))} -> {self.solucao_atual[0]}\n"
        s += f"Distância Total: {self.valor_atual}\n"
        return s

    def avalia(self):
        """Avalia a solução atual (retorna a distância)"""
        if not self.solucao_atual:
            return "Solução não gerada"
        return self._solucao_para_string()

    def _gerar_vizinho(self, rota):
        """
        Gera um vizinho usando 2-opt: inverte o segmento entre dois índices.
        Produz vizinhos de melhor qualidade do que simples troca de posições.
        """
        novo = rota[:]
        i, j = sorted(random.sample(range(len(novo)), 2))
        novo[i:j+1] = reversed(novo[i:j+1])
        return novo

    # ------------------------------------------------------------------
    # SUBIDA DE ENCOSTA
    # Estratégia: a cada iteração, testa TODOS os vizinhos possíveis (2-opt
    # completo) e aceita o melhor. Para quando nenhum vizinho melhora.
    # ------------------------------------------------------------------
    def subida_encosta(self, max_iter=1000):
        """Subida de Encosta — busca local com vizinhança 2-opt completa"""
        if not self.solucao_atual:
            return "Gere a solução inicial primeiro!"

        atual = self.solucao_atual[:]
        custo_atual = self._calcular_distancia(atual)
        iteracoes = 0

        for iteracoes in range(1, max_iter + 1):
            melhor_vizinho = None
            melhor_custo_vizinho = custo_atual

            # Explora TODA a vizinhança 2-opt antes de decidir
            n = len(atual)
            for i in range(n - 1):
                for j in range(i + 1, n):
                    vizinho = atual[:]
                    vizinho[i:j+1] = reversed(vizinho[i:j+1])
                    custo_v = self._calcular_distancia(vizinho)
                    if custo_v < melhor_custo_vizinho:
                        melhor_custo_vizinho = custo_v
                        melhor_vizinho = vizinho

            if melhor_vizinho is None:
                # Ótimo local: nenhum vizinho melhora
                break

            atual = melhor_vizinho
            custo_atual = melhor_custo_vizinho

        self.solucao_atual = atual
        self.valor_atual = custo_atual
        if custo_atual < self.melhor_valor:
            self.melhor_valor = custo_atual
            self.melhor_solucao = atual[:]

        s = f"Subida de Encosta (iterações até parar: {iteracoes})\n"
        s += self._solucao_para_string()
        return s

    # ------------------------------------------------------------------
    # SUBIDA DE ENCOSTA COM MÚLTIPLAS TENTATIVAS (Random Restart)
    # Executa `tmax` reinícios aleatórios independentes, cada um com
    # busca local 2-opt completa, e guarda o melhor resultado global.
    # ------------------------------------------------------------------
    def subida_encosta_tentativas(self, tmax):
        """Subida de Encosta com Reinícios Aleatórios (Random Restart Hill Climbing)"""
        if not self.distancias:
            return "Gere o problema primeiro!"

        n = len(self.distancias)
        melhor_global = None
        melhor_valor_global = float('inf')

        for tentativa in range(tmax):
            # Reinício: solução aleatória nova a cada tentativa
            atual = list(range(n))
            random.shuffle(atual)
            custo_atual = self._calcular_distancia(atual)

            # Busca local 2-opt completa a partir desta solução
            melhoria = True
            while melhoria:
                melhoria = False
                for i in range(n - 1):
                    for j in range(i + 1, n):
                        vizinho = atual[:]
                        vizinho[i:j+1] = reversed(vizinho[i:j+1])
                        custo_v = self._calcular_distancia(vizinho)
                        if custo_v < custo_atual:
                            atual = vizinho
                            custo_atual = custo_v
                            melhoria = True  # Encontrou melhoria; reinicia varredura

            if custo_atual < melhor_valor_global:
                melhor_global = atual[:]
                melhor_valor_global = custo_atual

        self.solucao_atual = melhor_global
        self.valor_atual = melhor_valor_global
        if melhor_valor_global < self.melhor_valor:
            self.melhor_valor = melhor_valor_global
            self.melhor_solucao = melhor_global[:]

        s = f"Subida de Encosta com Tentativas (TMAX={tmax})\n"
        s += self._solucao_para_string()
        return s

    # ------------------------------------------------------------------
    # TÊMPERA SIMULADA
    # Aceita soluções piores com probabilidade e^(-delta/T).
    # A temperatura T começa em `ti`, é multiplicada por `fr` a cada
    # iteração, e o algoritmo para quando T < tf.
    # ------------------------------------------------------------------
    def tempera_simulada(self, ti, tf, fr):
        """Têmpera Simulada"""
        if not self.solucao_atual:
            return "Gere a solução inicial primeiro!"

        atual = self.solucao_atual[:]
        custo_atual = self._calcular_distancia(atual)
        melhor_local = atual[:]
        melhor_custo_local = custo_atual
        T = ti
        aceitacoes = 0
        rejeicoes = 0
        iteracoes = 0

        while T > tf:
            iteracoes += 1
            vizinho = self._gerar_vizinho(atual)
            custo_vizinho = self._calcular_distancia(vizinho)
            delta = custo_vizinho - custo_atual

            if delta < 0 or random.random() < math.exp(-delta / T):
                atual = vizinho
                custo_atual = custo_vizinho
                aceitacoes += 1
                # Guarda o melhor encontrado durante toda a execução
                if custo_atual < melhor_custo_local:
                    melhor_local = atual[:]
                    melhor_custo_local = custo_atual
            else:
                rejeicoes += 1

            T *= fr

        # Retorna a melhor solução encontrada, não a última
        self.solucao_atual = melhor_local
        self.valor_atual = melhor_custo_local
        if melhor_custo_local < self.melhor_valor:
            self.melhor_valor = melhor_custo_local
            self.melhor_solucao = melhor_local[:]

        s = f"Têmpera Simulada (TI={ti}, TF={tf}, FR={fr}, it={iteracoes})\n"
        s += f"Aceitações: {aceitacoes}, Rejeições: {rejeicoes}\n"
        s += self._solucao_para_string()
        return s

    def _gerar_populacao(self, tamanho, pop_size):
        """Gera uma população inicial de rotas aleatórias."""
        populacao = []
        for _ in range(pop_size):
            individuo = list(range(tamanho))
            random.shuffle(individuo)
            populacao.append(individuo)
        return populacao

    def _selecionar_por_roleta(self, populacao, fitness):
        """Seleciona um indivíduo por roleta proporcional à aptidão."""
        total = sum(fitness)
        if total <= 0:
            return deepcopy(random.choice(populacao))
        limite = random.uniform(0, total)
        acumulado = 0.0
        for individuo, fit in zip(populacao, fitness):
            acumulado += fit
            if acumulado >= limite:
                return deepcopy(individuo)
        return deepcopy(populacao[-1])

    def _selecionar_por_torneio(self, populacao, tournament_size):
        """Seleciona um indivíduo por torneio entre amostras aleatórias."""
        participantes = random.sample(populacao, min(tournament_size, len(populacao)))
        melhor = min(participantes, key=lambda ind: self._calcular_distancia(ind))
        return deepcopy(melhor)

    def _selecionar_pais(self, populacao, fitness, metodo_selecao, tournament_size):
        if metodo_selecao.upper() in ('TOURNAMENT', 'TORNEIO'):
            return self._selecionar_por_torneio(populacao, tournament_size)
        return self._selecionar_por_roleta(populacao, fitness)

    def _crossover_ordem(self, pai1, pai2):
        """Realiza crossover de ordem (Order Crossover) para TSP."""
        n = len(pai1)
        filho = [-1] * n
        i, j = sorted(random.sample(range(n), 2))
        filho[i:j+1] = pai1[i:j+1]

        pos = (j + 1) % n
        for gene in pai2[j+1:] + pai2[:j+1]:
            if gene not in filho:
                filho[pos] = gene
                pos = (pos + 1) % n
        return filho

    def _mutacao_troca(self, individuo, taxa_mutacao):
        """Aplica mutação por troca de dois genes com probabilidade dada."""
        if random.random() < taxa_mutacao:
            i, j = random.sample(range(len(individuo)), 2)
            individuo[i], individuo[j] = individuo[j], individuo[i]
        return individuo

    def algoritmos_geneticos(self, pop_size=50, generations=200, selection='ROULETTE',
                             crossover_rate=0.9, mutation_rate=0.1, tournament_size=3,
                             elitism=1):
        """Executa um algoritmo genético simples para o problema do caixeiro viajante."""
        if not self.distancias:
            return "Gere o problema primeiro!"

        n = len(self.distancias)
        if pop_size <= 0:
            pop_size = max(10, n * 2)
        if generations <= 0:
            generations = 100
        pop = self._gerar_populacao(n, pop_size)

        melhor_global = None
        melhor_valor_global = float('inf')

        for _ in range(generations):
            distancias = [self._calcular_distancia(ind) for ind in pop]
            for individuo, distancia in zip(pop, distancias):
                if distancia < melhor_valor_global:
                    melhor_valor_global = distancia
                    melhor_global = deepcopy(individuo)

            fitness = [1.0 / (1.0 + d) for d in distancias]
            nova_pop = []

            if elitism > 0:
                indices_ordenados = sorted(range(len(pop)), key=lambda idx: distancias[idx])
                for idx in indices_ordenados[:min(elitism, len(pop))]:
                    nova_pop.append(deepcopy(pop[idx]))

            while len(nova_pop) < pop_size:
                pai1 = self._selecionar_pais(pop, fitness, selection, tournament_size)
                pai2 = self._selecionar_pais(pop, fitness, selection, tournament_size)

                if random.random() < crossover_rate:
                    filho1 = self._crossover_ordem(pai1, pai2)
                    filho2 = self._crossover_ordem(pai2, pai1)
                else:
                    filho1 = deepcopy(pai1)
                    filho2 = deepcopy(pai2)

                nova_pop.append(self._mutacao_troca(filho1, mutation_rate))
                if len(nova_pop) < pop_size:
                    nova_pop.append(self._mutacao_troca(filho2, mutation_rate))

            pop = nova_pop

        if melhor_global is None:
            melhor_global = pop[0]
            melhor_valor_global = self._calcular_distancia(melhor_global)

        self.solucao_atual = melhor_global[:]
        self.valor_atual = melhor_valor_global
        self.melhor_solucao = melhor_global[:]
        self.melhor_valor = melhor_valor_global

        s = f"Algoritmo Genético ({selection}, POP={pop_size}, GEN={generations}, CR={crossover_rate}, MR={mutation_rate}, T={tournament_size}, ELIT={elitism})\n"
        s += f"Melhor distância encontrada: {melhor_valor_global}\n"
        s += f"Melhor rota: {' -> '.join(map(str, melhor_global))} -> {melhor_global[0]}\n"
        return s

    # ------------------------------------------------------------------
    # ANÁLISE COMPARATIVA
    # ------------------------------------------------------------------
    def analise_comparativa(self):
        """Executa todos os métodos com diferentes parâmetros e compara"""
        if not self.distancias:
            return "Gere o problema primeiro!"

        n = len(self.distancias)
        # Reseta o melhor absoluto para comparação justa entre execuções
        self.melhor_valor = float('inf')
        self.melhor_solucao = None

        resultados = "=== ANÁLISE COMPARATIVA ===\n\n"

        configs = [
            ("SE",  {},                  {}),
            ("SET", {"tmax": n},         {}),
            ("SET", {"tmax": 2 * n},     {}),
            ("SET", {"tmax": n // 2},    {}),
            ("TE",  {}, {"ti": 100, "tf": 0.1,  "fr": 0.8}),
            ("TE",  {}, {"ti": 200, "tf": 0.1,  "fr": 0.8}),
            ("TE",  {}, {"ti": 500, "tf": 0.1,  "fr": 0.8}),
            ("TE",  {}, {"ti": 200, "tf": 0.1,  "fr": 0.9}),
            ("TE",  {}, {"ti": 500, "tf": 0.1,  "fr": 0.9}),
            ("TE",  {}, {"ti": 200, "tf": 0.01, "fr": 0.9}),
            ("TE",  {}, {"ti": 500, "tf": 0.01, "fr": 0.9}),
        ]

        for idx, (metodo, params_set, params_te) in enumerate(configs, 1):
            # Cada método começa de uma solução aleatória nova e independente
            self.solucao_atual = list(range(n))
            random.shuffle(self.solucao_atual)
            self.valor_atual = self._calcular_distancia(self.solucao_atual)
            valor_inicial = self.valor_atual

            if metodo == "SE":
                resultado = self.subida_encosta()
            elif metodo == "SET":
                tmax = params_set.get("tmax", n)
                resultado = self.subida_encosta_tentativas(tmax)
            elif metodo == "TE":
                ti = params_te.get("ti", 100)
                tf = params_te.get("tf", 0.1)
                fr = params_te.get("fr", 0.8)
                resultado = self.tempera_simulada(ti, tf, fr)

            valor_final = self.valor_atual
            ganho = ((valor_inicial - valor_final) / valor_inicial * 100) if valor_inicial > 0 else 0

            resultados += f"{idx}. {resultado}"
            resultados += f"Valor Inicial: {valor_inicial} | Valor Final: {valor_final}\n"
            resultados += f"Ganho: {ganho:.2f}%\n"
            resultados += "-" * 30 + "\n\n"

        resultados += f"Melhor valor absoluto encontrado em todos os testes: {self.melhor_valor}\n"
        if self.melhor_solucao:
            resultados += f"Melhor rota: {' -> '.join(map(str, self.melhor_solucao))} -> {self.melhor_solucao[0]}\n"
        return resultados


if __name__ == "__main__":
    cv = CaixeiroViajante(tipo_execucao='FIXO')
    print(cv.gerar_problema())
    print(cv.solucao_inicial())
    print(cv.analise_comparativa())
