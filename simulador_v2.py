
import random
import csv

from collections import Counter
from itertools import product, combinations
from functools import lru_cache


# CONFIGURACIÓN DEL EXPERIMENTO

NUMERO_PAREJAS = 20
SEMILLA = 2026
ARCHIVO_CSV = "W03_Piloto.csv"

NUMEROS = [
    "Unos",
    "Doses",
    "Treses",
    "Cuatros",
    "Cincos",
    "Seises"
]

ESPECIALES = [
    "Escalera_corta",
    "Escalera_larga",
    "Full",
    "Poker",
    "Generala"
]

CATEGORIAS = NUMEROS + ESPECIALES


# 1. LANZAMIENTO DE DADOS

def lanzar(n, rng):

    return tuple(
        rng.randint(1, 6) for _ in range(n)
    )


# 2. REGLAS DE PUNTUACIÓN

@lru_cache(maxsize=None)
def puntajes(dados):

    conteo = Counter(dados)
    cantidades = sorted(conteo.values())
    valores = set(dados)

    # Categorías numéricas

    puntos = {
        categoria: numero * conteo[numero]
        for numero, categoria in enumerate(NUMEROS, 1)
    }

    # Escalera larga: cinco números consecutivos

    larga = any(
        set(range(i, i + 5)).issubset(valores)
        for i in range(1, 3)
    )

    # Escalera corta: cuatro números consecutivos
    # sin formar una escalera larga

    corta = any(
        set(range(i, i + 4)).issubset(valores)
        for i in range(1, 4)
    ) and not larga

    # Combinaciones especiales

    puntos["Escalera_corta"] = 20 if corta else 0

    puntos["Escalera_larga"] = 30 if larga else 0

    puntos["Full"] = 30 if cantidades == [2, 3] else 0

    puntos["Poker"] = 45 if max(cantidades) == 4 else 0

    puntos["Generala"] = 50 if max(cantidades) == 5 else 0

    return puntos


# 3. POSIBLES RESULTADOS DE LOS RELANZAMIENTOS

@lru_cache(maxsize=None)
def resultados_posibles(n):

    resultados = Counter(
        tuple(sorted(tirada))
        for tirada in product(range(1, 7), repeat=n)
    )

    return tuple(resultados.items())


# 4. CÁLCULO DEL VALOR ESPERADO

def valor_categoria(puntos, categoria, subtotal):

    valor = puntos[categoria]

    # Considerar la bonificación de 35 puntos
    # si se alcanza el mínimo de 63 puntos

    if categoria in NUMEROS:

        if subtotal < 63 <= subtotal + valor:

            valor += 35

    return valor


def mejor_puntaje(dados, disponibles, subtotal):

    puntos = puntajes(tuple(sorted(dados)))

    return max(
        valor_categoria(puntos, c, subtotal)
        for c in disponibles
    )


def valor_esperado(conservados, disponibles, subtotal):

    n = 5 - len(conservados)

    total = 0

    for resultado, frecuencia in resultados_posibles(n):

        dados = conservados + resultado

        mejor = mejor_puntaje(
            dados, disponibles, subtotal
        )

        total += mejor * frecuencia

    return total / (6 ** n)


# 5. MODELO PROBABILÍSTICO

def elegir_dados_probabilistica(
    dados, disponibles, subtotal
):

    mejor_grupo = tuple(sorted(dados))

    mejor_valor = mejor_puntaje(
        dados, disponibles, subtotal
    )

    grupos = set()

    # Evaluar las diferentes alternativas
    # de conservación de dados

    for cantidad in range(5):

        for grupo in combinations(dados, cantidad):

            grupos.add(tuple(sorted(grupo)))

    # Calcular el valor esperado de cada alternativa

    for grupo in sorted(grupos):

        esperanza = valor_esperado(
            grupo, disponibles, subtotal
        )

        if esperanza > mejor_valor:

            mejor_valor = esperanza

            mejor_grupo = grupo

    return mejor_grupo


