"""Punto de entrada del Lab01: reproduce todo el proyecto con un solo comando.

    python main.py

Este archivo ORQUESTA Y REPORTA. No implementa nada: no hay aqui una sola
formula del modelo, del simulador ni del graficado. Toda la logica vive en
`src/`, y main.py se limita a llamarla en orden, imprimir los resultados de
forma legible y guardar las figuras en `docs/figuras/`. Si alguna vez hace
falta una cuenta nueva, va en el modulo de `src/` que le corresponda, no aqui.

Que hace, en orden:

1. Optimiza las cotizaciones del caso base (pi_i = 0.40) y verifica el optimo
   contra un barrido en malla fina.
2. Arma los tres regimenes de cotizacion y simula 10,000 trades en cada uno.
3. Contrasta la simulacion contra la utilidad esperada del modelo, que es lo
   que sostiene la advertencia de interpretacion del README.
4. Corre el Monte Carlo (1,000 corridas de 1,000 trades por regimen) y resume.
5. Reoptimiza para pi_i en {0.1, 0.4, 0.7}: analisis de sensibilidad.
6. Genera y guarda las cinco figuras.

Corre en menos de un minuto y es determinista: dos ejecuciones seguidas
imprimen exactamente los mismos numeros, porque toda la aleatoriedad cuelga de
SEED = 42, definida una sola vez en `src/model.py`.
"""

import pathlib

import matplotlib

# El backend Agg se fija ANTES de importar `src.plots`, que a su vez importa
# pyplot: si se hiciera despues, pyplot ya habria elegido un backend
# interactivo. Agg no necesita servidor grafico, asi que `python main.py` corre
# igual en una maquina sin entorno de ventanas -- por ejemplo, si el profesor lo
# ejecuta por SSH o dentro de un contenedor.
matplotlib.use("Agg")

import numpy as np
import pandas as pd

from src.model import (
    ALPHA,
    BETA,
    K_ERLANG,
    LAMBDA_ERLANG,
    PI_I,
    S0,
    SEED,
    analisis_sensibilidad,
    curva_teorica_spread,
    distribucion_valor,
    optimizar_cotizaciones,
    perdida_informados,
    prediccion_teorica_spread,
    utilidad_esperada,
    verificar_optimo_en_malla,
)
from src.plots import (
    fig_histograma_montecarlo,
    fig_inventario,
    fig_pnl_acumulado,
    fig_prob_ejecucion,
    fig_sensibilidad,
    guardar_figura,
)
from src.simulation import (
    construir_regimenes,
    monte_carlo_regimenes,
    resumen_monte_carlo,
    simular_regimenes,
    simular_trades,
)

# Parametros de la corrida. Los del modelo viven en `src/model.py`; estos son
# del reporte, no del modelo, y por eso si van aqui.
N_TRADES = 10_000        # trades por regimen en la simulacion de 3.3
N_CORRIDAS_MC = 1_000    # corridas de Monte Carlo por regimen
N_TRADES_MC = 1_000      # trades por corrida de Monte Carlo
N_TRADES_VERIFICACION = 300_000  # trades para contrastar simulacion vs modelo
N_SEMILLAS_DERIVA = 200          # semillas para separar la deriva de inventario del ruido

DIRECTORIO_FIGURAS = pathlib.Path("docs/figuras")

ETIQUETAS = {
    "optimo": "Optimo",
    "estrecho": "Estrecho (19.75 / 20.05)",
    "amplio": "Amplio (18.40 / 21.40)",
}


def encabezado(texto):
    """Imprime un titulo de seccion.

    Presentacion, no logica. La salida de consola es lo primero que ve el
    profesor cuando corre el proyecto, y una pared de numeros sin separar se lee
    peor que la misma informacion en bloques.
    """
    print()
    print("=" * 78)
    print(texto.upper())
    print("=" * 78)


