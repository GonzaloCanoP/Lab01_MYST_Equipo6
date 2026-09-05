"""Pruebas del Lab01, ejecutables con pytest.

El enunciado (3.6) nombra `tests/test_model.py` como archivo unico de pruebas,
asi que aqui viven tanto las tres pruebas obligatorias sobre `src/model.py`
como las pruebas adicionales que verifican `src/simulation.py`. No se crea un
segundo archivo: la estructura de carpetas del enunciado es exacta.

Como correrlas, desde la raiz del repositorio:

    pytest -v
    python -m pytest -v      # equivalente

Las tres pruebas obligatorias son:

1. `test_prob_ejecucion_nunca_es_negativa`
2. `test_perdida_informados_es_decreciente_en_el_ask`
3. `test_spread_optimo_con_pi_i_cero_es_el_del_monopolista`

Las demas son adicionales. Dos de ellas cargan el peso real del criterio de
pruebas significativas: `test_simulacion_converge_a_la_utilidad_esperada`, que
es la unica prueba del proyecto que verifica que el modelo y la simulacion son
el mismo objeto, y `test_condicion_de_primer_orden_del_optimo`, que contrasta
el optimo numerico contra la condicion de optimalidad derivada a mano.
"""

import pathlib
import sys

# pytest antepone tests/ a sys.path, no la raiz del proyecto, asi que
# `from src.model import ...` fallaria al invocar `pytest` a secas. Se agrega la
# raiz explicitamente para que las pruebas corran igual con `pytest` que con
# `python -m pytest`, y desde cualquier directorio de trabajo. Es plomeria de
# imports, no logica del proyecto.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd
import pytest

from src.model import (
    ALPHA,
    BETA,
    PI_I,
    PI_L,
    S0,
    SEED,
    analisis_sensibilidad,
    curva_teorica_spread,
    distribucion_valor,
    ganancia_liquidez,
    optimizar_cotizaciones,
    perdida_informados,
    prediccion_teorica_spread,
    prob_ejecucion,
    utilidad_esperada,
)
from src.simulation import construir_regimenes, simular_trades


# --------------------------------------------------------------------------- #
# Prueba obligatoria 1 — no negatividad de la demanda de liquidez
# --------------------------------------------------------------------------- #

def test_prob_ejecucion_nunca_es_negativa():
    """pi_LB(s) y pi_LS(s) nunca devuelven un valor negativo.

    `prob_ejecucion` es una probabilidad, y ALPHA - BETA*s se vuelve negativa a
    partir de s = ALPHA/BETA = 6.25. Sin el truncamiento en cero el optimizador
    encontraria "ganancia" ensanchando el spread al infinito, porque el producto
    de una probabilidad negativa por un medio spread positivo entra sumando con
    el signo equivocado. Por eso esta prueba barre hasta s = 20, muy por encima
    del punto de corte, y no solo el rango donde el modelo se porta bien.

    Se evalua escalar y array a proposito: P3 llama a esta funcion con un
    np.linspace para la Figura 1, asi que si alguien la reescribe con un `if`
    de Python en lugar de `np.maximum`, esta prueba lo detecta aqui y no en
    medio de la generacion de figuras.
    """
    malla = np.linspace(0.0, 20.0, 2001)

    valores = prob_ejecucion(malla)
    assert isinstance(valores, np.ndarray), "prob_ejecucion debe estar vectorizada"
    assert valores.shape == malla.shape
    assert np.all(valores >= 0.0), (
        f"valor negativo en s = {malla[valores < 0.0]}"
    )

    for s in (0.0, 3.125, 6.25, 6.26, 100.0, -1.0):
        valor = prob_ejecucion(s)
        assert np.ndim(valor) == 0, "el escalar debe devolver un escalar"
        assert valor >= 0.0, f"prob_ejecucion({s}) = {valor} es negativa"

    # Anclas concretas: en s = 0 vale ALPHA, y ya esta agotada en el corte.
    assert prob_ejecucion(0.0) == pytest.approx(ALPHA)
    assert prob_ejecucion(ALPHA / BETA) == pytest.approx(0.0, abs=1e-12)
    assert prob_ejecucion(1.50) == pytest.approx(0.38)  # el regimen amplio


# --------------------------------------------------------------------------- #
# Prueba obligatoria 2 — monotonia de la perdida frente a informados
# --------------------------------------------------------------------------- #

