"""Simulador de trades de un formador de mercado y analisis de Monte Carlo.

Este modulo simula, trade por trade, el mismo modelo que resuelve
`src.model`: no reimplementa la Erlang ni la probabilidad de ejecucion, las
importa de ahi. Dado un Bid y un Ask fijos, cada trade sortea un tipo de
trader (informado o de liquidez) y un valor verdadero, y contabiliza el P&L
con el mismo criterio que la utilidad esperada Pi(A, B), para que el
promedio simulado se pueda comparar contra el modelo.
"""

import numpy as np
import pandas as pd

from src.model import PI_I, S0, SEED, distribucion_valor, prob_ejecucion


def construir_regimenes(bid_opt, ask_opt):
    """Arma los tres regimenes de cotizacion que pide la simulacion (3.3).

    Devuelve un dict con las llaves fijas 'optimo', 'estrecho' y 'amplio',
    cada una mapeada a una tupla (bid, ask).

    El regimen optimo recibe `bid_opt` y `ask_opt` como argumentos en vez de
    llamar aqui a `optimizar_cotizaciones`: esta funcion no debe decidir que
    hacer si P1 no convergio, ni pagar el costo de optimizar cada vez que se
    arman los regimenes. Esa responsabilidad es de quien la llama (`main.py`
    o el notebook), que ya tiene el resultado de la optimizacion a la mano.

    Estrecho y amplio son los valores fijos del enunciado (19.75/20.05 y
    18.40/21.40), sin redondear.
    """
    return {
        "optimo": (bid_opt, ask_opt),
        "estrecho": (19.75, 20.05),
        "amplio": (18.40, 21.40),
    }