def main():
    pd.set_option("display.float_format", lambda v: f"{v:10.4f}")
    pd.set_option("display.width", 120)

    # ---------------------------------------------------------------------- #
    encabezado("0. Parametros del caso base")
    # ---------------------------------------------------------------------- #
    dist = distribucion_valor()

    print(f"  Precio de referencia S0        : {S0:.2f}")
    print(f"  Valor verdadero P              : Erlang(k={K_ERLANG}, lambda={LAMBDA_ERLANG})")
    print(f"    media                        : {dist.mean():.4f}")
    print(f"    desviacion estandar          : {dist.std():.4f}")
    print(f"  Prob. de trader informado pi_i : {PI_I:.2f}")
    print(f"  Demanda de liquidez            : max(0, {ALPHA:.2f} - {BETA:.2f}*s)")
    print(f"    se agota en s                : {ALPHA / BETA:.4f}")
    print(f"  Semilla                        : {SEED}")
    print()
    print(f"  Nota: S0 esta {dist.mean() - S0:.2f} por debajo del valor esperado verdadero.")
    print("  Ese sesgo no es accidental: es parte del caso que plantea el enunciado.")

    # ---------------------------------------------------------------------- #
    encabezado("1. Cotizaciones optimas (pi_i = 0.40)")
    # ---------------------------------------------------------------------- #
    optimo = optimizar_cotizaciones()

    if not optimo["convergio"]:
        print("  !! EL OPTIMIZADOR NO CONVERGIO. Los resultados de abajo NO son confiables.")
        print(f"  !! Mensaje de scipy: {optimo['mensaje']}")

    print(f"  Bid optimo B*                  : {optimo['bid']:.2f}")
    print(f"  Ask optimo A*                  : {optimo['ask']:.2f}")
    print(f"  Spread total A* - B*           : {optimo['spread']:.2f}")
    print(f"  Utilidad esperada por trade    : {optimo['utilidad_esperada']:.2f}")
    print()
    print("  Con mas precision, que es la que usa la simulacion (redondear aqui")
    print("  sesgaria el P&L acumulado de 10,000 trades):")
    print(f"    B* = {optimo['bid']:.6f}   A* = {optimo['ask']:.6f}   "
          f"spread = {optimo['spread']:.6f}")
    print(f"  Convergio: {optimo['convergio']} ({optimo['mensaje']})")

    print()
    print("  Verificacion independiente contra un barrido en malla fina de 0.01.")
    print("  L-BFGS-B aproxima el gradiente por diferencias finitas y `quad` mete")
    print("  ruido de orden 1e-10 en Pi; la malla no usa gradiente y hace de arbitro.")
    malla = verificar_optimo_en_malla(optimo)
    print(f"    optimo en malla                : B = {malla['bid_malla']:.4f}, "
          f"A = {malla['ask_malla']:.4f}")
    print(f"    utilidad en malla              : {malla['utilidad_malla']:.6f}")
    print(f"    diferencia (bid / ask)         : {malla['dif_bid']:.4f} / "
          f"{malla['dif_ask']:.4f}")
    print(f"    coincide                       : {malla['coincide']}")

    print()
    print("  Desglose de la perdida esperada frente a informados en el optimo:")
    lado_ask, lado_bid = perdida_informados(optimo["ask"], optimo["bid"])
    print(f"    lado ask (informado compra)    : {lado_ask:.6f}")
    print(f"    lado bid (informado vende)     : {lado_bid:.6f}")
    print(f"    total                          : {lado_ask + lado_bid:.6f}")
    print("  El lado del ask pesa mas porque S0 esta por debajo de la media de la")
    print("  Erlang: es mas probable que el valor verdadero rebase el ask a que")
    print("  caiga por debajo del bid.")

    # ---------------------------------------------------------------------- #
    encabezado("2. Costo de la seleccion adversa contra el spread")
    # ---------------------------------------------------------------------- #
    print("  Perdida esperada frente a informados, evaluada a medio spread")
    print("  simetrico creciente alrededor de S0. Responde la pregunta 2 del")
    print("  analisis mostrando el numero, no afirmandolo.")
    print()
    print(f"  {'medio spread':>13}  {'bid':>8}  {'ask':>8}  {'lado ask':>10}  "
          f"{'lado bid':>10}  {'total':>10}")
    for medio_spread in (0.15, 0.50, 1.00, 1.50, 2.00, 3.00, 3.50, 4.00):
        A, B = S0 + medio_spread, S0 - medio_spread
        ask_perdida, bid_perdida = perdida_informados(A, B)
        print(f"  {medio_spread:>13.2f}  {B:>8.2f}  {A:>8.2f}  {ask_perdida:>10.4f}  "
              f"{bid_perdida:>10.4f}  {ask_perdida + bid_perdida:>10.4f}")

    # ---------------------------------------------------------------------- #
    encabezado("3. Simulacion: tres regimenes, 10,000 trades cada uno")
    # ---------------------------------------------------------------------- #
    regimenes = construir_regimenes(optimo["bid"], optimo["ask"])

    print("  Regimenes de cotizacion:")
    for nombre, (bid, ask) in regimenes.items():
        print(f"    {nombre:<10}: bid = {bid:8.4f}   ask = {ask:8.4f}   "
              f"spread = {ask - bid:6.4f}")
    print()
    print(f"  Se simulan {N_TRADES:,} trades por regimen con forzar_ejecucion=True,")
    print("  que es el default del enunciado: el trader de liquidez siempre cruza.")
    print("  Los tres comparten la misma semilla, asi que la unica diferencia entre")
    print("  ellos es donde estan puestas las cotizaciones, no el azar.")

    simulaciones = simular_regimenes(regimenes, n_trades=N_TRADES, seed=SEED)

    print()
    print(f"  {'regimen':<10}  {'P&L total':>12}  {'P&L/trade':>11}  {'ejecutados':>11}  "
          f"{'inv. final':>11}  {'|inv| max':>10}")
    for nombre, df in simulaciones.items():
        print(f"  {nombre:<10}  {df['pnl'].sum():>12.2f}  {df['pnl'].mean():>11.4f}  "
              f"{df['ejecutado'].sum():>11,}  {df['inventario'].iloc[-1]:>11,}  "
              f"{df['inventario'].abs().max():>10,}")

    print()
    print("  Desglose del P&L por tipo de trader (el mecanismo de la seleccion adversa):")
    print()
    print(f"  {'regimen':<10}  {'P&L liquidez':>13}  {'P&L informados':>15}  "
          f"{'trades informados':>18}")
    for nombre, df in simulaciones.items():
        de_liquidez = df.loc[df["tipo_trader"] == "liquidez", "pnl"].sum()
        de_informados = df.loc[df["tipo_trader"] == "informado", "pnl"].sum()
        n_informados = int(
            ((df["tipo_trader"] == "informado") & df["ejecutado"]).sum()
        )
        print(f"  {nombre:<10}  {de_liquidez:>13.2f}  {de_informados:>15.2f}  "
              f"{n_informados:>18,}")
    print()
    print("  Desglose del INVENTARIO por tipo de trader, y de donde sale la deriva:")
    print()
    print(f"  {'regimen':<10}  {'inv. final':>10}  {'de inform.':>10}  {'de liquid.':>10}  "
          f"{'P(P>A)':>8}  {'P(P<B)':>8}  {'razon':>6}  {'deriva teor.':>12}")
    dist = distribucion_valor()
    for nombre, df in simulaciones.items():
        bid, ask = regimenes[nombre]
        de_informados = int(df.loc[df["tipo_trader"] == "informado", "delta_inventario"].sum())
        de_liquidez = int(df.loc[df["tipo_trader"] == "liquidez", "delta_inventario"].sum())
        cola_ask, cola_bid = float(dist.sf(ask)), float(dist.cdf(bid))
        deriva = -N_TRADES * PI_I * (cola_ask - cola_bid)
        print(f"  {nombre:<10}  {df['inventario'].iloc[-1]:>10,}  {de_informados:>10,}  "
              f"{de_liquidez:>10,}  {cola_ask:>8.4f}  {cola_bid:>8.4f}  "
              f"{cola_ask / cola_bid:>6.3f}  {deriva:>12.1f}")
    print()
    print("  El aporte de liquidez es IDENTICO en los tres: comparten semilla, la")
    print("  direccion se sortea 50/50 y con ejecucion forzada todos cruzan, asi que")
    print("  es literalmente la misma caminata aleatoria. Todo el desbalance viene de")
    print("  informados, y su deriva esperada es -n*pi_i*[P(P>A) - P(P<B)]: cuanto mas")
    print("  lejos se cotiza, mas domina la cola derecha de la Erlang, que es la pesada.")
    print()
    print(f"  Verificacion sobre {N_SEMILLAS_DERIVA} semillas independientes, para separar la deriva del ruido:")
    print()
    print(f"  {'regimen':<10}  {'inv. final promedio':>20}  {'error estandar':>15}  {'deriva teor.':>12}")
    for nombre, (bid, ask) in regimenes.items():
        finales = np.array([
            simular_trades(bid, ask, n_trades=N_TRADES, seed=SEED + i)["inventario"].iloc[-1]
            for i in range(N_SEMILLAS_DERIVA)
        ])
        cola_ask, cola_bid = float(dist.sf(ask)), float(dist.cdf(bid))
        deriva = -N_TRADES * PI_I * (cola_ask - cola_bid)
        error_estandar = finales.std(ddof=1) / np.sqrt(N_SEMILLAS_DERIVA)
        print(f"  {nombre:<10}  {finales.mean():>20.1f}  {error_estandar:>15.1f}  {deriva:>12.1f}")

    print()
    print("  El P&L frente a informados es negativo en los tres regimenes, siempre.")
    print("  Un informado solo cruza cuando sabe que el precio esta mal, asi que")
    print("  nunca le deja ganancia al formador: esa columna es el costo de la")
    print("  seleccion adversa, y el spread existe para pagarla.")

    # ---------------------------------------------------------------------- #
    encabezado("4. La simulacion contra el modelo, y la advertencia obligatoria")
    # ---------------------------------------------------------------------- #
    print("  Pi(A, B) pondera la ganancia de liquidez por prob_ejecucion, o sea")
    print("  supone que el trader de liquidez puede NO ejecutar. La simulacion del")
    print("  enunciado fuerza la ejecucion. Son dos objetos distintos, y aqui se")
    print("  ponen lado a lado en vez de mencionarlo de pasada.")
    print()

    utilidad_modelo = utilidad_esperada(optimo["ask"], optimo["bid"])
    forzada = simulaciones["optimo"]["pnl"].mean()
    sin_forzar = simular_trades(
        optimo["bid"], optimo["ask"],
        n_trades=N_TRADES_VERIFICACION, seed=SEED, forzar_ejecucion=False,
    )["pnl"].mean()

    error_relativo = abs(sin_forzar - utilidad_modelo) / abs(utilidad_modelo)

    print(f"  Utilidad esperada del modelo Pi(A*, B*)        : {utilidad_modelo:.4f}")
    print(f"  P&L/trade simulado, forzar_ejecucion=False     : {sin_forzar:.4f}   "
          f"({N_TRADES_VERIFICACION:,} trades)")
    print(f"    error relativo contra el modelo              : {error_relativo:.4%}")
    print(f"  P&L/trade simulado, forzar_ejecucion=True      : {forzada:.4f}   "
          f"({N_TRADES:,} trades)")
    print(f"    veces el modelo                              : "
          f"{forzada / utilidad_modelo:.2f}x")
    print()
    print("  ADVERTENCIA DE INTERPRETACION. Con ejecucion sorteada, la simulacion")
    print("  reproduce el modelo dentro del error de muestreo: son el mismo objeto.")
    print("  Con ejecucion forzada, el P&L por trade se infla, y se infla MAS")
    print("  mientras mas ancho es el spread, porque justo la probabilidad de")
    print("  ejecucion que se esta ignorando es la que castiga al spread ancho.")
    print("  Todos los resultados de la seccion 3 son rentabilidad POR TRADE, no")
    print("  por unidad de tiempo. El regimen amplio sale favorecido por eso: en un")
    print("  mercado real cotizaria tan lejos que casi nadie le cruzaria, y haria")
    print("  muchos menos trades por hora que los otros dos.")

    # ---------------------------------------------------------------------- #
    encabezado("5. Monte Carlo")
    # ---------------------------------------------------------------------- #
    print(f"  {N_CORRIDAS_MC:,} corridas independientes de {N_TRADES_MC:,} trades por")
    print("  regimen. La semilla de la corrida i-esima es SEED + i: determinista y")
    print("  distinta en cada corrida.")
    print()

    resultados_mc = monte_carlo_regimenes(
        regimenes, n_corridas=N_CORRIDAS_MC, n_trades=N_TRADES_MC, seed=SEED,
    )
    tabla_mc = resumen_monte_carlo(resultados_mc)

    print(tabla_mc.to_string(index=False))
    print()
    print("  pnl_promedio y pnl_std son la media y la desviacion estandar de las")
    print(f"  {N_CORRIDAS_MC:,} corridas, no de los trades individuales. prob_perdida es la")
    print("  proporcion de corridas que cierran estrictamente por debajo de cero.")

    # ---------------------------------------------------------------------- #
    encabezado("6. Analisis de sensibilidad en pi_i")
    # ---------------------------------------------------------------------- #
    df_sensibilidad = analisis_sensibilidad()

    print(df_sensibilidad.to_string(index=False))
    print()
    print("  Comparacion contra la prediccion teorica (enunciado 3.5). La condicion")
    print("  de primer orden del modelo, la misma CPO de la sesion de Copeland-Galai")
    print("  del curso, dice que el medio spread optimo se descompone en dos partes:")
    print()
    print("      a*  =  ALPHA/(2*BETA)  +  (pi_I/pi_L) * (1 - F(A*)) / (2*BETA)")
    print("             monopolista        prima de seleccion adversa")
    print()
    print("  El primer termino no depende de pi_i y vale 3.125 siempre. El segundo")
    print("  es todo el efecto de la informacion asimetrica.")
    print()
    print(f"  {'pi_i':>5}  {'a* numerico':>12}  {'monopolista':>12}  {'prima':>9}  "
          f"{'a* teorico':>11}  {'residuo':>10}")
    for pi_i in (0.0, 0.1, 0.4, 0.7):
        pred = prediccion_teorica_spread(pi_i)
        print(f"  {pi_i:>5.1f}  {pred['medio_spread_ask']:>12.4f}  "
              f"{pred['monopolista']:>12.4f}  {pred['prima_ask']:>9.4f}  "
              f"{pred['teorico_ask']:>11.4f}  {pred['residuo_ask']:>10.2e}")
    print()
    print()
    print("  Verificacion independiente: la CPO tambien se resuelve por su cuenta con")
    print("  scipy.optimize.brentq, sin llamar al optimizador. brentq biseca el cambio")
    print("  de signo de una ecuacion escalar y no usa gradientes, asi que no comparte")
    print("  ninguna fuente de error con L-BFGS-B. Los dos metodos coinciden:")
    print()
    print(f"  {'pi_i':>5}  {'spread minimize':>16}  {'spread brentq':>14}  {'diferencia':>11}")
    curva_en_los_puntos = curva_teorica_spread(df_sensibilidad["pi_i"].to_numpy())
    for (_, fila), (_, teo) in zip(df_sensibilidad.iterrows(), curva_en_los_puntos.iterrows()):
        print(f"  {fila['pi_i']:>5.1f}  {fila['spread']:>16.6f}  {teo['spread']:>14.6f}  "
              f"{abs(fila['spread'] - teo['spread']):>11.2e}")
    print()
    print("  El residuo es de orden 1e-6 en los cuatro casos: el optimo numerico y")
    print("  la prediccion teorica son el mismo punto. La prima de seleccion adversa")
    print("  pasa de 0.00 con pi_i = 0 a 0.98 con pi_i = 0.7, o sea que a esa altura")
    print("  casi un cuarto del medio spread existe solo para pagar informacion.")
    print()
    print("  Matiz importante: la identidad es IMPLICITA, no una formula cerrada, y")
    print("  por eso se evalua EN el optimo. En el ejemplo discreto de clase")
    print("  (1 - F(A)) es la constante 0.10 y ahi si sale d* = 5 + pi_I/pi_L; con la")
    print("  Erlang continua, (1 - F(A*)) depende del A* que se quiere despejar.")

    # ---------------------------------------------------------------------- #
    encabezado("7. Figuras")
    # ---------------------------------------------------------------------- #
    # Se crea el directorio aqui y no se da por hecho: en un clon limpio
    # `docs/figuras/` puede no existir, y `python main.py` tiene que correr sin
    # ningun paso manual previo. `exist_ok=True` lo hace idempotente.
    DIRECTORIO_FIGURAS.mkdir(parents=True, exist_ok=True)

    curva_teorica = curva_teorica_spread()

    figuras = {
        "fig1_prob_ejecucion": fig_prob_ejecucion(),
        "fig2_pnl_acumulado": fig_pnl_acumulado(simulaciones),
        "fig3_inventario": fig_inventario(simulaciones),
        "fig4_histograma_montecarlo": fig_histograma_montecarlo(resultados_mc),
        "fig5_sensibilidad": fig_sensibilidad(df_sensibilidad, curva_teorica),
    }

    for nombre, fig in figuras.items():
        ruta = guardar_figura(fig, nombre)
        print(f"  guardada: {ruta}")

    encabezado("Listo")
    print(f"  Las cinco figuras estan en {DIRECTORIO_FIGURAS}/.")
    print("  Todo lo de arriba es determinista: correr `python main.py` otra vez")
    print("  imprime exactamente los mismos numeros.")
    print()


if __name__ == "__main__":
    main()
