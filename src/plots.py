"""Figuras del laboratorio: Copeland-Galai, simulacion y sensibilidad.

Este modulo no calcula nada: recibe los DataFrames y arrays que producen
`src.model` y `src.simulation` y los dibuja. La unica excepcion es
`fig_prob_ejecucion`, que evalua `model.prob_ejecucion` sobre un `linspace`
para trazar la curva -- eso es evaluar una funcion ya existente, no
implementar logica nueva.

Cada funcion `fig_*` devuelve un `matplotlib.figure.Figure` y no llama a
`plt.show()` ni a `savefig()`. Guardar a disco es responsabilidad de
`main.py`, a traves de `guardar_figura`.

`COLORES` fija un color por regimen que se usa igual en las figuras 2, 3 y 4:
que el regimen optimo cambie de color entre figuras confunde en la
exposicion.
"""

import pathlib

import numpy as np
import matplotlib.pyplot as plt

from src.model import ALPHA, BETA, prob_ejecucion

COLORES = {
    "optimo": "#1f77b4",
    "estrecho": "#d62728",
    "amplio": "#2ca02c",
}

# Nombres de regimen para leyendas: las llaves de los dicts de src.simulation
# son minusculas sin acento ('optimo'), pero en las figuras se leen mejor
# capitalizadas. Un solo diccionario para las tres figuras que comparan
# regimenes evita que una quede con 'optimo' y otra con 'Óptimo'.
ETIQUETAS_REGIMEN = {
    "optimo": "Óptimo",
    "estrecho": "Estrecho",
    "amplio": "Amplio",
}


def fig_prob_ejecucion():
    """Probabilidad de ejecucion del trader de liquidez contra el medio spread.

    El eje x es el medio spread `s = |cotizacion - S0|`, no el spread total:
    asi esta definida `prob_ejecucion(s)` en el enunciado (pi_LB(s) = pi_LS(s)
    = max(0, ALPHA - BETA*s)), y se aclara en la etiqueta del eje porque
    "spread" a secas es ambiguo entre medio spread y spread total.

    Marca con una linea vertical `s = ALPHA/BETA = 6.25`, el punto donde la
    probabilidad de ejecucion se anula: mas alla de ahi nadie de liquidez
    esta dispuesto a cruzar, sin importar cuanto se ensanche el spread.

    La firma esta congelada sin argumentos (contrato de `src/plots.py`), asi
    que esta funcion no recibe los regimenes concretos (optimo, estrecho,
    amplio) para marcarlos tambien sobre la curva -- el regimen optimo sale
    de una optimizacion (`model.optimizar_cotizaciones`), y llamarla aqui
    violaria la regla de que `plots.py` no calcula nada mas alla de evaluar
    `prob_ejecucion`. Esa comparacion visual entre regimenes y el limite de
    ejecucion se deja para el notebook, superponiendo texto o lineas propias
    sobre esta figura si hace falta.
    """
    s_max = ALPHA / BETA
    s = np.linspace(0.0, s_max * 1.3, 400)
    p = prob_ejecucion(s)

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.plot(s, p, linewidth=2.5, color=COLORES["optimo"], label="Probabilidad de ejecución")
    ax.axvline(s_max, color="black", linestyle="--", linewidth=1.5)
    ax.annotate(
        f"s = {s_max:.2f}\n(ejecución nula)",
        xy=(s_max, 0.0),
        xytext=(s_max - s_max * 0.32, max(p) * 0.25),
        fontsize=11,
        arrowprops={"arrowstyle": "->", "linewidth": 1},
    )

    ax.set_title(
        "Probabilidad de ejecución del trader de liquidez vs. medio spread",
        fontsize=13,
    )
    ax.set_xlabel("Medio spread s = |cotización − S0| (unidades monetarias)", fontsize=11)
    ax.set_ylabel("Probabilidad de ejecución", fontsize=11)
    ax.tick_params(labelsize=11)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=11)

    fig.tight_layout()
    return fig


