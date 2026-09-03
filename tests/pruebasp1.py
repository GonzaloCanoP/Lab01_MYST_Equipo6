"""Script de verificacion manual de la Parte 1 — SOLO src/model.py.

NO ES PARTE DEL ENTREGABLE. Es un script suelto para correr a mano, ver los
numeros y detectar cualquier cosa rara antes de abrir el Pull Request de P1.
No se commitea: el enunciado no acepta archivos sueltos en la raiz fuera de los
que lista la estructura, asi que este archivo se queda sin versionar y se borra
cuando ya no haga falta.

Las pruebas formales con pytest son de P4 y van despues, cuando existan
src/simulation.py y src/plots.py.

Uso, desde la raiz del repositorio:

    python tests/pruebasp1.py
"""

import pathlib
import sys
import warnings

# Al correr `python tests/pruebasp1.py`, Python pone tests/ al frente de
# sys.path, no la raiz del proyecto, y `from src.model import ...` fallaria.
# Se agrega la raiz a mano para que el script corra parado donde sea.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import numpy as np
from scipy import integrate

from src.model import (
    ALPHA,
    BETA,
    K_ERLANG,
    LAMBDA_ERLANG,
    PI_I,
    PI_L,
    S0,
    SEED,
    TOL_QUAD,
    analisis_sensibilidad,
    distribucion_valor,
    ganancia_liquidez,
    objetivo,
    optimizar_cotizaciones,
    perdida_informados,
    prob_ejecucion,
    utilidad_esperada,
    verificar_optimo_en_malla,
)

_fallas = []


def titulo(texto):
    print(f"\n{'=' * 72}\n  {texto}\n{'=' * 72}")


def revisar(condicion, descripcion, detalle=""):
    """Imprime el resultado de una comprobacion y lleva la cuenta de las fallas."""
    marca = "[ OK ]" if condicion else "[FALLA]"
    print(f"  {marca}  {descripcion}")
    if detalle:
        print(f"          {detalle}")
    if not condicion:
        _fallas.append(descripcion)


def dato(etiqueta, valor):
    print(f"    {etiqueta:.<46} {valor}")


# --------------------------------------------------------------------------- #
titulo("1. PARAMETROS DEL CASO BASE")
# --------------------------------------------------------------------------- #

dato("Precio de referencia S0", S0)
dato("Forma de la Erlang K", K_ERLANG)
dato("Tasa de la Erlang lambda", LAMBDA_ERLANG)
dato("Prob. de trader informado PI_I", PI_I)
dato("Prob. de trader de liquidez PI_L", PI_L)
dato("Intercepto de la demanda ALPHA", ALPHA)
dato("Pendiente de la demanda BETA", BETA)
dato("Semilla SEED", SEED)

revisar(
    (S0, K_ERLANG, LAMBDA_ERLANG, PI_I, PI_L, ALPHA, BETA, SEED)
    == (19.90, 60, 3, 0.40, 0.60, 0.50, 0.08, 42),
    "Los ocho parametros son los del enunciado",
)
revisar(PI_L == 1 - PI_I, "PI_L = 1 - PI_I")


# --------------------------------------------------------------------------- #
titulo("2. DISTRIBUCION DEL VALOR VERDADERO  P ~ Erlang(60, lambda=3)")
# --------------------------------------------------------------------------- #

dist = distribucion_valor()
media, desv = dist.mean(), dist.std()

dato("Media obtenida", f"{media:.10f}")
dato("Media teorica K/lambda", f"{K_ERLANG / LAMBDA_ERLANG:.10f}")
dato("Desviacion obtenida", f"{desv:.10f}")
dato("Desviacion teorica sqrt(K)/lambda", f"{np.sqrt(K_ERLANG) / LAMBDA_ERLANG:.10f}")
dato("Sesgo del precio de referencia  E[P] - S0", f"{media - S0:.10f}")
dato("Percentiles 1% / 50% / 99%", f"{dist.ppf(0.01):.4f} / {dist.ppf(0.5):.4f} / {dist.ppf(0.99):.4f}")

