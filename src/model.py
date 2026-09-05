"""Modelo de Copeland y Galai (1983) para un formador de mercado.

Este modulo concentra tres cosas:

1. Los parametros del caso base del enunciado. Se definen aqui y solo aqui;
   `simulation.py`, `plots.py`, `tests/` y `main.py` los importan de `src.model`.
2. La utilidad esperada por trade Pi(A, B): la ganancia frente a traders de
   liquidez menos la perdida frente a traders informados.
3. La optimizacion de las cotizaciones y el analisis de sensibilidad en pi_i.

La intuicion del modelo: el formador de mercado publica un Bid B y un Ask A
alrededor de un precio de referencia S0. Frente a un trader de liquidez gana el
medio spread, porque ese trader opera por razones ajenas al valor. Frente a un
trader informado pierde, porque el informado solo cruza cuando el valor
verdadero P esta fuera de las cotizaciones. Ensanchar el spread sube la ganancia
por trade pero baja la probabilidad de que alguien opere: ahi esta el trade-off
que se optimiza.
"""

import warnings

import numpy as np
import pandas as pd
from scipy import integrate, optimize, stats

# --------------------------------------------------------------------------- #
# Parametros del caso base (enunciado, seccion 3.1)
# --------------------------------------------------------------------------- #

S0 = 19.90            # precio de referencia publicado por el formador
K_ERLANG = 60         # parametro de forma de la Erlang
LAMBDA_ERLANG = 3     # parametro de tasa de la Erlang
PI_I = 0.40           # probabilidad de que llegue un trader informado
PI_L = 0.60           # probabilidad de que llegue un trader de liquidez
ALPHA = 0.50          # intercepto de la demanda de liquidez
BETA = 0.08           # pendiente de la demanda de liquidez
SEED = 42             # semilla unica del proyecto

# Tolerancia sobre el error absoluto que reporta `quad`. Por encima de esto la
# integral no es confiable y se advierte en vez de seguir en silencio.
TOL_QUAD = 1e-8


# --------------------------------------------------------------------------- #
# Distribucion del valor verdadero
# --------------------------------------------------------------------------- #

def distribucion_valor():
    """Distribucion del valor verdadero del activo, P ~ Erlang(K, lambda).

    Devuelve un objeto congelado de scipy, no una muestra. P2 lo usa para
    samplear el valor verdadero en la simulacion y P1 para integrar la perdida
    esperada: que ambas partes usen literalmente el mismo objeto es lo que hace
    que modelo y simulacion sean comparables.

    Cuidado con la parametrizacion: scipy pide `scale`, que es 1/lambda, no
    lambda. Con `scale=3` la media saldria 180 en vez de 20 y nada lanzaria un
    error. Por eso hay un assert de modulo justo debajo.
    """
    return stats.erlang(a=K_ERLANG, scale=1.0 / LAMBDA_ERLANG)


# Verificacion al importar: media = K/lambda = 60/3 = 20.0.
assert abs(distribucion_valor().mean() - 20.0) < 1e-9, (
    "La Erlang esta mal parametrizada: revisa que scale sea 1/LAMBDA_ERLANG."
)


# --------------------------------------------------------------------------- #
# Demanda de liquidez
# --------------------------------------------------------------------------- #

def prob_ejecucion(s):
    """Probabilidad de que un trader de liquidez ejecute contra un medio spread s.

    pi_LB(s) = pi_LS(s) = max(0, ALPHA - BETA*s). Es la misma funcion de los dos
    lados: el modelo supone demanda de liquidez simetrica.

    Se trunca en cero porque una probabilidad negativa no significa nada: a
    partir de s = ALPHA/BETA = 6.25 ya no queda nadie dispuesto a cruzar. Sin el
    truncamiento el optimizador encontraria "ganancia" ensanchando el spread al
    infinito, que es exactamente el artefacto numerico que hay que evitar.

    Acepta escalares y arrays (P3 la llama con un np.linspace para la Figura 1).
    """
    return np.maximum(0.0, ALPHA - BETA * np.asarray(s, dtype=float))[()]


# --------------------------------------------------------------------------- #
# Los dos componentes de la utilidad
# --------------------------------------------------------------------------- #

