# Lab01 — Cotizaciones óptimas de un formador de mercado

Laboratorio 01 de Microestructuras y Sistemas de Trading (IT1731B, ITESO, Otoño 2026).
Módulo 1, Situación de Aprendizaje 1. Vale 10% de la calificación del curso.

Implementamos el modelo de Copeland y Galai (1983): encontrar el Bid y el Ask que maximizan la
utilidad esperada de un formador de mercado, y medir por simulación cuánto le cuesta la
selección adversa.

Este archivo tiene las convenciones que aplican a todo el proyecto. Las instrucciones
detalladas de cada parte viven en `docs/instrucciones/`.

---

## Quién trabaja aquí y qué instrucciones leer

Equipo de dos personas. El proyecto está partido en cuatro partes con archivos disjuntos: nadie
edita nunca el mismo archivo que el otro.

| Parte | Responsable | Rama | Archivos que toca | Instrucciones |
|---|---|---|---|---|
| P1 — Modelo y optimización | Gonzalo | `feat/p1-modelo` | `src/model.py` | `docs/instrucciones/P1_modelo.md` |
| P2 — Simulación y Monte Carlo | Milca | `feat/p2-simulacion` | `src/simulation.py` | `docs/instrucciones/P2_simulacion.md` |
| P3 — Figuras y notebook | Milca | `feat/p3-figuras` | `src/plots.py`, `notebooks/` | `docs/instrucciones/P3_figuras.md` |
| P4 — Pruebas, orquestación y reporte | Gonzalo | `feat/p4-infra` | `tests/`, `main.py`, `README.md`, `requirements.txt`, `.gitignore` | `docs/instrucciones/P4_infra.md` |

**Al iniciar una sesión de trabajo, identifica en qué parte estás** (por la rama actual o por
los archivos que se van a tocar) y **lee el archivo de instrucciones correspondiente antes de
escribir código**. No leas los cuatro: solo el que aplica.

Si no queda claro en qué parte estamos, pregúntalo antes de empezar.

Las convenciones compartidas que todos necesitan (contratos entre módulos, contabilidad del P&L,
parámetros) están más abajo en este mismo archivo, no en `docs/instrucciones/`. El índice de esa
carpeta está en `docs/instrucciones/README.md`.

El reglamento exige que ambos integrantes tengan commits propios. Un integrante sin commits
recibe cero en toda la parte técnica. No hagas commits a nombre de quien no está trabajando.

---

## El rol de Claude

Claude es el **tutor y asistente del curso**, no solo quien escribe el código. Tres cosas, y las
tres pesan igual:

**Escribe el código.** El equipo define qué pide la actividad y qué hace falta; Claude implementa
las funciones en `src/`.

**Lo explica.** Que el código corra no basta. El equipo tiene que poder decir en clase qué hace
cada función, por qué está escrita así y qué decisión hay detrás. Un resultado correcto que no
sabe defender no le sirve para nada.

**Enseña.** Complementa lo que se ve en clase: la teoría detrás del método, de dónde sale una
fórmula, por qué un supuesto importa y qué pasa cuando se rompe. Cuando aparece un concepto
nuevo, se explica; no se asume.

Dos corolarios prácticos:

- Si Gonzalo o Milca preguntan algo que "ya deberían saber", se explica derecho y sin
  condescendencia. Preguntar es el punto del curso.
- Si una decisión tuvo alternativas, se dice cuál era y por qué se descartó. Eso es justamente
  lo que después pueden defender.

Corolario específico de este Lab: la exposición vale 40 de los 100 puntos, y el profesor dirige
las preguntas a un integrante que él elige, sobre cualquier parte del trabajo. Al terminar cada
bloque de código, deja en el chat una explicación breve de qué se hizo y por qué, en un lenguaje
que sirva para repetirlo en voz alta.

---

## Reglas duras

1. **La estructura de carpetas es exacta** y está dictada por el enunciado. No se aceptan archivos
   sueltos en la raíz distintos a los listados abajo. No inventes módulos nuevos en `src/`.
2. **Toda la lógica vive en `src/`.** El notebook solo importa funciones y grafica. Un notebook
   que contenga la definición de la función de utilidad o del simulador se califica como
   Deficiente en Estructura del Proyecto. Es una penalización explícita del enunciado.
3. **Sin fórmulas inline en el notebook**, ni siquiera "para probar rápido".
4. **`python main.py` reproduce todo el proyecto** desde cero, sin pasos manuales. Si no corre con
   el comando documentado son −10 puntos.
5. **Semilla fija.** `SEED = 42`, definida una sola vez en `src/model.py`, importada por todos los
   demás módulos, documentada en el README. Nadie define su propia semilla local.