revisar(
    abs(media - 20.0) < 1e-9,
    "La media es 20.0 (blindaje contra scale=3 en vez de scale=1/3)",
    f"con scale=3 esta media saldria 180.0 y scipy NO lanzaria ningun error",
)
revisar(abs(desv - 2.581988897471611) < 1e-9, "La desviacion es 2.582")
revisar(
    abs((media - S0) - 0.10) < 1e-9,
    "S0 esta 0.10 por debajo de E[P], y el sesgo es intencional",
    "por eso el ask termina abriendose mas que el bid: al informado le conviene",
    )
revisar(
    np.array_equal(dist.pdf(np.linspace(5, 40, 50)),
                   distribucion_valor().pdf(np.linspace(5, 40, 50))),
    "Dos llamadas a distribucion_valor() dan la misma distribucion",
    "P2 samplea el valor verdadero con esta misma funcion",
)


# --------------------------------------------------------------------------- #
titulo("3. PROBABILIDAD DE EJECUCION   pi_LB(s) = pi_LS(s) = max(0, 0.50 - 0.08*s)")
# --------------------------------------------------------------------------- #

s_corte = ALPHA / BETA
print(f"\n    Punto de corte de la demanda: ALPHA/BETA = {s_corte}\n")
print(f"    {'medio spread s':>16} | {'prob. ejecucion':>16}")
print(f"    {'-' * 16}-+-{'-' * 16}")
for s in [0.0, 1.5, 3.0, 3.125, 6.24, 6.25, 6.26, 10.0, 20.0]:
    print(f"    {s:>16.3f} | {float(prob_ejecucion(s)):>16.6f}")

barrido = prob_ejecucion(np.linspace(0, 20, 2001))

revisar(np.all(barrido >= 0.0), "Nunca devuelve un valor negativo en [0, 20]",
        "sin el truncamiento, el optimizador 'ganaria' ensanchando al infinito")
revisar(
    np.allclose(prob_ejecucion(np.array([0.0, 3.0, 6.25, 10.0])),
                [0.50, 0.26, 0.0, 0.0], atol=1e-12),
    "prob_ejecucion([0, 3, 6.25, 10]) = [0.5, 0.26, 0.0, 0.0]",
)
revisar(float(prob_ejecucion(6.25)) == 0.0, "prob_ejecucion(6.25) es exactamente 0.0")
revisar(float(prob_ejecucion(6.24)) > 0.0,
        "prob_ejecucion(6.24) es positiva", f"vale {float(prob_ejecucion(6.24)):.6f}")
revisar(
    isinstance(prob_ejecucion(np.linspace(0, 10, 33)), np.ndarray)
    and prob_ejecucion(np.linspace(0, 10, 33)).shape == (33,)
    and np.ndim(prob_ejecucion(3.0)) == 0,
    "Esta vectorizada: array entra, array sale; escalar entra, escalar sale",
    "P3 la necesita asi para la Figura 1",
)
revisar(
    np.all(np.diff(prob_ejecucion(np.linspace(0, s_corte, 500))) < 0),
    "Es estrictamente decreciente antes del corte",
)
revisar(
    float(prob_ejecucion(1.50)) == 0.38,
    "En el regimen amplio (medio spread 1.50) la probabilidad es 0.38, no cero",
)


# --------------------------------------------------------------------------- #
titulo("4. PERDIDA ESPERADA FRENTE A INFORMADOS  (las dos integrales con quad)")
# --------------------------------------------------------------------------- #

print("\n    Lado del ask: integral de A a infinito de (P - A) f(P) dP")
print("    Sube A y la perdida DEBE bajar: el informado solo compra si P > A\n")
print(f"    {'A':>10} | {'perdida lado ask':>18}")
print(f"    {'-' * 10}-+-{'-' * 18}")
lado_ask_serie = []
for A in [20.0, 21.0, 22.0, 23.0, 24.0]:
    v = perdida_informados(A, 18.0)[0]
    lado_ask_serie.append(v)
    print(f"    {A:>10.2f} | {v:>18.8f}")