def _integrar(funcion, limite_inferior, limite_superior, etiqueta):
    """Envoltura de `scipy.integrate.quad` que no esconde el error numerico.

    `quad` devuelve (valor, error_absoluto_estimado). El segundo suele ignorarse;
    aqui se revisa y se advierte si supera TOL_QUAD, porque una integral que no
    alcanzo tolerancia contamina el gradiente del optimizador sin lanzar ninguna
    excepcion.
    """
    valor, error = integrate.quad(funcion, limite_inferior, limite_superior)
    if error > TOL_QUAD:
        warnings.warn(
            f"quad no alcanzo tolerancia en {etiqueta}: error absoluto estimado "
            f"{error:.3e} > {TOL_QUAD:.0e} (valor = {valor:.6e}).",
            RuntimeWarning,
            stacklevel=3,
        )
    return valor


def perdida_informados(A, B):
    """Perdida esperada frente a traders informados, desglosada por lado.

    Devuelve la tupla (lado_ask, lado_bid), no la suma, porque el desglose es
    lo que permite decir de que lado duele mas la seleccion adversa.

        lado_ask = integral de A a infinito de (P - A) f(P) dP
        lado_bid = integral de 0 a B de (B - P) f(P) dP

    Por que el lado del ask integra desde A y no desde S0: el informado solo
    compra al ask cuando el valor verdadero supera el precio que le estan
    cobrando, es decir cuando P > A. Si S0 < P < A el informado sabe que el
    activo vale mas que la referencia, pero no lo suficiente para pagar el ask;
    no opera. El limite de integracion es la cotizacion, no la referencia.

    Ambos valores son mayores o iguales a cero por construccion: el integrando
    (P - A) es positivo en todo el rango de integracion, y lo mismo (B - P).
    Por eso en Pi(A, B) esta cantidad entra restando, con signo negativo
    explicito, en vez de venir ya firmada.
    """
    f = distribucion_valor().pdf

    lado_ask = _integrar(lambda P: (P - A) * f(P), A, np.inf, "lado ask")
    lado_bid = _integrar(lambda P: (B - P) * f(P), 0.0, B, "lado bid")

    return lado_ask, lado_bid


def ganancia_liquidez(A, B):
    """Ganancia esperada frente a traders de liquidez, sin ponderar por pi_L.

        pi_LB(A - S0)*(A - S0) + pi_LS(S0 - B)*(S0 - B)

    Cada sumando es "probabilidad de que ejecuten" por "cuanto gano si ejecutan".
    Frente a liquidez el trade se marca contra S0 porque el formador no aprende
    nada del flujo no informado.

    Devuelve el corchete crudo, sin multiplicar por pi_L, para que
    `utilidad_esperada` pueda ponderarlo con el pi_l que corresponda al escenario
    de sensibilidad que se este evaluando.
    """
    medio_spread_ask = A - S0
    medio_spread_bid = S0 - B

    return (
        prob_ejecucion(medio_spread_ask) * medio_spread_ask
        + prob_ejecucion(medio_spread_bid) * medio_spread_bid
    )


def utilidad_esperada(A, B, pi_i=PI_I):
    """Utilidad esperada por trade del formador de mercado, Pi(A, B).

        Pi(A,B) = pi_L * [ganancia frente a liquidez]
                - pi_I * [perdida frente a informados]

    `pi_l` se calcula aqui como 1 - pi_i y NO se lee de la constante global
    PI_L. Si se leyera de la global, el analisis de sensibilidad quedaria mal y
    el error seria invisible: para pi_i = 0.4 los dos caminos dan el mismo
    numero, y solo se separan en pi_i = 0.1 y 0.7.
    """
    pi_l = 1.0 - pi_i

    lado_ask, lado_bid = perdida_informados(A, B)

    return pi_l * ganancia_liquidez(A, B) - pi_i * (lado_ask + lado_bid)


# --------------------------------------------------------------------------- #
# Optimizacion
# --------------------------------------------------------------------------- #

def objetivo(x, pi_i=PI_I):
    """Funcion objetivo a minimizar: el negativo de Pi(A, B).

    `scipy.optimize.minimize` solo minimiza. Maximizar Pi equivale a minimizar
    -Pi, con el mismo argmax. x = [A, B].
    """
    A, B = x
    return -utilidad_esperada(A, B, pi_i=pi_i)