6. **Erlang en scipy:** `scipy.stats.erlang(a=60, scale=1/3)`. El parámetro `scale` es `1/lambda`,
   **no** `lambda`. Con `scale=3` la media sale 180 en lugar de 20 y el modelo entero queda mal
   sin lanzar ningún error.
7. **Las integrales de pérdida usan `scipy.integrate.quad`.** Prohibidas las sumas discretas,
   Monte Carlo o `np.trapz`. El enunciado lo pide explícitamente.
8. **La función objetivo es el negativo de Pi**, y se minimiza con `scipy.optimize.minimize`.
9. **Los puntos abiertos no se resuelven en silencio.** Están listados abajo. Pregunta antes de
   inventar una respuesta. Si aparece uno nuevo, agrégalo a la lista en vez de asumirlo.
10. **Los NaN y los casos degenerados se reportan, no se maquillan.** Si el optimizador no
    converge o una integral no alcanza tolerancia, se imprime y se documenta. Nada de `abs()`,
    `try/except: pass` ni fallbacks silenciosos.
11. **Antes de crear cualquier archivo o función, inspecciona `src/` completo.** Somos dos
    trabajando en paralelo; lo que crees que falta puede ya existir en otra rama.

---

## Estructura del repositorio

```
Lab01_MYST_Equipo6/
├── README.md
├── requirements.txt
├── .gitignore
├── main.py
├── CLAUDE.md
├── src/
│   ├── model.py               # función de utilidad y optimización
│   ├── simulation.py          # simulador de trades
│   └── plots.py               # generación de figuras
├── tests/
│   └── test_model.py
├── notebooks/
│   └── analysis.ipynb         # solo análisis y figuras, sin lógica
└── docs/
    ├── presentacion.pdf
    ├── figuras/               # salida de plots.py (punto abierto O2)
    └── instrucciones/         # instrucciones por parte, uso interno del equipo
```

`src/` tiene **exactamente** tres módulos. Si una función no cae natural en ninguno de los tres,
eso es señal de que está mal delimitada, o un punto abierto que se pregunta antes de crear un
cuarto archivo.

**El `.gitignore` no debe ignorar `docs/instrucciones/`.** Es material del equipo y tiene que
viajar con el repo.

---

## Parámetros del caso base

Fijos por el enunciado. Van como constantes de módulo en `src/model.py` y nadie los redefine en
otro lado.

| Parámetro | Valor | Constante |
|---|---|---|
| Precio de referencia S0 | 19.90 | `S0` |
| Forma de la Erlang K | 60 | `K_ERLANG` |
| Tasa de la Erlang lambda | 3 | `LAMBDA_ERLANG` |
| Prob. de trader informado | 0.40 | `PI_I` |
| Prob. de trader de liquidez | 0.60 | `PI_L` |
| Intercepto de la demanda | 0.50 | `ALPHA` |
| Pendiente de la demanda | 0.08 | `BETA` |
| Semilla | 42 | `SEED` |

Dos hechos que se usan como verificación:

- La Erlang(60, lambda=3) tiene media `K/lambda = 20.0` y desviación estándar
  `sqrt(K)/lambda = 2.582`. El precio de referencia S0 = 19.90 está 0.10 por debajo del valor
  esperado verdadero, y ese sesgo no es accidental.
- `prob_ejecucion(s) = max(0, 0.50 − 0.08*s)` llega a cero en `s = 6.25`. El régimen "amplio"
  del enunciado tiene medio spread de 1.50, muy por dentro de ese límite: ahí la probabilidad
  de ejecución es 0.38, no cero.

**`PI_L = 1 − PI_I` siempre.** En el análisis de sensibilidad, cuando `pi_i` cambia a 0.1 o 0.7,
`pi_l` cambia a 0.9 o 0.3. No dejes `PI_L` clavado en 0.60 dentro de las funciones.

### La función de utilidad (copiada del enunciado, sección 3.2)

```
Pi(A,B) = pi_L * [ pi_LB(A−S0)*(A−S0) + pi_LS(S0−B)*(S0−B) ]
        − pi_I * [ integral de A a inf de (P−A)*f(P) dP
                 + integral de 0 a B de (B−P)*f(P) dP ]
```

Primer corchete: ganancia esperada frente a traders de liquidez. Segundo: pérdida esperada frente
a informados. Implementar literalmente, sin simplificar el álgebra.

---

## Contratos entre módulos

Estas firmas están **congeladas**. Son lo que permite que P1, P2 y P3 se escriban en paralelo:
quien depende de un módulo que todavía no existe programa contra esta interfaz, no contra la
implementación. Cambiar una firma requiere avisar a la otra persona antes.