print("\n    Lado del bid: integral de 0 a B de (B - P) f(P) dP")
print("    Sube B y la perdida DEBE subir: se mueve en direccion contraria\n")
print(f"    {'B':>10} | {'perdida lado bid':>18}")
print(f"    {'-' * 10}-+-{'-' * 18}")
lado_bid_serie = []
for B in [16.0, 17.0, 18.0, 19.0, 19.90]:
    v = perdida_informados(23.0, B)[1]
    lado_bid_serie.append(v)
    print(f"    {B:>10.2f} | {v:>18.8f}")

par = perdida_informados(23.0, 18.0)

revisar(isinstance(par, tuple) and len(par) == 2 and all(isinstance(x, float) for x in par),
        "Devuelve una tupla de dos floats, no la suma", f"{par}")
revisar(all(x >= 0.0 for x in par),
        "Los dos lados son >= 0 (son magnitudes, el signo lo pone Pi afuera)")
revisar(all(a > b for a, b in zip(lado_ask_serie, lado_ask_serie[1:])),
        "El lado del ask es estrictamente DECRECIENTE en A")
revisar(all(a < b for a, b in zip(lado_bid_serie, lado_bid_serie[1:])),
        "El lado del bid es estrictamente CRECIENTE en B",
        "por esto la funcion devuelve la tupla y no la suma")
revisar(perdida_informados(200.0, 18.0)[0] < 1e-12,
        "Con un ask absurdamente alto la perdida del lado ask es cero")


# --------------------------------------------------------------------------- #
titulo("5. GANANCIA ESPERADA FRENTE A LIQUIDEZ")
# --------------------------------------------------------------------------- #

print(f"\n    {'medio spread s':>16} | {'ganancia (2 lados)':>20}")
print(f"    {'-' * 16}-+-{'-' * 20}")
for s in [0.0, 1.0, 2.0, 3.0, 3.125, 4.0, 6.25, 8.0]:
    print(f"    {s:>16.3f} | {ganancia_liquidez(S0 + s, S0 - s):>20.8f}")

s_teorico = ALPHA / (2 * BETA)
malla_s = np.linspace(0.0, s_corte, 2001)
s_num = malla_s[int(np.argmax([ganancia_liquidez(S0 + s, S0 - s) for s in malla_s]))]

revisar(abs(ganancia_liquidez(S0, S0)) < 1e-12, "Sin spread no hay ganancia")
revisar(abs(ganancia_liquidez(S0 + 7, S0 - 7)) < 1e-12,
        "Pasado el corte nadie cruza, asi que la ganancia es cero")
revisar(abs(s_num - s_teorico) < 1e-2,
        f"El maximo por lado esta en s = {s_teorico} (derivada 0.5 - 0.16s = 0)",
        f"el barrido numerico lo pone en {s_num:.4f}")
revisar(
    abs(ganancia_liquidez(S0 + 2, S0 - 1) - ganancia_liquidez(S0 + 1, S0 - 2)) < 1e-12,
    "Es simetrica: pi_LB y pi_LS son la misma funcion",
)


# --------------------------------------------------------------------------- #
titulo("6. UTILIDAD ESPERADA  Pi(A,B)  Y FUNCION OBJETIVO")
# --------------------------------------------------------------------------- #

A_p, B_p = 22.0, 18.0
la, lb = perdida_informados(A_p, B_p)
print(f"\n    Evaluada en A = {A_p}, B = {B_p}\n")
print(f"    {'pi_i':>6} | {'pi_l':>6} | {'Pi(A,B)':>14} | {'armada a mano':>14}")
print(f"    {'-' * 6}-+-{'-' * 6}-+-{'-' * 14}-+-{'-' * 14}")
coincide_formula = True
for pi in [0.0, 0.1, 0.4, 0.7, 1.0]:
    obtenida = utilidad_esperada(A_p, B_p, pi_i=pi)
    a_mano = (1 - pi) * ganancia_liquidez(A_p, B_p) - pi * (la + lb)
    coincide_formula &= abs(obtenida - a_mano) < 1e-12
    print(f"    {pi:>6.1f} | {1-pi:>6.1f} | {obtenida:>14.8f} | {a_mano:>14.8f}")

