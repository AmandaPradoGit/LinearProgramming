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
        """Calcula a distância total de uma rota"""
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
        """Gera um vizinho trocando duas cidades aleatórias"""
        novo = rota[:]
        i, j = random.sample(range(len(novo)), 2)
        novo[i], novo[j] = novo[j], novo[i]
        return novo
    
    def subida_encosta(self, max_iter=1000):
        """Subida de Encosta"""
        if not self.solucao_atual:
            return "Gere a solução inicial primeiro!"

        atual = self.solucao_atual[:]
        custo_atual = self._calcular_distancia(atual)
        iteracoes = 0
        melhoria = True

        while melhoria and iteracoes < max_iter:
            iteracoes += 1
            melhoria = False
            vizinho = self._gerar_vizinho(atual)
            custo_vizinho = self._calcular_distancia(vizinho)
            delta = custo_vizinho - custo_atual

            if delta < 0:
                atual = vizinho
                custo_atual = custo_vizinho
                melhoria = True

        self.solucao_atual = atual
        self.valor_atual = custo_atual
        if custo_atual < self.melhor_valor:
            self.melhor_valor = custo_atual
            self.melhor_solucao = atual[:]

        s = f"Subida de Encosta (iterações: {iteracoes})\n"
        s += self._solucao_para_string()
        return s
    
    def subida_encosta_tentativas(self, tmax):
        """Subida de Encosta com Tentativas"""
        if not self.solucao_atual:
            return "Gere a solução inicial primeiro!"

        melhor_global = self.solucao_atual[:]
        melhor_valor_global = self._calcular_distancia(melhor_global)
        n = len(self.distancias)

        for tentativa in range(tmax):
            atual = list(range(n))
            random.shuffle(atual)
            custo_atual = self._calcular_distancia(atual)
            iteracoes = 0
            melhoria = True

            while melhoria and iteracoes < n * 10:
                iteracoes += 1
                vizinho = self._gerar_vizinho(atual)
                custo_vizinho = self._calcular_distancia(vizinho)
                delta = custo_vizinho - custo_atual

                if delta < 0:
                    atual = vizinho
                    custo_atual = custo_vizinho
                else:
                    melhoria = False

            if custo_atual < melhor_valor_global:
                melhor_global = atual[:]
                melhor_valor_global = custo_atual

        self.solucao_atual = melhor_global
        self.valor_atual = melhor_valor_global
        self.melhor_solucao = melhor_global[:]
        self.melhor_valor = melhor_valor_global

        s = f"Subida de Encosta com Tentativas (TMAX={tmax})\n"
        s += self._solucao_para_string()
        return s
    
    def tempera_simulada(self, ti, tf, fr):
        """Têmpera Simulada"""
        if not self.solucao_atual:
            return "Gere a solução inicial primeiro!"

        atual = self.solucao_atual[:]
        custo_atual = self._calcular_distancia(atual)
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
            else:
                rejeicoes += 1

            T *= fr

        self.solucao_atual = atual
        self.valor_atual = custo_atual
        if custo_atual < self.melhor_valor:
            self.melhor_valor = custo_atual
            self.melhor_solucao = atual[:]

        s = f"Têmpera Simulada (TI={ti}, TF={tf}, FR={fr}, it={iteracoes})\n"
        s += f"Aceitações: {aceitacoes}, Rejeições: {rejeicoes}\n"
        s += self._solucao_para_string()
        return s
    
    def analise_comparativa(self):
        """Executa todos os métodos com diferentes parâmetros"""
        if not self.solucao_atual:
            return "Gere a solução inicial primeiro!"
        
        n = len(self.distancias)
        resultados = "=== ANÁLISE COMPARATIVA ===\n\n"
        
        configs = [
            ("SE", {}, {}),
            ("SET", {"tmax": n}, {}),
            ("SET", {"tmax": 2 * n}, {}),
            ("SET", {"tmax": n // 2}, {}),
            ("SET", {"tmax": n}, {}),
            ("TE", {"ti": 100, "tf": 0.1, "fr": 0.8}, {}),
            ("TE", {"ti": 200, "tf": 0.1, "fr": 0.8}, {}),
            ("TE", {"ti": 500, "tf": 0.1, "fr": 0.8}, {}),
            ("TE", {"ti": 200, "tf": 0.1, "fr": 0.9}, {}),
            ("TE", {"ti": 500, "tf": 0.1, "fr": 0.9}, {}),
            ("TE", {"ti": 200, "tf": 0.01, "fr": 0.9}, {}),
            ("TE", {"ti": 500, "tf": 0.01, "fr": 0.9}, {}),
        ]
        
        melhor_valor_global = self.melhor_valor
        
        for idx, (metodo, params_set, params_te) in enumerate(configs, 1):
            # Reinicializa a solução
            self.solucao_atual = list(range(n))
            random.shuffle(self.solucao_atual)
            self.valor_atual = self._calcular_distancia(self.solucao_atual)
            
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
            
            ganho = ((melhor_valor_global - self.melhor_valor) / melhor_valor_global * 100) if melhor_valor_global > 0 else 0
            resultados += f"{idx}. {resultado}\nGanho: {ganho:.2f}%\n\n"
        
        resultados += f"\nMelhor solução encontrada: {self.melhor_valor}\n"
        return resultados