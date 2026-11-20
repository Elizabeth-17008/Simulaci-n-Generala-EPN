
import random

# Simular el lanzamiento de cinco dados
dados = []

for i in range(5):
    numero = random.randint(1, 6)
    dados.append(numero)

# Mostrar los resultados
print("SIMULADOR DE GENERALA")
print("Dados obtenidos:", dados)
print("Primera suma de dados:", sum(dados))