def optimizar_cotizaciones(pi_i=PI_I):
    """Encuentra el (Bid, Ask) que maximiza la utilidad esperada por trade.

    Restricciones del enunciado: A en [S0, inf) y B en (0, S0]. El cero abierto
    del bid se implementa con una cota inferior de 1e-6, porque L-BFGS-B pide
    cotas cerradas.

    Punto inicial [S0 + 1, S0 - 1]: un spread de 2 unidades, dentro del rango
    donde la probabilidad de ejecucion todavia es positiva. Arrancar en S0 exacto
    dejaria al optimizador en un punto con gradiente ambiguo.

    Devuelve precision completa, sin redondear: P2 usa estos valores como precios
    de ejecucion y redondear aqui mete un sesgo pequeno pero real en el P&L
    acumulado de 10,000 trades. El redondeo a dos decimales es cosa del reporte.

    Si el optimizador no converge se registra en la llave `convergio` y el
    mensaje de scipy viaja en `mensaje`. No se maquilla un resultado malo.
    """
    x0 = [S0 + 1.0, S0 - 1.0]
    bounds = [(S0, None), (1e-6, S0)]

    res = optimize.minimize(
        objetivo,
        x0=x0,
        args=(pi_i,),
        method="L-BFGS-B",
        bounds=bounds,
    )

    ask, bid = float(res.x[0]), float(res.x[1])

    return {
        "bid": bid,
        "ask": ask,
        "spread": ask - bid,
        "utilidad_esperada": -float(res.fun),
        "pi_i": pi_i,
        "convergio": bool(res.success),
        "mensaje": str(res.message),
    }


def verificar_optimo_en_malla(resultado, paso=0.01, radio=0.30, tol=0.02):
    """Contrasta el optimo de L-BFGS-B contra un barrido en malla fina.

    Por que hace falta: `quad` introduce ruido numerico del orden de 1e-10 en el
    valor de Pi. L-BFGS-B aproxima el gradiente por diferencias finitas, asi que
    ese ruido se amplifica al dividir entre el paso. Un optimo que se ve bien
    puede estar desplazado. La malla no usa gradiente y sirve de arbitro.

    Va fuera de `optimizar_cotizaciones` a proposito: evalua unos miles de veces
    la utilidad y encarecerla en cada llamada no tiene sentido cuando la
    verificacion solo se corre una vez.

    Devuelve un dict con el punto de la malla, las diferencias contra el optimo
    y la bandera `coincide` (ambas diferencias por debajo de `tol`).
    """
    pi_i = resultado["pi_i"]

    # La malla se ancla en multiplos exactos de `paso`, no en el optimo mismo.
    # Si se anclara en el optimo, ese punto caeria dentro de la rejilla y la
    # verificacion se responderia sola: siempre coincidiria por construccion.
    centro_ask = round(resultado["ask"] / paso) * paso
    centro_bid = round(resultado["bid"] / paso) * paso

    rejilla_ask = np.arange(
        max(S0, centro_ask - radio), centro_ask + radio + paso / 2, paso
    )
    rejilla_bid = np.arange(
        centro_bid - radio, min(S0, centro_bid + radio) + paso / 2, paso
    )

    mejor_utilidad = -np.inf
    mejor_ask, mejor_bid = np.nan, np.nan

    for A in rejilla_ask:
        for B in rejilla_bid:
            u = utilidad_esperada(A, B, pi_i=pi_i)
            if u > mejor_utilidad:
                mejor_utilidad, mejor_ask, mejor_bid = u, A, B

    dif_ask = abs(mejor_ask - resultado["ask"])
    dif_bid = abs(mejor_bid - resultado["bid"])

    return {
        "pi_i": pi_i,
        "ask_malla": float(mejor_ask),
        "bid_malla": float(mejor_bid),
        "utilidad_malla": float(mejor_utilidad),
        "dif_ask": float(dif_ask),
        "dif_bid": float(dif_bid),
        "coincide": bool(dif_ask <= tol and dif_bid <= tol),
    }


def analisis_sensibilidad(valores_pi=(0.1, 0.4, 0.7)):
    """Reoptimiza para cada pi_i y devuelve el resultado como DataFrame.

    Lo que se espera ver: a mayor proporcion de traders informados, mayor spread
    optimo y menor utilidad. El formador se defiende de la seleccion adversa de
    la unica forma que puede, ensanchando las cotizaciones, y eso a su vez le
    espanta flujo de liquidez.

    La grafica de spread contra pi_i es de P3; aqui solo se produce la tabla que
    la alimenta.
    """
    filas = [optimizar_cotizaciones(pi_i=pi) for pi in valores_pi]

    return pd.DataFrame(filas)[
        ["pi_i", "bid", "ask", "spread", "utilidad_esperada", "convergio"]
    ]