def simular_trades(bid, ask, n_trades=10_000, seed=SEED, forzar_ejecucion=True):
    """Simula `n_trades` trades contra un bid y un ask fijos.

    Cada trade sortea, en este orden y con un unico `rng = default_rng(seed)`:
    tipo de trader (informado con probabilidad PI_I), valor verdadero
    (`distribucion_valor().rvs`) y, si es de liquidez, direccion 50/50. Ese
    orden fijo es lo que hace reproducible la simulacion: la misma semilla
    agota el generador siempre igual y da el mismo DataFrame byte a byte.

    Contabilidad (ver CLAUDE.md, "Contabilidad del P&L", y
    docs/instrucciones/contabilidad_pnl.md):

    - Informado: compra al ask si P > A (pnl = A - P, delta = -1), vende al
      bid si P < B (pnl = P - B, delta = +1). Si B <= P <= A no tiene
      incentivo de ningun lado: convencion del punto abierto O2, fila con
      direccion='ninguna', ejecutado=False, pnl=0.0, delta_inventario=0. Esa
      rama no necesita codigo aparte porque son los valores por defecto con
      los que se inicializan los arrays antes de tocar las mascaras.

    - Liquidez: la direccion se sortea 50/50 (compra/venta), independiente
      del spread, por supuesto explicito del enunciado (flujo no informado y
      simetrico). Con `forzar_ejecucion=True` (el default que pide el
      enunciado) el trade siempre se ejecuta: pnl = A - S0 si compra,
      S0 - B si vende. Con `forzar_ejecucion=False` la ejecucion se sortea
      contra `prob_ejecucion` para poder verificar el simulador contra el
      modelo y mostrar el sesgo del regimen amplio en vez de solo
      mencionarlo.

      El factor 2 en `2.0 * prob_ejecucion(s)`: en `ganancia_liquidez` de
      `src.model`, `prob_ejecucion(s)` ya es la probabilidad CONJUNTA de
      "llega un trader de liquidez de ese lado y ejecuta" (a spread 0 vale
      ALPHA = 0.50, no 1.0). Aqui la direccion ya se sorteo aparte, 50/50, asi
      que la probabilidad de ejecutar CONDICIONAL a esa direccion es el doble:
      2*prob_ejecucion(s). Sin el factor 2, el P&L promedio simulado saldria
      la mitad de `ganancia_liquidez(A, B)` y la prueba de reproducibilidad
      contra `utilidad_esperada` (tolerancia 2%) fallaria por un factor
      sistematico de 2, no por ruido de muestreo.

    Vectorizado con arrays de numpy y mascaras booleanas: nada de `for` por
    trade. `pnl_acumulado` e `inventario` salen de `cumsum` sobre `pnl` y
    `delta_inventario`.
    """
    rng = np.random.default_rng(seed)

    es_informado = rng.random(n_trades) < PI_I
    tipo_trader = np.where(es_informado, "informado", "liquidez")

    valor_verdadero = distribucion_valor().rvs(size=n_trades, random_state=rng)

    compra_liquidez = rng.random(n_trades) < 0.5

    direccion = np.full(n_trades, "ninguna", dtype=object)
    ejecutado = np.zeros(n_trades, dtype=bool)
    precio_ejecucion = np.full(n_trades, np.nan)
    pnl = np.zeros(n_trades)
    delta_inventario = np.zeros(n_trades, dtype=int)

    # --- Informados: compran si P > A, venden si P < B. Dentro de la banda
    # se quedan en los valores por defecto (ninguna, sin ejecutar, pnl 0).
    informado_compra = es_informado & (valor_verdadero > ask)
    informado_vende = es_informado & (valor_verdadero < bid)

    direccion[informado_compra] = "compra"
    ejecutado[informado_compra] = True
    precio_ejecucion[informado_compra] = ask
    pnl[informado_compra] = ask - valor_verdadero[informado_compra]
    delta_inventario[informado_compra] = -1

    direccion[informado_vende] = "venta"
    ejecutado[informado_vende] = True
    precio_ejecucion[informado_vende] = bid
    pnl[informado_vende] = valor_verdadero[informado_vende] - bid
    delta_inventario[informado_vende] = 1

    # --- Liquidez: direccion 50/50, ejecucion forzada o sorteada.
    es_liquidez = ~es_informado
    liquidez_compra = es_liquidez & compra_liquidez
    liquidez_vende = es_liquidez & ~compra_liquidez

    direccion[liquidez_compra] = "compra"
    direccion[liquidez_vende] = "venta"

    if forzar_ejecucion:
        ejecuta_compra = liquidez_compra
        ejecuta_vende = liquidez_vende
    else:
        u = rng.random(n_trades)
        p_ejecuta_compra = 2.0 * prob_ejecucion(ask - S0)
        p_ejecuta_vende = 2.0 * prob_ejecucion(S0 - bid)
        ejecuta_compra = liquidez_compra & (u < p_ejecuta_compra)
        ejecuta_vende = liquidez_vende & (u < p_ejecuta_vende)

    ejecutado[ejecuta_compra] = True
    precio_ejecucion[ejecuta_compra] = ask
    pnl[ejecuta_compra] = ask - S0
    delta_inventario[ejecuta_compra] = -1

    ejecutado[ejecuta_vende] = True
    precio_ejecucion[ejecuta_vende] = bid
    pnl[ejecuta_vende] = S0 - bid
    delta_inventario[ejecuta_vende] = 1

    return pd.DataFrame({
        "trade_id": np.arange(n_trades),
        "tipo_trader": tipo_trader,
        "direccion": direccion,
        "ejecutado": ejecutado,
        "valor_verdadero": valor_verdadero,
        "precio_ejecucion": precio_ejecucion,
        "pnl": pnl,
        "delta_inventario": delta_inventario,
        "pnl_acumulado": np.cumsum(pnl),
        "inventario": np.cumsum(delta_inventario),
    })


def simular_regimenes(regimenes, n_trades=10_000, seed=SEED):
    """Corre `simular_trades` para cada regimen de `construir_regimenes`.

    Devuelve un dict que mapea el nombre del regimen ('optimo', 'estrecho',
    'amplio') a su DataFrame de trades. No duplica nada de la contabilidad:
    solo itera sobre `regimenes` y delega en `simular_trades`, con
    `forzar_ejecucion` en su default (True), que es la version que pide el
    enunciado para esta tabla de 10,000 trades por regimen.

    Decision deliberada: se pasa la MISMA `seed` a los tres regimenes. Eso
    significa que, antes de que el bid y el ask entren en juego, las tres
    corridas sortean exactamente el mismo tipo de trader, el mismo valor
    verdadero y la misma direccion de liquidez para el trade i-esimo de cada
    regimen (numeros aleatorios comunes). Asi la unica fuente de diferencia
    entre 'optimo', 'estrecho' y 'amplio' es donde estan puestas las
    cotizaciones, no que a un regimen le haya tocado por azar una mezcla de
    traders distinta. Sin este control, una diferencia entre regimenes podria
    ser ruido de muestreo en vez de un efecto real del spread.
    """
    return {
        nombre: simular_trades(bid, ask, n_trades=n_trades, seed=seed)
        for nombre, (bid, ask) in regimenes.items()
    }