# 6. MODELO INTUITIVO

def elegir_dados_intuitiva(dados, disponibles, rng):

    puntos_actuales = puntajes(
        tuple(sorted(dados))
    )

    # Verificar si existe una combinación especial
    # que todavía pueda registrarse

    especiales_disponibles = [
        categoria
        for categoria in ESPECIALES
        if categoria in disponibles
        and puntos_actuales[categoria] > 0
    ]

    # Si existe una combinación especial disponible,
    # conservar los cinco dados

    if especiales_disponibles:

        return tuple(dados)

    # Si no existe una combinación especial,
    # contar las repeticiones de cada número

    conteo = Counter(dados)

    frecuencia_maxima = max(conteo.values())

    # Identificar los números que más se repiten

    candidatos = [
        numero
        for numero, frecuencia in conteo.items()
        if frecuencia == frecuencia_maxima
    ]

    # Si existe un empate, elegir al azar
    # uno de los números candidatos

    numero_elegido = rng.choice(candidatos)

    # Conservar los dados del número elegido

    conservados = tuple(
        dado
        for dado in dados
        if dado == numero_elegido
    )

    # 6.1. MODELO DE ALEATORIEDAD CON INTUICIÓN

def elegir_dados_aleatoria(dados, disponibles, rng):

    if rng.random() < PROBABILIDAD_INTUICION:

        # 70 %: decisión intuitiva

        return elegir_dados_intuitiva(
            dados, disponibles, rng
        )

    else:

        # 30 %: decisión aleatoria

        return tuple(
            dado for dado in dados
            if rng.random() < 0.5
        )
        
    return conservados


# 7. SIMULAR UNA PARTIDA COMPLETA

def jugar(estrategia, tiradas_iniciales, rng):

    planilla = {}

    disponibles = CATEGORIAS.copy()

    # Suma del primer lanzamiento de la partida

    primera_suma = sum(tiradas_iniciales[0])

    # Cada partida tiene once turnos

    for ronda in range(11):

        dados = tiradas_iniciales[ronda]

        subtotal = sum(
            planilla.get(c, 0) for c in NUMEROS
        )

        # Máximo dos relanzamientos adicionales

        for _ in range(2):

            # MODELO PROBABILÍSTICO

            if estrategia == "Probabilistica":

                conservados = elegir_dados_probabilistica(
                    dados, disponibles, subtotal
                )

            # MODELO DE ALEATORIEDAD

            elif estrategia == "Aleatoria":

                conservados = elegir_dados_aleatoria(
                    dados, disponibles, rng
                )

            else:

                raise ValueError("Estrategia no reconocida")

            # Si conserva los cinco dados,
            # finaliza los lanzamientos del turno

            if len(conservados) == 5:

                break

            # Relanzar los dados no conservados

            dados = conservados + lanzar(
                5 - len(conservados), rng
            )

        # Calcular los puntos obtenidos

        puntos = puntajes(tuple(sorted(dados)))

        # SELECCIÓN DE CATEGORÍA

        if estrategia == "Probabilistica":

            categoria = max(
                disponibles,
                key=lambda c: valor_categoria(
                    puntos, c, subtotal
                )
            )

        else:

            if rng.random() < PROBABILIDAD_INTUICION:

                # 70 %: selección intuitiva

                puntaje_maximo = max(
                    puntos[c] for c in disponibles
                )

                mejores_categorias = [
                    c for c in disponibles
                    if puntos[c] == puntaje_maximo
                ]

                categoria = rng.choice(
                    mejores_categorias
                )

            else:

                # 30 %: selección aleatoria

                categorias_positivas = [
                    c for c in disponibles
                    if puntos[c] > 0
                ]

                if categorias_positivas:

                    categoria = rng.choice(
                        categorias_positivas
                    )

                else:

                    categoria = rng.choice(
                        disponibles
                    )

        # Registrar la categoría seleccionada

        planilla[categoria] = puntos[categoria]

        # Eliminar la categoría utilizada

        disponibles.remove(categoria)

    # Calcular subtotal de categorías numéricas

    subtotal = sum(
        planilla[c] for c in NUMEROS
    )

    # Calcular la bonificación

    bonus = 35 if subtotal >= 63 else 0

    # Calcular el puntaje final de la partida

    total = sum(planilla.values()) + bonus

    # REGISTRO DE LAS VARIABLES DEL ESTUDIO

    registro = {

        "Estrategia": estrategia,

        "Puntos_acumulados": total,

        "Primera_suma_dados": primera_suma

    }

    # Registrar las combinaciones especiales
    # 1 = registrada con puntos
    # 0 = no registrada con puntos

    for categoria in ESPECIALES:

        registro[categoria] = int(
            planilla[categoria] > 0
        )

    # Registrar la bonificación obtenida
    # 1 = obtuvo la bonificación
    # 0 = no obtuvo la bonificación

    registro["Bonificacion_obtenida"] = int(
        bonus > 0
    )

    # VERIFICACIONES INTERNAS

    assert len(planilla) == 11

    assert 0 <= total <= 315

    assert 5 <= primera_suma <= 30

    assert registro["Bonificacion_obtenida"] in (0, 1)

    for categoria in ESPECIALES:

        assert registro[categoria] in (0, 1)

    return registro