con_bug = 0.6 * ganancia_liquidez(A_p, B_p) - 0.1 * (la + lb)

revisar(coincide_formula,
        "Pi coincide con pi_l*[ganancia] - pi_i*[perdida] armada pieza por pieza")
revisar(abs(utilidad_esperada(A_p, B_p, pi_i=0.1) - con_bug) > 1e-6,
        "utilidad_esperada NO lee PI_L global: calcula pi_l = 1 - pi_i",
        "probado en pi_i=0.1; en pi_i=0.4 los dos caminos darian lo mismo y no se veria")
revisar(utilidad_esperada(A_p, B_p, pi_i=0.0) > 0 > utilidad_esperada(A_p, B_p, pi_i=1.0),
        "Sin informados la utilidad es positiva; con puros informados, negativa")
revisar(
    all(a > b for a, b in zip(
        [utilidad_esperada(A_p, B_p, pi_i=p) for p in [0.0, 0.2, 0.4, 0.6]],
        [utilidad_esperada(A_p, B_p, pi_i=p) for p in [0.2, 0.4, 0.6, 0.8]])),
    "Cotizando en el mismo lugar, mas informados = menos utilidad",
)
revisar(
    all(abs(objetivo([A_p, B_p], pi_i=p) + utilidad_esperada(A_p, B_p, pi_i=p)) < 1e-15
        for p in [0.0, 0.4, 0.7]),
    "objetivo(x) es exactamente -utilidad_esperada  (minimize solo minimiza)",
)


# --------------------------------------------------------------------------- #
titulo("7. OPTIMIZACION DEL CASO BASE  (pi_i = 0.40)")
# --------------------------------------------------------------------------- #

with warnings.catch_warnings(record=True) as avisos:
    warnings.simplefilter("always")
    base = optimizar_cotizaciones()
avisos_quad = [str(w.message) for w in avisos if w.category is RuntimeWarning]

print("\n    --- REPORTE A DOS DECIMALES (lo que pide el enunciado 3.2.7) ---\n")
dato("Bid optimo", f"{base['bid']:.2f}")
dato("Ask optimo", f"{base['ask']:.2f}")
dato("Spread", f"{base['spread']:.2f}")
dato("Utilidad esperada por trade", f"{base['utilidad_esperada']:.2f}")

print("\n    --- PRECISION COMPLETA (lo que consume P2) ---\n")
dato("bid", repr(base["bid"]))
dato("ask", repr(base["ask"]))
dato("spread", repr(base["spread"]))
dato("utilidad_esperada", repr(base["utilidad_esperada"]))
dato("convergio", base["convergio"])
dato("mensaje", base["mensaje"])

f_pdf = distribucion_valor().pdf
_, err_ask = integrate.quad(lambda P: (P - base["ask"]) * f_pdf(P), base["ask"], np.inf)
_, err_bid = integrate.quad(lambda P: (base["bid"] - P) * f_pdf(P), 0.0, base["bid"])
p_ask, p_bid = perdida_informados(base["ask"], base["bid"])

print("\n    --- DESGLOSE EN EL OPTIMO ---\n")
dato("Medio spread del ask  (ask - S0)", f"{base['ask'] - S0:.6f}")
dato("Medio spread del bid  (S0 - bid)", f"{S0 - base['bid']:.6f}")
dato("Prob. de ejecucion en el ask", f"{float(prob_ejecucion(base['ask'] - S0)):.6f}")
dato("Prob. de ejecucion en el bid", f"{float(prob_ejecucion(S0 - base['bid'])):.6f}")
dato("Ganancia frente a liquidez (bruta)", f"{ganancia_liquidez(base['ask'], base['bid']):.6f}")
dato("Perdida informados, lado ask", f"{p_ask:.6f}")
dato("Perdida informados, lado bid", f"{p_bid:.6f}")
dato("Error absoluto de quad, lado ask", f"{err_ask:.3e}")
dato("Error absoluto de quad, lado bid", f"{err_bid:.3e}")