def prediccion_teorica_spread(pi_i=PI_I):
    """Medio spread optimo predicho por la condicion de primer orden (CPO).

    Es la "prediccion teorica" que pide el enunciado (3.5) para contrastar
    contra el resultado numerico del analisis de sensibilidad. Es la misma CPO
    de la sesion de Copeland-Galai del curso, que en su ejemplo discreto se
    escribe `pi_L*(0.5 - 0.1*d) + pi_I*(0.10) = 0`; aqui se usa la version
    general del modelo continuo.

    Derivacion. Con a = A - S0, la utilidad esperada es

        Pi = pi_L*[(ALPHA - BETA*a)*a + ...] - pi_I*[int_A^inf (P-A) f(P) dP + ...]

    Derivando respecto de A, y usando que d/dA int_A^inf (P-A) f(P) dP = -(1-F(A)):

        dPi/dA = pi_L*(ALPHA - 2*BETA*a) + pi_I*(1 - F(A)) = 0

    que se despeja como

        a* = ALPHA/(2*BETA) + (pi_I/pi_L) * (1 - F(A*)) / (2*BETA)
             |_____________|   |_______________________________|
              monopolista            prima de seleccion adversa

    El primer termino es el medio spread del monopolista sin informados, 3.125
    con los parametros del caso base, y es exactamente lo que verifica la prueba
    obligatoria con pi_i = 0. El segundo es lo que hay que cobrar de mas para
    financiar la opcion que se le regala al informado, y crece con pi_i por dos
    vias: el cociente pi_I/pi_L y, en menor medida, la cola de la Erlang.

    Analogo del lado del bid, con b = S0 - B:

        b* = ALPHA/(2*BETA) + (pi_I/pi_L) * F(B*) / (2*BETA)

    OJO: es una identidad IMPLICITA, no una formula cerrada. El lado derecho
    depende de A*, que es justo lo que se quiere despejar. En el ejemplo de
    clase (1 - F(A)) es una constante de 0.10 porque la distribucion es discreta
    y el optimo no cambia de estado, y por eso ahi si sale una formula cerrada,
    d* = 5 + pi_I/pi_L. Con la Erlang continua no hay tal cosa. Por eso esta
    funcion evalua la identidad EN el optimo numerico: sirve para verificar que
    el optimizador encontro un punto estacionario del problema correcto, no para
    reemplazarlo.

    Devuelve un dict con el medio spread de cada lado, su descomposicion en
    monopolista mas prima, y el residuo de la CPO (que debe ser ~0 en el optimo).
    """
    pi_l = 1.0 - pi_i
    if pi_l <= 0.0:
        raise ValueError(
            "La CPO no esta definida con pi_i = 1: sin traders de liquidez no "
            "hay ingreso que compensar y el problema deja de tener interior."
        )

    resultado = optimizar_cotizaciones(pi_i=pi_i)
    dist = distribucion_valor()

    medio_spread_monopolista = ALPHA / (2 * BETA)

    prima_ask = (pi_i / pi_l) * dist.sf(resultado["ask"]) / (2 * BETA)
    prima_bid = (pi_i / pi_l) * dist.cdf(resultado["bid"]) / (2 * BETA)

    a_optimo = resultado["ask"] - S0
    b_optimo = S0 - resultado["bid"]

    return {
        "pi_i": pi_i,
        "monopolista": medio_spread_monopolista,
        "medio_spread_ask": a_optimo,
        "medio_spread_bid": b_optimo,
        "prima_ask": float(prima_ask),
        "prima_bid": float(prima_bid),
        "teorico_ask": medio_spread_monopolista + float(prima_ask),
        "teorico_bid": medio_spread_monopolista + float(prima_bid),
        "residuo_ask": abs(a_optimo - medio_spread_monopolista - float(prima_ask)),
        "residuo_bid": abs(b_optimo - medio_spread_monopolista - float(prima_bid)),
        "spread_teorico": 2 * medio_spread_monopolista + float(prima_ask) + float(prima_bid),
        "spread_numerico": resultado["spread"],
    }