def monte_carlo(bid, ask, n_corridas=1_000, n_trades=1_000, seed=SEED):
    """Corre `n_corridas` simulaciones independientes y devuelve su P&L final.

    Cada corrida es una llamada a `simular_trades` con `n_trades` trades y su
    propia semilla `seed + i`: derivada de la semilla del proyecto y
    determinista, para que la corrida i-esima sea siempre la misma. No se
    reimplementa la contabilidad aqui, se reutiliza `simular_trades` tal
    cual, que es la version ya verificada contra el modelo.

    Devuelve un array de forma `(n_corridas,)` con el P&L acumulado al final
    de cada corrida (`df['pnl'].sum()`), no los DataFrames completos: para el
    Monte Carlo del enunciado (promedio, desviacion estandar y probabilidad
    de perdida) solo hace falta ese numero final por corrida, y guardar las
    `n_corridas` corridas completas serian varios millones de filas que nadie
    vuelve a leer.

    El `for` sobre corridas no es el loop por trade que las instrucciones
    prohiben: cada iteracion sigue vectorizada por dentro (`simular_trades`
    resuelve sus `n_trades` con arrays de numpy), y el loop mismo es
    necesario porque cada corrida necesita su propia semilla independiente.
    """
    pnl_final = np.empty(n_corridas)

    for i in range(n_corridas):
        df = simular_trades(bid, ask, n_trades=n_trades, seed=seed + i)
        pnl_final[i] = df["pnl"].sum()

    return pnl_final


def monte_carlo_regimenes(regimenes, n_corridas=1_000, n_trades=1_000, seed=SEED):
    """Corre `monte_carlo` para cada regimen de `construir_regimenes`.

    Devuelve un dict que mapea el nombre del regimen a su array de P&L
    finales (forma `(n_corridas,)`), el mismo que produce `monte_carlo`. Es
    el analogo de `simular_regimenes` pero para el Monte Carlo: itera sobre
    `regimenes` y delega, sin tocar la contabilidad.

    Se pasa la misma `seed` base a los tres regimenes, por la misma razon que
    en `simular_regimenes`: como `monte_carlo` deriva la semilla de la
    corrida i-esima como `seed + i`, los tres regimenes comparten, corrida
    por corrida, el mismo tipo de trader, valor verdadero y direccion de
    liquidez en cada uno de los `n_trades` trades. La diferencia entre los
    tres arrays resultantes viene solo de donde estan puestas las
    cotizaciones, no de que un regimen haya tenido, por azar, corridas mas
    favorables que otro.
    """
    return {
        nombre: monte_carlo(bid, ask, n_corridas=n_corridas, n_trades=n_trades, seed=seed)
        for nombre, (bid, ask) in regimenes.items()
    }


def resumen_monte_carlo(resultados):
    """Resume el dict de `monte_carlo_regimenes` en la tabla que pide 3.3.

    `resultados` es un dict {nombre_regimen: array de P&L finales}, tal cual
    lo devuelve `monte_carlo_regimenes`. Por cada regimen calcula, sobre las
    `n_corridas` corridas (no sobre los trades individuales, que responderia
    otra pregunta):

    - `pnl_promedio`: la media de los P&L finales.
    - `pnl_std`: la desviacion estandar de esos mismos P&L finales
      (`ddof=0`, desviacion poblacional de las corridas observadas: no se
      esta estimando la desviacion de una poblacion mas grande a partir de
      una muestra, las 1,000 corridas child son el objeto de interes).
    - `prob_perdida`: la proporcion de corridas con P&L final ESTRICTAMENTE
      negativo (`< 0`, no `<= 0`): una corrida que cierra en exactamente cero
      no es una perdida.

    Devuelve un DataFrame con una fila por regimen y las columnas exactas
    `['regimen', 'pnl_promedio', 'pnl_std', 'prob_perdida']`, en el orden de
    `resultados` (el mismo orden 'optimo', 'estrecho', 'amplio' con el que
    `construir_regimenes` arma el dict, porque los dicts de Python preservan
    orden de insercion).
    """
    filas = [
        {
            "regimen": nombre,
            "pnl_promedio": pnl_final.mean(),
            "pnl_std": pnl_final.std(ddof=0),
            "prob_perdida": (pnl_final < 0).mean(),
        }
        for nombre, pnl_final in resultados.items()
    ]

    return pd.DataFrame(filas)[["regimen", "pnl_promedio", "pnl_std", "prob_perdida"]]