def test_perdida_informados_es_decreciente_en_el_ask():
    """La perdida esperada frente a informados decrece en A.

    Mientras mas arriba cotizas el ask, menos te pega el informado que compra:
    el integrando (P - A) se evalua sobre una cola cada vez mas delgada de la
    Erlang y ademas con un exceso (P - A) cada vez menor. Los dos efectos
    empujan en la misma direccion.

    Se usa SOLO el primer elemento de la tupla (el lado ask), no la suma de los
    dos lados: el lado del bid depende de B y no de A, asi que sumarlos no
    cambiaria nada aqui, pero la version equivocada de esta prueba -- variar el
    spread completo y sumar -- si se romperia, porque los dos lados se mueven en
    direcciones contrarias. La prueba mide lo que dice medir.
    """
    valores_de_A = [20.0, 21.0, 22.0, 23.0, 24.0, 25.0]

    perdidas = [perdida_informados(A, 19.0)[0] for A in valores_de_A]

    for A_previo, A_actual, previa, actual in zip(
        valores_de_A, valores_de_A[1:], perdidas, perdidas[1:]
    ):
        assert actual < previa, (
            f"la perdida no decrecio entre A = {A_previo} ({previa:.6f}) y "
            f"A = {A_actual} ({actual:.6f})"
        )

    # Y ademas nunca es negativa: (P - A) > 0 en todo el rango de integracion,
    # por eso en Pi(A, B) esta cantidad entra con un signo negativo explicito.
    assert all(p >= 0.0 for p in perdidas)


# --------------------------------------------------------------------------- #
# Prueba obligatoria 3 — el caso del monopolista (punto abierto O1)
# --------------------------------------------------------------------------- #

def test_spread_optimo_con_pi_i_cero_es_el_del_monopolista():
    """Con pi_i = 0 el spread optimo coincide con el resultado analitico.

    Sin traders informados no hay seleccion adversa, la utilidad se separa en
    dos problemas independientes y cada lado maximiza

        (ALPHA - BETA*s) * s

    cuya condicion de primer orden es

        d/ds [(0.50 - 0.08 s) s] = 0.50 - 0.16 s = 0   =>   s* = 0.50 / 0.16

    o sea s* = ALPHA / (2*BETA) = 3.125 de MEDIO spread por lado, y por lo tanto
    2 * 3.125 = 6.25 de spread TOTAL.

    Punto abierto O1: el enunciado escribe "0.50/0.08 por lado", y 0.50/0.08 es
    6.25. Bajo la derivacion de arriba, 6.25 es el total y 3.125 es el de cada
    lado. Son la misma afirmacion matematica leida de dos formas, asi que esta
    prueba verifica LAS DOS y pasa sin importar cual era la intencion del
    enunciado. Si el profesor pregunta cual es, la respuesta es la derivada de
    arriba, no una preferencia.
    """
    resultado = optimizar_cotizaciones(pi_i=0.0)

    assert resultado["convergio"], resultado["mensaje"]

    medio_spread_ask = resultado["ask"] - S0
    medio_spread_bid = S0 - resultado["bid"]

    # Lectura 1: "por lado" = medio spread de cada lado = ALPHA/(2*BETA).
    assert medio_spread_ask == pytest.approx(ALPHA / (2 * BETA), abs=1e-3)
    assert medio_spread_bid == pytest.approx(ALPHA / (2 * BETA), abs=1e-3)
    assert medio_spread_ask == pytest.approx(3.125, abs=1e-3)

    # Lectura 2: "0.50/0.08" = spread total.
    assert resultado["spread"] == pytest.approx(ALPHA / BETA, abs=1e-3)
    assert resultado["spread"] == pytest.approx(6.25, abs=1e-3)

    # El valor de la utilidad tambien es analitico: dos lados, cada uno
    # (ALPHA - BETA*s*)*s* = 0.25 * 3.125 = 0.78125, que suman 1.5625.
    assert resultado["utilidad_esperada"] == pytest.approx(2 * 0.25 * 3.125, abs=1e-6)


# --------------------------------------------------------------------------- #
# Prueba adicional — la condicion de optimalidad con pi_i > 0 (punto abierto O3)
# --------------------------------------------------------------------------- #