revisar(set(base) == {"bid", "ask", "spread", "utilidad_esperada", "pi_i",
                      "convergio", "mensaje"},
        "Devuelve las siete llaves exactas del contrato")
revisar(base["convergio"], "El optimizador convergio", base["mensaje"])
revisar(base["ask"] >= S0 and 0 < base["bid"] <= S0,
        "Respeta las restricciones: A en [S0, inf), B en (0, S0]")
revisar(abs(base["spread"] - (base["ask"] - base["bid"])) < 1e-12,
        "spread = ask - bid")
revisar(abs(base["utilidad_esperada"]
            - utilidad_esperada(base["ask"], base["bid"])) < 1e-9,
        "La utilidad reportada es Pi evaluada realmente en el optimo")
revisar(err_ask < TOL_QUAD and err_bid < TOL_QUAD,
        f"El error de quad es menor a {TOL_QUAD:.0e} en las dos integrales")
revisar(avisos_quad == [], "quad no emitio ninguna advertencia al optimizar",
        "" if not avisos_quad else str(avisos_quad))
revisar(base["bid"] != round(base["bid"], 2) and base["ask"] != round(base["ask"], 2),
        "Devuelve precision completa, sin redondear",
        "redondear aqui sesga el P&L acumulado de 10,000 trades de P2")
revisar(p_ask > p_bid,
        "Duele mas el lado del ask que el del bid",
        "porque E[P] = 20.0 esta ARRIBA de S0 = 19.90: al informado le conviene comprar")


# --------------------------------------------------------------------------- #
titulo("8. PUNTO ABIERTO O1 — EL MONOPOLISTA CON pi_i = 0")
# --------------------------------------------------------------------------- #

mono = optimizar_cotizaciones(pi_i=0.0)
medio_teorico = ALPHA / (2 * BETA)
total_teorico = ALPHA / BETA
util_teorica = 2 * (ALPHA - BETA * medio_teorico) * medio_teorico

print("\n    Derivacion: con pi_i = 0 la utilidad es separable y cada lado")
print("    maximiza (0.50 - 0.08*s)*s.  d/ds = 0.50 - 0.16*s = 0  =>  s = 3.125\n")
dato("Medio spread del ask, obtenido", f"{mono['ask'] - S0:.8f}")
dato("Medio spread del bid, obtenido", f"{S0 - mono['bid']:.8f}")
dato("Medio spread teorico  ALPHA/(2*BETA)", f"{medio_teorico}")
dato("Spread total, obtenido", f"{mono['spread']:.8f}")
dato("Spread total teorico  ALPHA/BETA", f"{total_teorico}")
dato("Utilidad obtenida", f"{mono['utilidad_esperada']:.8f}")
dato("Utilidad teorica  2*(0.5-0.08*3.125)*3.125", f"{util_teorica}")

revisar(abs((mono["ask"] - S0) - medio_teorico) < 1e-3,
        f"Lectura A: el medio spread por lado es {medio_teorico}")
revisar(abs((S0 - mono["bid"]) - medio_teorico) < 1e-3,
        f"Lectura A: simetrico en el bid")
revisar(abs(mono["spread"] - total_teorico) < 1e-3,
        f"Lectura B: el spread TOTAL es 0.50/0.08 = {total_teorico}")
revisar(abs(mono["utilidad_esperada"] - util_teorica) < 1e-6,
        "La utilidad coincide con el valor analitico 1.5625")
revisar(base["spread"] > mono["spread"],
        "Con informados el spread se ensancha respecto al monopolista",
        f"{base['spread']:.4f} contra {mono['spread']:.4f}: "
        f"{base['spread'] - mono['spread']:.4f} es el precio de la seleccion adversa")


# --------------------------------------------------------------------------- #
titulo("9. VERIFICACION POR MALLA  (arbitro independiente de L-BFGS-B)")
# --------------------------------------------------------------------------- #