### `src/model.py`

```python
S0, K_ERLANG, LAMBDA_ERLANG, PI_I, PI_L, ALPHA, BETA, SEED   # constantes

def distribucion_valor()               -> rv_frozen de scipy
def prob_ejecucion(s)                  -> float | np.ndarray   # = pi_LB(s) = pi_LS(s)
def perdida_informados(A, B)           -> tuple[float, float]   # (lado ask, lado bid)
def ganancia_liquidez(A, B)            -> float
def utilidad_esperada(A, B, pi_i=PI_I) -> float
def objetivo(x, pi_i=PI_I)             -> float                 # -utilidad, x = [A, B]
def optimizar_cotizaciones(pi_i=PI_I)  -> dict
def analisis_sensibilidad(valores_pi=(0.1, 0.4, 0.7)) -> pd.DataFrame
```

`optimizar_cotizaciones` devuelve un dict con llaves exactas:
`{'bid', 'ask', 'spread', 'utilidad_esperada', 'pi_i', 'convergio', 'mensaje'}`.

`analisis_sensibilidad` devuelve un DataFrame con columnas exactas:
`['pi_i', 'bid', 'ask', 'spread', 'utilidad_esperada', 'convergio']`.

### `src/simulation.py`

```python
def construir_regimenes(bid_opt, ask_opt) -> dict[str, tuple[float, float]]
def simular_trades(bid, ask, n_trades=10_000, seed=SEED, forzar_ejecucion=True) -> pd.DataFrame
def simular_regimenes(regimenes, n_trades=10_000, seed=SEED) -> dict[str, pd.DataFrame]
def monte_carlo(bid, ask, n_corridas=1_000, n_trades=1_000, seed=SEED) -> np.ndarray
def monte_carlo_regimenes(regimenes, n_corridas=1_000, n_trades=1_000, seed=SEED) -> dict
def resumen_monte_carlo(resultados) -> pd.DataFrame
```

`construir_regimenes` devuelve exactamente:
`{'optimo': (bid_opt, ask_opt), 'estrecho': (19.75, 20.05), 'amplio': (18.40, 21.40)}`.

`simular_trades` devuelve un DataFrame con columnas exactas y en este orden:
`['trade_id', 'tipo_trader', 'direccion', 'ejecutado', 'valor_verdadero', 'precio_ejecucion',
'pnl', 'delta_inventario', 'pnl_acumulado', 'inventario']`

- `tipo_trader` en `{'informado', 'liquidez'}`
- `direccion` en `{'compra', 'venta', 'ninguna'}`, **desde la perspectiva del trader que llega**,
  no del formador de mercado.
- `delta_inventario`: +1 cuando el MM compra (el trader vende al bid), −1 cuando el MM vende (el
  trader compra al ask), 0 si no hubo trade.

`resumen_monte_carlo` devuelve un DataFrame con columnas exactas:
`['regimen', 'pnl_promedio', 'pnl_std', 'prob_perdida']`.

### `src/plots.py`

Cada función **devuelve un `matplotlib.figure.Figure` y no guarda nada**. Guardar es
responsabilidad de `main.py` vía `guardar_figura`. Así el notebook las muestra inline y `main.py`
las escribe a disco sin duplicar código.

```python
def fig_prob_ejecucion()                     -> Figure
def fig_pnl_acumulado(simulaciones)          -> Figure
def fig_inventario(simulaciones)             -> Figure
def fig_histograma_montecarlo(resultados_mc) -> Figure
def fig_sensibilidad(df_sensibilidad)        -> Figure
def guardar_figura(fig, nombre)              -> pathlib.Path
```

---

---

## Contabilidad del P&L

**Regla:** la simulación se contabiliza con el mismo criterio con el que está escrita Pi(A,B). Si
no, el P&L promedio simulado no converge a la utilidad esperada del modelo y no hay forma de
verificar nada.

| Situación | Precio | P&L del formador | Delta inventario |
|---|---|---|---|
| Liquidez compra al ask | A | `A − S0` | −1 |
| Liquidez vende al bid | B | `S0 − B` | +1 |
| Informado compra al ask (si P > A) | A | `A − P` (negativo) | −1 |
| Informado vende al bid (si P < B) | B | `P − B` (negativo) | +1 |

Frente a liquidez el trade se marca contra S0 porque el formador no aprende nada del flujo no
informado. Frente a informados se marca contra el valor verdadero P porque el informado solo
opera cuando sabe que el precio está mal. **Esa asimetría es la selección adversa**, no una
convención contable arbitraria.