def test_condicion_de_primer_orden_del_optimo():
    """El optimo numerico satisface la condicion de optimalidad derivada a mano.

    Derivando Pi(A, B) respecto de A, con a = A - S0:

        dPi/dA = pi_L * (ALPHA - 2*BETA*a) + pi_I * (1 - F(A)) = 0

    que se reordena como

        pi_L * (2*BETA*a* - ALPHA)  =  pi_I * (1 - F(A*))

    Izquierda: lo que cuesta ensanchar un centavo mas, en ganancia de liquidez
    que se espanta. Derecha: lo que ahorra ese centavo, en perdida frente a
    informados que ya no ocurre. En el optimo se igualan.

    El analogo del lado del bid, con b = S0 - B, es

        pi_L * (2*BETA*b* - ALPHA)  =  pi_I * F(B*)

    Esta prueba vale por dos razones. Primero, es un arbitro independiente de
    L-BFGS-B: `quad` mete ruido numerico del orden de 1e-10 en Pi, el gradiente
    por diferencias finitas lo amplifica, y esta identidad se evalua sin usar el
    optimizador. Segundo, es la prediccion teorica del punto abierto O3 en forma
    verificable: con pi_i = 0 el lado derecho se anula y se recupera
    a* = ALPHA/(2*BETA) = 3.125, y como el lado izquierdo crece en a, subir pi_i
    obliga a subir el spread. La comparacion del analisis de sensibilidad contra
    la teoria deja de ser cualitativa.
    """
    F = distribucion_valor().cdf
    supervivencia = distribucion_valor().sf

    for pi_i in (0.1, 0.4, 0.7):
        pi_l = 1.0 - pi_i
        resultado = optimizar_cotizaciones(pi_i=pi_i)
        assert resultado["convergio"], resultado["mensaje"]

        a = resultado["ask"] - S0
        b = S0 - resultado["bid"]

        costo_marginal_ask = pi_l * (2 * BETA * a - ALPHA)
        ahorro_marginal_ask = pi_i * supervivencia(resultado["ask"])

        costo_marginal_bid = pi_l * (2 * BETA * b - ALPHA)
        ahorro_marginal_bid = pi_i * F(resultado["bid"])

        assert costo_marginal_ask == pytest.approx(ahorro_marginal_ask, abs=1e-5), (
            f"la condicion de primer orden del ask no se cumple en pi_i = {pi_i}"
        )
        assert costo_marginal_bid == pytest.approx(ahorro_marginal_bid, abs=1e-5), (
            f"la condicion de primer orden del bid no se cumple en pi_i = {pi_i}"
        )


def test_el_spread_optimo_crece_con_la_proporcion_de_informados():
    """Mas traders informados => spread mas ancho y menos utilidad.

    Es la prediccion cualitativa que se sigue de la condicion de primer orden de
    `test_condicion_de_primer_orden_del_optimo`, verificada sobre la tabla que
    consume la figura de sensibilidad. Tambien blinda el contrato: si alguien
    cambia las columnas del DataFrame, esta prueba se rompe antes que la figura.
    """
    df = analisis_sensibilidad(valores_pi=(0.1, 0.4, 0.7))

    assert list(df.columns) == [
        "pi_i", "bid", "ask", "spread", "utilidad_esperada", "convergio",
    ]
    assert df["convergio"].all(), "algun caso del analisis no convergio"

    assert df["spread"].is_monotonic_increasing
    assert df["utilidad_esperada"].is_monotonic_decreasing


def test_utilidad_esperada_no_usa_la_constante_global_pi_l():
    """pi_l se calcula como 1 - pi_i, no se lee de PI_L.

    Este es el bug invisible del proyecto: para pi_i = 0.4 los dos caminos dan
    exactamente el mismo numero, porque PI_L vale 0.60 = 1 - 0.40. Solo se
    separan en los otros escenarios de sensibilidad. Se comprueba reconstruyendo
    la utilidad a mano con pi_l = 1 - pi_i y exigiendo que coincida.
    """
    assert PI_L == pytest.approx(1.0 - PI_I)

    A, B = 23.0, 17.0
    for pi_i in (0.0, 0.1, 0.7, 1.0):
        lado_ask, lado_bid = perdida_informados(A, B)
        esperado = (1.0 - pi_i) * ganancia_liquidez(A, B) - pi_i * (lado_ask + lado_bid)

        assert utilidad_esperada(A, B, pi_i=pi_i) == pytest.approx(esperado, rel=1e-12)