print("\n    quad mete ruido de ~1e-10 en Pi y L-BFGS-B aproxima el gradiente por")
print("    diferencias finitas, que amplifica ese ruido. La malla no usa gradiente.")
print("    La rejilla se ancla en multiplos de 0.01, NO en el optimo: si se anclara")
print("    en el optimo, ese punto caeria en la malla y la prueba se responderia sola.\n")
print(f"    {'pi_i':>5} | {'ask opt':>10} {'ask malla':>10} {'dif':>8} | "
      f"{'bid opt':>10} {'bid malla':>10} {'dif':>8}")
print(f"    {'-' * 5}-+-{'-' * 30}-+-{'-' * 30}")

for pi in [0.0, 0.1, 0.4, 0.7]:
    r = optimizar_cotizaciones(pi_i=pi)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        m = verificar_optimo_en_malla(r, paso=0.01, radio=0.10)
    print(f"    {pi:>5.1f} | {r['ask']:>10.4f} {m['ask_malla']:>10.4f} "
          f"{m['dif_ask']:>8.4f} | {r['bid']:>10.4f} {m['bid_malla']:>10.4f} "
          f"{m['dif_bid']:>8.4f}")
    revisar(m["coincide"], f"pi_i = {pi}: el optimo coincide con la malla dentro de 0.02")


# --------------------------------------------------------------------------- #
titulo("10. ANALISIS DE SENSIBILIDAD  (pi_i en 0.1, 0.4, 0.7)")
# --------------------------------------------------------------------------- #

df = analisis_sensibilidad()
print()
print(df.to_string(index=False))
print("\n    Aperturas por lado:\n")
print(f"    {'pi_i':>6} | {'ask - S0':>10} | {'S0 - bid':>10} | {'asimetria':>10}")
print(f"    {'-' * 6}-+-{'-' * 10}-+-{'-' * 10}-+-{'-' * 10}")
for _, fila in df.iterrows():
    ap_a, ap_b = fila["ask"] - S0, S0 - fila["bid"]
    print(f"    {fila['pi_i']:>6.1f} | {ap_a:>10.4f} | {ap_b:>10.4f} | {ap_a - ap_b:>10.4f}")

revisar(list(df.columns) == ["pi_i", "bid", "ask", "spread",
                            "utilidad_esperada", "convergio"],
        "Las seis columnas exactas del contrato")
revisar(len(df) == 3 and list(df["pi_i"]) == [0.1, 0.4, 0.7], "Tres filas, una por pi_i")
revisar(bool(df["convergio"].all()), "Las tres optimizaciones convergieron")
revisar(bool(df["spread"].is_monotonic_increasing),
        "El spread optimo CRECE con pi_i",
        "es el resultado central: el formador se defiende ensanchando")
revisar(bool(df["utilidad_esperada"].is_monotonic_decreasing),
        "La utilidad CAE con pi_i",
        "ensanchar mitiga la perdida pero no la borra")
revisar(bool(((df["ask"] - S0) > (S0 - df["bid"])).all()),
        "El ask se abre mas que el bid en los tres escenarios")
fila_base = df[df["pi_i"] == 0.4].iloc[0]
revisar(abs(fila_base["bid"] - base["bid"]) < 1e-9
        and abs(fila_base["ask"] - base["ask"]) < 1e-9,
        "La fila de pi_i = 0.4 reproduce exactamente el caso base")


# --------------------------------------------------------------------------- #
titulo("RESUMEN")
# --------------------------------------------------------------------------- #

if _fallas:
    print(f"\n  {len(_fallas)} COMPROBACION(ES) FALLARON:\n")
    for f in _fallas:
        print(f"    - {f}")
    raise SystemExit(1)

print("\n  Todas las comprobaciones de P1 pasaron.")
print("\n  Valores para pasarle a P2 (construir_regimenes espera precision completa):")
print(f"    bid_opt = {base['bid']!r}")
print(f"    ask_opt = {base['ask']!r}")