# 8. SIMULAR LOS ENFRENTAMIENTOS

rng = random.Random(SEMILLA)

registros = []

for id_partida in range(1, NUMERO_PAREJAS + 1):

    tiradas = [
        lanzar(5, rng) for _ in range(11)
    ]

    # Modelo probabilístico

    probabilistica = jugar(
        "Probabilistica",
        tiradas,
        random.Random(rng.getrandbits(64))
    )

    # Modelo de aleatoriedad con intuición

    aleatoria = jugar(
        "Aleatoria",
        tiradas,
        random.Random(rng.getrandbits(64))
    )

    # Comparar puntajes

    p1 = probabilistica["Puntos_acumulados"]

    p2 = aleatoria["Puntos_acumulados"]

    # Resultado de la partida

    if p1 > p2:

        probabilistica["Resultado_partida"] = 1
        aleatoria["Resultado_partida"] = 0

    elif p1 < p2:

        probabilistica["Resultado_partida"] = 0
        aleatoria["Resultado_partida"] = 1

    else:

        probabilistica["Resultado_partida"] = 2
        aleatoria["Resultado_partida"] = 2

    # Registrar los resultados

    for registro in [probabilistica, aleatoria]:

        registro["ID_enfrentamiento"] = id_partida

        registros.append(registro)

    print(
        f"Enfrentamiento {id_partida}: "
        f"Probabilistica = {p1}, "
        f"Aleatoria = {p2}"
    )

# 9. EXPORTAR LOS DATOS A CSV

columnas = [

    "ID_enfrentamiento",

    "Estrategia",

    "Puntos_acumulados",

    "Primera_suma_dados",

    "Escalera_corta",

    "Escalera_larga",

    "Full",

    "Poker",

    "Generala",

    "Bonificacion_obtenida",

    "Resultado_partida"

]

with open(
    ARCHIVO_CSV,
    "w",
    newline="",
    encoding="utf-8-sig"
) as archivo:

    escritor = csv.DictWriter(
        archivo,
        fieldnames=columnas
    )

    escritor.writeheader()

    escritor.writerows(registros)


# 10. MOSTRAR RESUMEN DE LA SIMULACIÓN

print("\nSIMULACION FINALIZADA")

print("Enfrentamientos:", NUMERO_PAREJAS)

print("Partidas probabilisticas:", NUMERO_PAREJAS)

print("Partidas aleatorias:", NUMERO_PAREJAS)

print("Registros individuales:", len(registros))

print("Variables de estudio:", len(columnas) - 1)

print("Total de columnas:", len(columnas))

print("Archivo generado:", ARCHIVO_CSV)
