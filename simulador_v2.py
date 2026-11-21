
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
    return tuple(rng.randint(1, 6) for _ in range(n))


# 2. REGLAS DE PUNTUACIÓN

@lru_cache(maxsize=None)
def puntajes(dados):

    conteo = Counter(dados)
    cantidades = sorted(conteo.values())
    valores = set(dados)

    puntos = {
        categoria: numero * conteo[numero]
        for numero, categoria in enumerate(NUMEROS, 1)
    }

    # Escalera larga: cinco números consecutivos

    larga = any(
        set(range(i, i + 5)).issubset(valores)
        for i in range(1, 3)
    )

    # Escalera corta: cuatro números consecutivos,
    # siempre que no sea una escalera larga.

    corta = any(
        set(range(i, i + 4)).issubset(valores)
        for i in range(1, 4)
    ) and not larga

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

def mejor_puntaje(dados, disponibles, subtotal):

    puntos = puntajes(tuple(sorted(dados)))

    return max(
        valor_categoria(puntos, c, subtotal)
        for c in disponibles
    )


def valor_categoria(puntos, categoria, subtotal):

    valor = puntos[categoria]

    # Considerar la bonificación de 35 puntos
    # si se alcanza el mínimo de 63 puntos.

    if categoria in NUMEROS:

        if subtotal < 63 <= subtotal + valor:
            valor += 35

    return valor


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


# 5. ESTRATEGIA PROBABILÍSTICA

def elegir_dados(dados, disponibles, subtotal):

    mejor_grupo = tuple(sorted(dados))

    mejor_valor = mejor_puntaje(
        dados, disponibles, subtotal
    )

    grupos = set()

    for cantidad in range(5):

        for grupo in combinations(dados, cantidad):

            grupos.add(tuple(sorted(grupo)))

    for grupo in sorted(grupos):

        esperanza = valor_esperado(
            grupo, disponibles, subtotal
        )

        if esperanza > mejor_valor:

            mejor_valor = esperanza
            mejor_grupo = grupo

    return mejor_grupo


# 6. SIMULAR UNA PARTIDA COMPLETA

def jugar(estrategia, tiradas_iniciales, rng):

    planilla = {}

    disponibles = CATEGORIAS.copy()

    primera_suma = sum(tiradas_iniciales[0])

    for ronda in range(11):

        dados = tiradas_iniciales[ronda]

        subtotal = sum(
            planilla.get(c, 0) for c in NUMEROS
        )

        # Máximo dos relanzamientos adicionales

        for _ in range(2):

            if estrategia == "Probabilistica":

                conservados = elegir_dados(
                    dados, disponibles, subtotal
                )

            else:

                conservados = tuple(
                    d for d in dados
                    if rng.random() < 0.5
                )

            if len(conservados) == 5:
                break

            dados = conservados + lanzar(
                5 - len(conservados), rng
            )

        puntos = puntajes(tuple(sorted(dados)))

        # Elegir una categoría disponible

        if estrategia == "Probabilistica":

            categoria = max(
                disponibles,
                key=lambda c: valor_categoria(
                    puntos, c, subtotal
                )
            )

        else:

            categoria = rng.choice(disponibles)

        # Registrar el puntaje de la categoría

        planilla[categoria] = puntos[categoria]

        disponibles.remove(categoria)

    # Calcular subtotal de categorías numéricas

    subtotal = sum(planilla[c] for c in NUMEROS)

    # Calcular la bonificación

    bonus = 35 if subtotal >= 63 else 0

    # Calcular puntuación final

    total = sum(planilla.values()) + bonus

    # Registrar las variables del estudio

    registro = {
        "Estrategia": estrategia,
        "Puntos_acumulados": total,
        "Primera_suma_dados": primera_suma
    }

    # Registrar las combinaciones especiales
    # 1 = combinación registrada con puntos
    # 0 = combinación no registrada con puntos

    for categoria in ESPECIALES:

        registro[categoria] = int(
            planilla[categoria] > 0
        )

    # Registrar la bonificación obtenida
    # 1 = obtuvo la bonificación
    # 0 = no obtuvo la bonificación

    registro["Bonificacion_obtenida"] = int(bonus > 0)

    # EVENTO A:
    # Obtener al menos una combinación especial
    # registrada con puntos en la planilla.

    registro["Evento_A"] = int(
        any(planilla[c] > 0 for c in ESPECIALES)
    )

    # EVENTO B:
    # Utilizar una estrategia probabilística.
    # 1 = estrategia probabilística
    # 0 = decisiones aleatorias

    registro["Evento_B"] = int(
        estrategia == "Probabilistica"
    )

    # Verificaciones internas

    assert len(planilla) == 11
    assert 0 <= total <= 315
    assert 5 <= primera_suma <= 30
    assert registro["Bonificacion_obtenida"] in (0, 1)
    assert registro["Evento_A"] in (0, 1)
    assert registro["Evento_B"] in (0, 1)

    return registro


# 7. SIMULAR LOS ENFRENTAMIENTOS

rng = random.Random(SEMILLA)

registros = []

for id_partida in range(1, NUMERO_PAREJAS + 1):

    # Los dos jugadores comienzan cada ronda
    # con los mismos cinco dados.

    tiradas = [
        lanzar(5, rng) for _ in range(11)
    ]

    probabilistica = jugar(
        "Probabilistica",
        tiradas,
        random.Random(rng.getrandbits(64))
    )

    aleatoria = jugar(
        "Aleatoria",
        tiradas,
        random.Random(rng.getrandbits(64))
    )

    p1 = probabilistica["Puntos_acumulados"]
    p2 = aleatoria["Puntos_acumulados"]

    # Resultado de la partida
    # 0 = Derrota
    # 1 = Victoria

    if p1 > p2:

        probabilistica["Resultado_partida"] = 1
        aleatoria["Resultado_partida"] = 0

    elif p1 < p2:

        probabilistica["Resultado_partida"] = 0
        aleatoria["Resultado_partida"] = 1

    for registro in [probabilistica, aleatoria]:

        registro["ID_enfrentamiento"] = id_partida

        registros.append(registro)

    print(
        f"Enfrentamiento {id_partida}: "
        f"Probabilistica = {p1}, Aleatoria = {p2}"
    )


# 8. EXPORTAR LOS DATOS A CSV

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
    "Resultado_partida",
    "Evento_A",
    "Evento_B"
]

with open(
    ARCHIVO_CSV, "w",
    newline="", encoding="utf-8-sig"
) as archivo:

    escritor = csv.DictWriter(
        archivo,
        fieldnames=columnas
    )

    escritor.writeheader()
    escritor.writerows(registros)


# 9. MOSTRAR RESUMEN DE LA SIMULACIÓN

print("\nSIMULACION FINALIZADA")
print("Enfrentamientos:", NUMERO_PAREJAS)
print("Partidas probabilisticas:", NUMERO_PAREJAS)
print("Partidas aleatorias:", NUMERO_PAREJAS)
print("Registros individuales:", len(registros))
print("Variables de estudio:", len(columnas) - 1)
print("Total de columnas:", len(columnas))
print("Archivo generado:", ARCHIVO_CSV)