def test_la_erlang_esta_bien_parametrizada():
    """Media 20.0 y desviacion estandar 2.582, con scale = 1/lambda.

    El error clasico es pasar `scale=LAMBDA_ERLANG` en vez de
    `scale=1/LAMBDA_ERLANG`: la media saldria 180 en lugar de 20, el modelo
    entero quedaria mal y scipy no lanzaria ningun error. La prueba tambien deja
    escrito el hecho que se usa despues en el analisis: S0 = 19.90 esta 0.10 por
    DEBAJO del valor esperado verdadero, y ese sesgo no es accidental.
    """
    dist = distribucion_valor()

    assert dist.mean() == pytest.approx(20.0, abs=1e-9)
    assert dist.std() == pytest.approx(np.sqrt(60) / 3, abs=1e-9)
    assert dist.std() == pytest.approx(2.582, abs=1e-3)

    assert S0 < dist.mean()
    assert dist.mean() - S0 == pytest.approx(0.10, abs=1e-9)


# --------------------------------------------------------------------------- #
# Pruebas adicionales — la simulacion
# --------------------------------------------------------------------------- #

def test_simular_trades_es_reproducible_con_la_misma_semilla():
    """La misma semilla da el mismo DataFrame; una distinta, uno distinto.

    Sin la primera mitad, "semilla fija" es una frase en el README. Sin la
    segunda, la prueba pasaria igual si alguien dejara la simulacion clavada en
    un resultado constante.
    """
    primera = simular_trades(19.0, 21.0, n_trades=1_000, seed=SEED)
    segunda = simular_trades(19.0, 21.0, n_trades=1_000, seed=SEED)
    otra = simular_trades(19.0, 21.0, n_trades=1_000, seed=SEED + 1)

    pd.testing.assert_frame_equal(primera, segunda)
    assert not primera["pnl"].equals(otra["pnl"])


def test_simular_trades_respeta_el_contrato_de_columnas():
    """Columnas exactas, en orden, y la contabilidad del P&L fila por fila.

    Las firmas congeladas del CLAUDE.md son lo que permite que P1, P2 y P3 se
    escriban en paralelo, asi que se verifican como cualquier otra propiedad.

    La parte de contabilidad reconstruye el P&L y el delta de inventario de cada
    trade desde cero y exige que coincidan con lo que reporto el simulador. Ojo
    con la asimetria, que es el corazon del modelo: frente a liquidez el trade
    se marca contra S0, frente a informados contra el valor verdadero P. Eso es
    la seleccion adversa, no una convencion contable.
    """
    bid, ask = 19.0, 21.0
    df = simular_trades(bid, ask, n_trades=5_000, seed=SEED)

    assert list(df.columns) == [
        "trade_id", "tipo_trader", "direccion", "ejecutado", "valor_verdadero",
        "precio_ejecucion", "pnl", "delta_inventario", "pnl_acumulado", "inventario",
    ]
    assert set(df["tipo_trader"].unique()) <= {"informado", "liquidez"}
    assert set(df["direccion"].unique()) <= {"compra", "venta", "ninguna"}

    # Un trade no ejecutado no deja P&L ni mueve inventario.
    sin_ejecutar = df[~df["ejecutado"]]
    assert (sin_ejecutar["pnl"] == 0.0).all()
    assert (sin_ejecutar["delta_inventario"] == 0).all()
    assert sin_ejecutar["precio_ejecucion"].isna().all()

    ejecutados = df[df["ejecutado"]]
    informado = ejecutados["tipo_trader"] == "informado"
    compra = ejecutados["direccion"] == "compra"

    # Referencia contra la que se marca cada trade: P si es informado, S0 si no.
    referencia = np.where(informado, ejecutados["valor_verdadero"], S0)
    # El MM vende al ask cuando el trader compra, y compra al bid cuando vende.
    precio = np.where(compra, ask, bid)
    signo = np.where(compra, 1.0, -1.0)

    pnl_esperado = signo * (precio - referencia)
    delta_esperado = np.where(compra, -1, 1)

    np.testing.assert_allclose(ejecutados["pnl"], pnl_esperado, rtol=1e-12)
    np.testing.assert_array_equal(ejecutados["delta_inventario"], delta_esperado)
    np.testing.assert_allclose(ejecutados["precio_ejecucion"], precio, rtol=1e-12)

    # Un informado solo cruza cuando le conviene: nunca le deja P&L al formador.
    assert (ejecutados.loc[informado, "pnl"] <= 0.0).all()

    # Acumulados coherentes con las columnas por trade.
    np.testing.assert_allclose(df["pnl_acumulado"], df["pnl"].cumsum(), rtol=1e-12)
    np.testing.assert_array_equal(df["inventario"], df["delta_inventario"].cumsum())