Los dos casos frontera (qué hace el informado cuando `B <= P <= A`, y qué implica la ejecución
forzada) están en `docs/instrucciones/contabilidad_pnl.md`. Se leen antes de tocar
`src/simulation.py` o sus pruebas.

---

## Git

- **Nunca hagas commit ni push a `main`.** El trabajo va en la rama de la parte correspondiente.
- Verifica en qué rama estás antes de commitear. Si es `main`, detente y avísale a quien esté
  trabajando.
- Commits chicos, uno por unidad de sentido, con mensaje descriptivo en español y en imperativo:
  `feat(model): implementar perdida esperada frente a informados con quad`.
- `main.py`, `README.md`, `requirements.txt` y `.gitignore` son de P4. No los edites desde otra rama. Si P2 o
  P3 necesitan una dependencia nueva, se le avisa a P4.
- Antes de commitear, revisa qué archivos entran. Nada de `__pycache__/`, checkpoints de
  notebook, cachés de pytest ni entornos virtuales.
- Orden de merge: P1, luego P2, luego P3, y P4 al final, porque `main.py` importa de los tres
  módulos.

El proceso humano completo (clone, configuración de identidad, Pull Requests, resolución de
conflictos) está en el PDF del equipo, no aquí.

---

## Puntos abiertos — PENDIENTE DE CONFIRMAR

No inventes respuestas a estos. Pregunta. Los tres primeros bloquean código.

**O1 — El spread del monopolista en la prueba obligatoria.** El enunciado (3.6) pide verificar que
con `pi_i = 0` el spread óptimo sea `0.50/0.08` **"por lado"**. Con `pi_i = 0` la utilidad es
separable y cada lado maximiza `(0.50 − 0.08*s)*s`; la condición de primer orden es
`0.50 − 0.16*s = 0`, o sea `s = 3.125` por lado y `6.25` de spread total. El `0.50/0.08 = 6.25`
del enunciado es el spread **total**, no el de cada lado. Mientras se aclara, la prueba verifica
ambas cosas y pasa bajo cualquiera de las dos lecturas.

**O2 — El informado cuando `B <= P <= A`.** La convención propuesta (fila con `ejecutado=False`
y P&L cero) choca con la frase del enunciado "la simulación fuerza la ejecución de un trade en
cada iteración". Las alternativas se descartaron: re-samplear P sesga la Erlang, y forzar una
dirección al azar le regala P&L positivo al formador.

**O3 — La predicción teórica del análisis de sensibilidad.** El enunciado (3.5) pide comparar el
spread óptimo contra "la predicción teórica vista en la Sesión 04". Hace falta la fórmula exacta
de esa diapositiva. Sin ella, la comparación se queda en cualitativa y eso cuesta puntos en el
criterio B.

**O4 — Cuántas figuras son.** La sección 3.4 pide "exactamente estas cuatro figuras" y la 3.5
pide además graficar el spread óptimo contra `pi_i`, que sería una quinta. Afecta el conteo de
diapositivas, que tiene máximo de 12.
*No bloquea código:* el contrato congelado de `src/plots.py` ya define cinco funciones `fig_*` y
`main.py` genera las cinco. Lo abierto es cuántas van a las diapositivas, no cuántas produce el
código.

**O5 — Dónde se guardan las figuras.** El enunciado no lista carpeta de salida. Propuesta:
`docs/figuras/` en PNG a 150 dpi.
*No bloquea código:* el bloque de estructura y `P4_infra.md` ya trabajan sobre `docs/figuras/`,
que `main.py` crea con `mkdir(parents=True, exist_ok=True)`. Falta además decidir si esa carpeta
se versiona o se regenera siempre, y dejarlo escrito en el README.

**O6 — Número de equipo. RESUELTO:** equipo 6, y la materia se abrevia MYST. El repositorio
se llama `Lab01_MYST_Equipo6`. Confirmar contra el enunciado si el nombre exigido usa otra
convención antes de la entrega.

**O7 — Qué mecanismo de semilla se usa.** La regla dura 5 fija `SEED = 42` en `src/model.py`,
pero el enunciado (2.3) dice literalmente `np.random.seed`, que es el generador global, mientras
que las firmas congeladas de `src/simulation.py` reciben `seed=SEED` como argumento, que es el
patrón de `np.random.default_rng(seed)`. No son intercambiables: el global depende del orden en
que se llamen las funciones, el local no. `default_rng` es lo que las firmas ya asumen y lo que
hace que la prueba de reproducibilidad signifique algo. Se declara como supuesto en el README
mientras no se confirme.

---

## Cuándo está terminado el Lab

El checklist de cierre está en `docs/instrucciones/definicion_de_terminado.md`. Se revisa antes
de dar el laboratorio por entregado, no el mismo día de la exposición.
