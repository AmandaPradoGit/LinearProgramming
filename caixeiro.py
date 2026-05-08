import random
import math
from copy import deepcopy

# Matriz de distâncias fixa para FIXO
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
        """Gera um vizinho trocando duas cidades (2-opt)"""
        novo = deepcopy(rota)
        i, j = random.sample(range(len(novo)), 2)
        novo[i], novo[j] = novo[j], novo[i]
        return novo
    
    def subida_encosta(self):
        """Subida de Encosta - Greedy local search"""
        if not self.solucao_atual:
            return "Gere a solução inicial primeiro!"
        
        melhoria = True
        iteracoes = 0
        
        while melhoria:
            melhoria = False
            iteracoes += 1
            
            for i in range(len(self.solucao_atual)):
                for j in range(i + 1, len(self.solucao_atual)):
                    novo = deepcopy(self.solucao_atual)
                    novo[i], novo[j] = novo[j], novo[i]
                    novo_valor = self._calcular_distancia(novo)
                    
                    if novo_valor < self.valor_atual:
                        self.solucao_atual = novo
                        self.valor_atual = novo_valor
                        melhoria = True
                        
                        if novo_valor < self.melhor_valor:
                            self.melhor_valor = novo_valor
                            self.melhor_solucao = deepcopy(novo)
        
        s = f"Subida de Encosta (iterações: {iteracoes})\n"
        s += self._solucao_para_string()
        return s
    
    def subida_encosta_tentativas(self, tmax):
        """Subida de Encosta com Tentativas"""
        if not self.solucao_atual:
            return "Gere a solução inicial primeiro!"
        
        melhor_global = deepcopy(self.melhor_solucao)
        melhor_valor_global = self.melhor_valor
        
        for tentativa in range(tmax):
            # Realiza busca local
            melhoria = True
            while melhoria:
                melhoria = False
                for i in range(len(self.solucao_atual)):
                    for j in range(i + 1, len(self.solucao_atual)):
                        novo = deepcopy(self.solucao_atual)
                        novo[i], novo[j] = novo[j], novo[i]
                        novo_valor = self._calcular_distancia(novo)
                        
                        if novo_valor < self.valor_atual:
                            self.solucao_atual = novo
                            self.valor_atual = novo_valor
                            melhoria = True
                            
                            if novo_valor < melhor_valor_global:
                                melhor_valor_global = novo_valor
                                melhor_global = deepcopy(novo)
            
            # Se não é a última tentativa, gera nova solução aleatória
            if tentativa < tmax - 1:
                self.solucao_atual = list(range(len(self.distancias)))
                random.shuffle(self.solucao_atual)
                self.valor_atual = self._calcular_distancia(self.solucao_atual)
        
        self.melhor_solucao = melhor_global
        self.melhor_valor = melhor_valor_global
        self.solucao_atual = melhor_global
        self.valor_atual = melhor_valor_global
        
        s = f"Subida de Encosta com Tentativas (TMAX={tmax})\n"
        s += self._solucao_para_string()
        return s
    
    def tempera_simulada(self, ti, tf, fr):
        """Têmpera Simulada - Simulated Annealing"""
        if not self.solucao_atual:
            return "Gere a solução inicial primeiro!"
        
        T = ti
        aceitacoes = 0
        rejeicoes = 0
        
        while T > tf:
            for _ in range(10):  # Iterações por temperatura
                vizinho = self._gerar_vizinho(self.solucao_atual)
                valor_vizinho = self._calcular_distancia(vizinho)
                delta = valor_vizinho - self.valor_atual
                
                if delta < 0 or random.random() < math.exp(-delta / T):
                    self.solucao_atual = vizinho
                    self.valor_atual = valor_vizinho
                    aceitacoes += 1
                    
                    if valor_vizinho < self.melhor_valor:
                        self.melhor_valor = valor_vizinho
                        self.melhor_solucao = deepcopy(vizinho)
                else:
                    rejeicoes += 1
            
            T = T * fr
        
        s = f"Têmpera Simulada (TI={ti}, TF={tf}, FR={fr})\n"
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