def fig_pnl_acumulado(simulaciones):
    """P&L acumulado a lo largo de los trades, tres regimenes en los mismos ejes.

    `simulaciones` es el dict {nombre_regimen: DataFrame} que produce
    `src.simulation.simular_regimenes`. Cada curva es `pnl_acumulado` contra
    `trade_id`, ya calculados alla -- aqui solo se grafican las columnas, sin
    tocar la contabilidad.

    El color de cada regimen sale de `COLORES`, el mismo diccionario que usan
    `fig_inventario` y `fig_histograma_montecarlo`: que el optimo sea azul
    aqui y otro color en la figura de inventario rompe la lectura cruzada
    entre figuras durante la exposicion.
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    for nombre, df in simulaciones.items():
        ax.plot(
            df["trade_id"],
            df["pnl_acumulado"],
            color=COLORES[nombre],
            label=ETIQUETAS_REGIMEN.get(nombre, nombre),
            linewidth=2,
        )

    ax.set_title(
        "P&L acumulado del formador de mercado a lo largo de los trades",
        fontsize=13,
    )
    ax.set_xlabel("Número de trade", fontsize=11)
    ax.set_ylabel("P&L acumulado (unidades monetarias)", fontsize=11)
    ax.tick_params(labelsize=11)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=11, title="Régimen")

    fig.tight_layout()
    return fig


def fig_inventario(simulaciones):
    """Inventario acumulado a lo largo de los trades, tres regimenes en los mismos ejes.

    Mismo patron que `fig_pnl_acumulado`: `simulaciones` es el dict
    {nombre_regimen: DataFrame} de `simular_regimenes`, y cada curva es la
    columna `inventario` (ya un `cumsum` de `delta_inventario`) contra
    `trade_id`. Comparten `COLORES` y `ETIQUETAS_REGIMEN` con las otras
    figuras que comparan regimenes.

    Linea horizontal en inventario = 0: el inventario es un desbalance con
    signo (positivo si el formador acumulo compras, negativo si acumulo
    ventas), y el cero es la referencia de "sin posicion", no un valor
    arbitrario del rango. Sin esa linea no se distingue de un vistazo si una
    curva esta mayormente larga o mayormente corta.
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    for nombre, df in simulaciones.items():
        ax.plot(
            df["trade_id"],
            df["inventario"],
            color=COLORES[nombre],
            label=ETIQUETAS_REGIMEN.get(nombre, nombre),
            linewidth=2,
        )

    ax.axhline(0.0, color="black", linewidth=1.2, linestyle="-")

    ax.set_title(
        "Inventario acumulado del formador de mercado a lo largo de los trades",
        fontsize=13,
    )
    ax.set_xlabel("Número de trade", fontsize=11)
    ax.set_ylabel("Inventario (unidades del activo)", fontsize=11)
    ax.tick_params(labelsize=11)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=11, title="Régimen")

    fig.tight_layout()
    return fig


def fig_histograma_montecarlo(resultados_mc):
    """Distribucion del P&L final por corrida, tres regimenes superpuestos.

    `resultados_mc` es el dict {nombre_regimen: array de P&L finales} que
    produce `src.simulation.monte_carlo_regimenes`. No se recalcula nada del
    Monte Carlo aqui, solo se histograma cada array.

    Los bordes de bin se calculan UNA sola vez sobre el rango conjunto de los
    tres arrays (`np.histogram_bin_edges` sobre la concatenacion) y se
    reusan para los tres histogramas. Si cada regimen calculara sus propios
    bordes, las barras de distintas series no compartirian ancho ni
    alineacion, y comparar alturas entre series dejaria de tener sentido: la
    figura estaria comparando peras con manzanas sin decirlo.

    `alpha=0.6` para que las tres distribuciones sean visibles donde se
    superponen, y una linea vertical en el P&L final = 0: la probabilidad de
    perdida que reporta `resumen_monte_carlo` es exactamente la masa de cada
    histograma a la izquierda de esa linea, asi que la figura responde sola
    la pregunta de que tan mal le puede ir a cada regimen.
    """
    todos_los_pnl = np.concatenate(list(resultados_mc.values()))
    bordes = np.histogram_bin_edges(todos_los_pnl, bins=40)

    fig, ax = plt.subplots(figsize=(10, 6))

    for nombre, pnl_final in resultados_mc.items():
        ax.hist(
            pnl_final,
            bins=bordes,
            alpha=0.6,
            color=COLORES[nombre],
            label=ETIQUETAS_REGIMEN.get(nombre, nombre),
        )

    ax.axvline(0.0, color="black", linewidth=1.5, linestyle="--")

    ax.set_title(
        "Distribución del P&L final por corrida — análisis de Monte Carlo",
        fontsize=13,
    )
    ax.set_xlabel("P&L final de la corrida (unidades monetarias)", fontsize=11)
    ax.set_ylabel("Frecuencia (número de corridas)", fontsize=11)
    ax.tick_params(labelsize=11)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=11, title="Régimen")

    fig.tight_layout()
    return fig