def test_el_informado_no_opera_dentro_de_la_banda():
    """Convencion del punto abierto O2, verificada donde mas se nota.

    Si B <= P <= A el informado no tiene incentivo de ningun lado: comprar al
    ask le costaria mas de lo que vale y vender al bid le pagaria menos. La
    convencion del proyecto es dejar la fila sin ejecutar, con P&L cero.

    Se prueba con el regimen amplio (18.40 / 21.40), donde la banda cubre casi
    toda la masa de la Erlang y por lo tanto la gran mayoria de los informados
    debe quedarse fuera. Con un bid y un ask pegados a S0 la prueba pasaria por
    poco y no distinguiria una implementacion correcta de una accidental.
    """
    bid, ask = 18.40, 21.40
    df = simular_trades(bid, ask, n_trades=10_000, seed=SEED)

    informados = df[df["tipo_trader"] == "informado"]
    en_la_banda = informados[
        informados["valor_verdadero"].between(bid, ask, inclusive="both")
    ]

    assert len(en_la_banda) > 0, "la prueba no esta tocando el caso que dice probar"
    assert (~en_la_banda["ejecutado"]).all()
    assert (en_la_banda["direccion"] == "ninguna").all()
    assert (en_la_banda["pnl"] == 0.0).all()
    assert (en_la_banda["delta_inventario"] == 0).all()

    # Y fuera de la banda si opera, del lado que le conviene.
    fuera = informados[~informados.index.isin(en_la_banda.index)]
    assert fuera["ejecutado"].all()


def test_simulacion_converge_a_la_utilidad_esperada():
    """El P&L promedio simulado converge a Pi(A, B) del modelo.

    Es la unica prueba del proyecto que verifica que el modelo y la simulacion
    son el mismo objeto y no dos implementaciones que casualmente corren. Si
    esta pasa, la contabilidad del P&L de `simular_trades` esta escrita con el
    mismo criterio que la utilidad esperada de `utilidad_esperada`; si falla, uno
    de los dos esta mal y el resto del laboratorio no significa nada.

    Se usa `forzar_ejecucion=False` a proposito. Pi(A, B) pondera la ganancia de
    liquidez por `prob_ejecucion`, o sea supone que el trader de liquidez puede
    NO ejecutar. La simulacion del enunciado corre con `forzar_ejecucion=True`,
    que es otro objeto: ahi el trader de liquidez siempre cruza, y el P&L
    promedio sale muy por encima de Pi. Comparar la version forzada contra Pi
    seria comparar dos cosas distintas.

    300,000 trades con tolerancia del 2%: el error de muestreo de la media va
    como 1/sqrt(n), y a este tamano queda holgadamente dentro. La tolerancia es
    la del enunciado, no una ajustada al resultado.
    """
    resultado = optimizar_cotizaciones()
    bid, ask = resultado["bid"], resultado["ask"]

    df = simular_trades(bid, ask, n_trades=300_000, seed=SEED, forzar_ejecucion=False)

    pnl_simulado = df["pnl"].mean()
    utilidad_modelo = utilidad_esperada(ask, bid)

    error_relativo = abs(pnl_simulado - utilidad_modelo) / abs(utilidad_modelo)

    assert error_relativo < 0.02, (
        f"la simulacion no reproduce el modelo: simulado = {pnl_simulado:.6f}, "
        f"modelo = {utilidad_modelo:.6f}, error relativo = {error_relativo:.4%}"
    )


def test_construir_regimenes_devuelve_los_tres_del_enunciado():
    """Llaves exactas y valores fijos de estrecho y amplio.

    El regimen optimo pasa por argumento, sin redondear: P2 usa esos precios
    como precio de ejecucion, y redondear a dos decimales mete un sesgo pequeno
    pero real en el P&L acumulado de 10,000 trades.
    """
    regimenes = construir_regimenes(16.5, 23.5)

    assert list(regimenes) == ["optimo", "estrecho", "amplio"]
    assert regimenes["optimo"] == (16.5, 23.5)
    assert regimenes["estrecho"] == (19.75, 20.05)
    assert regimenes["amplio"] == (18.40, 21.40)