def fig_sensibilidad(df_sensibilidad, df_teorico=None):
    """Spread optimo contra pi_i, contra la curva teorica de la CPO.

    `df_sensibilidad` es el DataFrame de `src.model.analisis_sensibilidad`, con
    columnas `['pi_i', 'bid', 'ask', 'spread', 'utilidad_esperada',
    'convergio']`. Aqui solo se grafica `spread` contra `pi_i`, ya calculados
    alla.

    `df_teorico` es opcional y es lo que produce
    `src.model.curva_teorica_spread`: columnas `['pi_i', 'medio_spread_ask',
    'medio_spread_bid', 'spread']`. Si se pasa, se traza como curva continua
    debajo de los puntos numericos. El argumento tiene default `None` para no
    romper a quien llame `fig_sensibilidad(df)` con un solo argumento, que es
    como estaba congelada la firma original.

    Por que ahora si se traza la curva teorica, cuando antes no. La version
    anterior de esta figura no la dibujaba porque la prediccion teorica de la
    Sesion 04 era un punto abierto y la regla del proyecto es no inventar una
    formula para tener algo que graficar. Ese punto ya esta cerrado: la
    prediccion es la condicion de primer orden del propio modelo,

        pi_L*(ALPHA - 2*BETA*a) + pi_I*(1 - F(A)) = 0

    y `curva_teorica_spread` la resuelve con `brentq`, sin llamar al
    optimizador. Que los tres puntos de `minimize` caigan sobre esa curva es la
    comparacion que pide el enunciado (3.5), y vale porque son dos metodos
    numericos independientes que no comparten fuente de error.

    La linea horizontal en `ALPHA/BETA = 6.25` es el spread del monopolista,
    o sea el optimo cuando pi_i = 0. No depende de la informacion asimetrica
    en absoluto. El area sombreada entre esa linea y la curva teorica es la
    prima de seleccion adversa: la parte del spread que existe unicamente
    porque hay traders informados. Esa separacion es el punto que la figura
    sostiene, y es lo que no se ve en una grafica de spread contra pi_i a secas.

    Los puntos numericos se dibujan con marcadores y SIN linea que los una:
    antes se conectaban con una linea punteada como guia visual, pero ahora la
    curva teorica ocupa ese lugar y hace el trabajo mejor, porque si es una
    afirmacion de forma funcional y esta justificada.

    Los casos con `convergio=False` se marcan aparte con una 'x' negra en vez
    de dejarlos mezclados con los puntos validos: un optimo que no convergio no
    es un dato mas, es un caso degenerado que hay que poder distinguir a simple
    vista (CLAUDE.md, regla 10 -- los NaN y los casos degenerados se reportan,
    no se maquillan).
    """
    convergio = df_sensibilidad["convergio"].astype(bool)
    spread_monopolista = ALPHA / BETA

    fig, ax = plt.subplots(figsize=(10, 6))

    if df_teorico is not None:
        ax.fill_between(
            df_teorico["pi_i"],
            spread_monopolista,
            df_teorico["spread"],
            color=COLORES["optimo"],
            alpha=0.12,
            label="Prima de selección adversa",
        )
        ax.plot(
            df_teorico["pi_i"],
            df_teorico["spread"],
            linestyle="-",
            linewidth=2,
            color=COLORES["optimo"],
            label="Predicción teórica (CPO, resuelta con brentq)",
            zorder=2,
        )

    ax.axhline(
        spread_monopolista,
        color="black",
        linestyle="--",
        linewidth=1.5,
        label=f"Spread del monopolista, sin informados = {spread_monopolista:.2f}",
    )

    ax.plot(
        df_sensibilidad.loc[convergio, "pi_i"],
        df_sensibilidad.loc[convergio, "spread"],
        marker="o",
        markersize=11,
        linestyle="none",
        markerfacecolor="white",
        markeredgecolor=COLORES["estrecho"],
        markeredgewidth=2.5,
        label="Óptimo numérico (scipy.optimize.minimize)",
        zorder=3,
    )

    if (~convergio).any():
        ax.scatter(
            df_sensibilidad.loc[~convergio, "pi_i"],
            df_sensibilidad.loc[~convergio, "spread"],
            marker="x",
            s=150,
            linewidths=2.5,
            color="black",
            label="No convergió",
            zorder=4,
        )

    ax.set_title(
        "Spread óptimo contra la proporción de traders informados",
        fontsize=13,
    )
    ax.set_xlabel("Probabilidad de trader informado, pi_i", fontsize=11)
    ax.set_ylabel("Spread óptimo, ask − bid (unidades monetarias)", fontsize=11)
    ax.tick_params(labelsize=11)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=10, loc="upper left")

    fig.tight_layout()
    return fig


def guardar_figura(fig, nombre):
    """Guarda `fig` como PNG en `docs/figuras/{nombre}.png` y devuelve la ruta.

    Es la unica funcion de este modulo que escribe a disco -- las `fig_*`
    solo devuelven el `Figure` para que el notebook lo muestre inline sin
    tocar el sistema de archivos, y `main.py` llama a `guardar_figura` para
    cada una sin repetir la logica de ruta y `savefig` cinco veces.

    150 dpi y PNG: la resolucion propuesta en el punto abierto O5 del
    CLAUDE.md, suficiente para proyectar en el salon sin generar archivos
    pesados. `bbox_inches='tight'` recorta el margen sobrante para que la
    figura completa (incluyendo anotaciones fuera de los ejes, como en
    `fig_prob_ejecucion`) quede dentro del PNG.

    Crea `docs/figuras/` si no existe (`mkdir(parents=True, exist_ok=True)`),
    de forma idempotente: no falla si `main.py` ya la creo antes, y tampoco
    depende de que lo haya hecho, asi que esta funcion se puede llamar sola
    para pruebas sin correr el pipeline completo primero.
    """
    directorio = pathlib.Path("docs/figuras")
    directorio.mkdir(parents=True, exist_ok=True)

    ruta = directorio / f"{nombre}.png"
    fig.savefig(ruta, dpi=150, bbox_inches="tight")

    return ruta