def test_prediccion_teorica_coincide_con_el_optimo_numerico():
    """La CPO descompone el medio spread en monopolista mas prima, y cierra.

    Es la comparacion que pide el enunciado (3.5) contra la prediccion teorica,
    en forma verificable:

        a* = ALPHA/(2*BETA) + (pi_I/pi_L) * (1 - F(A*)) / (2*BETA)

    El residuo tiene que ser numericamente cero. La tolerancia de 1e-4 es
    holgada respecto de lo que se observa (orden 1e-6) porque el residuo hereda
    la precision de L-BFGS-B, no la de la identidad: si el optimizador se
    detiene un poco antes, el residuo sube sin que la teoria este mal.

    La prima frente a pi_i = 0 es exactamente cero, y crece de forma estricta
    con pi_i: esa es la prediccion cualitativa del modelo -- mas informados,
    spread mas ancho -- ahora con el numero al lado.
    """
    predicciones = [prediccion_teorica_spread(pi_i) for pi_i in (0.0, 0.1, 0.4, 0.7)]

    for pred in predicciones:
        assert pred["residuo_ask"] < 1e-4, pred
        assert pred["residuo_bid"] < 1e-4, pred
        assert pred["spread_teorico"] == pytest.approx(pred["spread_numerico"], abs=1e-4)

    # Sin informados no hay prima: se recupera el monopolista exacto.
    assert predicciones[0]["prima_ask"] == pytest.approx(0.0, abs=1e-12)
    assert predicciones[0]["monopolista"] == pytest.approx(ALPHA / (2 * BETA))

    # Y la prima crece de forma estricta con pi_i, de los dos lados.
    primas_ask = [p["prima_ask"] for p in predicciones]
    primas_bid = [p["prima_bid"] for p in predicciones]
    assert primas_ask == sorted(primas_ask) and len(set(primas_ask)) == len(primas_ask)
    assert primas_bid == sorted(primas_bid) and len(set(primas_bid)) == len(primas_bid)


def test_prediccion_teorica_falla_fuerte_si_no_hay_liquidez():
    """Con pi_i = 1 la CPO no existe, y se dice, no se devuelve un NaN.

    Sin traders de liquidez no hay ingreso que compensar la perdida frente a
    informados: el problema deja de tener un optimo interior y el cociente
    pi_I/pi_L se indefine. Devolver `inf` o `nan` en silencio propagaria basura
    hasta la tabla del reporte. Se levanta ValueError con el motivo.
    """
    with pytest.raises(ValueError, match="pi_i = 1"):
        prediccion_teorica_spread(pi_i=1.0)


def test_curva_teorica_resuelta_con_brentq_coincide_con_el_optimizador():
    """Dos metodos numericos independientes dan el mismo spread optimo.

    `analisis_sensibilidad` usa L-BFGS-B, que aproxima el gradiente por
    diferencias finitas sobre una utilidad que `quad` contamina con ruido de
    orden 1e-10. `curva_teorica_spread` usa `brentq`, una biseccion sobre el
    cambio de signo de la CPO que no toca gradientes ni llama al optimizador.

    No comparten fuente de error, asi que coincidir no es tautologico: es la
    verificacion que pide el enunciado (3.5) al comparar el resultado numerico
    contra la prediccion teorica. Si alguien rompiera la funcion objetivo, las
    dos curvas se separarian y esta prueba lo diria.
    """
    df_numerico = analisis_sensibilidad(valores_pi=(0.1, 0.4, 0.7))
    df_teorico = curva_teorica_spread(df_numerico["pi_i"].to_numpy())

    assert list(df_teorico.columns) == [
        "pi_i", "medio_spread_ask", "medio_spread_bid", "spread",
    ]

    for spread_numerico, spread_teorico in zip(
        df_numerico["spread"], df_teorico["spread"]
    ):
        assert spread_numerico == pytest.approx(spread_teorico, abs=1e-4)


def test_la_curva_teorica_arranca_en_el_monopolista_y_crece():
    """Con pi_i = 0 la CPO da 3.125 por lado; de ahi solo puede subir.

    Es la prediccion cualitativa del modelo con el numero al lado: el spread
    tiene un piso que no depende de la informacion asimetrica, y todo lo que
    esta por encima es prima de seleccion adversa. La figura de sensibilidad
    dibuja exactamente esta afirmacion.
    """
    curva = curva_teorica_spread(np.linspace(0.0, 0.9, 10))

    assert curva.loc[0, "medio_spread_ask"] == pytest.approx(ALPHA / (2 * BETA), abs=1e-9)
    assert curva.loc[0, "spread"] == pytest.approx(ALPHA / BETA, abs=1e-9)

    assert curva["spread"].is_monotonic_increasing
    assert (curva["spread"] >= ALPHA / BETA - 1e-9).all()

    # Y nunca se sale del rango donde prob_ejecucion es positiva y la CPO vale.
    assert (curva["medio_spread_ask"] <= ALPHA / BETA).all()
    assert (curva["medio_spread_bid"] <= ALPHA / BETA).all()
