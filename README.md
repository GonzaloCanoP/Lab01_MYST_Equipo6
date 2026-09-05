# Lab01 — Cotizaciones óptimas de un formador de mercado

Laboratorio 01 de **Microestructuras y Sistemas de Trading (IT1731B)** — ITESO, Otoño 2026.
Módulo 1, Situación de Aprendizaje 1. **Equipo 6.**

## Integrantes

| Integrante | GitHub | Parte |
|---|---|---|
| Gonzalo Cano | [@GonzaloCanoP](https://github.com/GonzaloCanoP) | P1 — modelo y optimización · P4 — pruebas, orquestación y reporte |
| Milca Correa | [@Milca2004](https://github.com/Milca2004) | P2 — simulación y Monte Carlo · P3 — figuras y notebook |

## Descripción del proyecto

Este proyecto implementa el modelo de **Copeland y Galai (1983)** para un formador de mercado que
publica un Bid `B` y un Ask `A` alrededor de un precio de referencia `S0 = 19.90`, sin saber si
quien va a cruzar contra sus cotizaciones es un trader de liquidez —que opera por razones ajenas
al valor y le deja el medio spread— o un trader informado, que conoce el valor verdadero
`P ~ Erlang(k=60, λ=3)` y solo opera cuando el precio publicado está equivocado. Ensanchar el
spread aumenta lo que se gana por trade y reduce la pérdida frente a informados, pero también
espanta flujo de liquidez, así que existe un óptimo interior. El proyecto lo resuelve
numéricamente maximizando la utilidad esperada por trade `Π(A,B)` con `scipy.optimize.minimize`
sobre el negativo de la función objetivo, con las integrales de pérdida evaluadas con
`scipy.integrate.quad`; después simula 10,000 trades en tres regímenes de cotización, corre 1,000
corridas de Monte Carlo por régimen para medir la distribución del P&L y la probabilidad de
pérdida, y reoptimiza para `π_I ∈ {0.1, 0.4, 0.7}` contrastando el resultado numérico contra la
predicción teórica del modelo. Todo el análisis es reproducible con un solo comando.

## Instalación

Requiere **Python 3.12**.

```bash
git clone https://github.com/GonzaloCanoP/Lab01_MYST_Equipo6.git
cd Lab01_MYST_Equipo6
python3 -m venv .venv
source .venv/bin/activate          # en Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Reproducir todos los resultados

```bash
python main.py
```

Un solo comando, sin pasos manuales previos. Genera toda la salida numérica en consola y escribe
las cinco figuras en `docs/figuras/`, creando la carpeta si no existe. Tarda **unos 17 segundos**.

Las pruebas se corren aparte:

```bash
pytest -v
```

**14 pruebas, todas pasan en ~1.7 s.** Las tres obligatorias del enunciado (3.6) son
`test_prob_ejecucion_nunca_es_negativa`, `test_perdida_informados_es_decreciente_en_el_ask` y
`test_spread_optimo_con_pi_i_cero_es_el_del_monopolista`; las once restantes verifican la
contabilidad del P&L, la reproducibilidad, la condición de optimalidad y la equivalencia entre el
modelo y la simulación.

El análisis narrado, con las figuras inline, está en `notebooks/analysis.ipynb`. Ese notebook
**solo importa y grafica**: no contiene ni una fórmula del modelo ni del simulador.

## Semilla aleatoria

`SEED = 42`, definida **una sola vez** en `src/model.py` e importada por `src/simulation.py`,
`tests/test_model.py` y `main.py`. Ningún módulo define una semilla local.

Dos corridas consecutivas de `python main.py` producen una salida **idéntica byte a byte**
(verificado con `diff`). En Monte Carlo, la corrida *i*-ésima usa `SEED + i`: determinista y
distinta en cada corrida. Los tres regímenes comparten la misma semilla a propósito (**números
aleatorios comunes**), así que sortean el mismo tipo de trader, el mismo valor verdadero y la
misma dirección de liquidez trade por trade: la única diferencia entre ellos es dónde están
puestas las cotizaciones, no que a uno le haya tocado por azar una mezcla más favorable.

> **Supuesto declarado (O7).** El enunciado (2.3) dice literalmente `np.random.seed`, que fija el
> generador **global**. El proyecto usa `np.random.default_rng(SEED)`, que crea un generador
> **local**. No son intercambiables: con el global, el resultado de una función depende del orden
> en que se hayan llamado las funciones anteriores, así que la prueba de reproducibilidad no
> significaría gran cosa. Con el local, `simular_trades(..., seed=42)` devuelve siempre el mismo
> DataFrame sin importar qué se haya ejecutado antes. Se eligió el local porque es lo que las
> firmas congeladas del proyecto ya asumen (`seed=SEED` como argumento) y porque es la práctica
> recomendada por NumPy desde la versión 1.17.

## Parámetros del caso base

| Parámetro | Valor | Constante en `src/model.py` |
|---|---|---|
| Precio de referencia | 19.90 | `S0` |
| Forma de la Erlang, k | 60 | `K_ERLANG` |
| Tasa de la Erlang, λ | 3 | `LAMBDA_ERLANG` |
| Prob. de trader informado | 0.40 | `PI_I` |
| Prob. de trader de liquidez | 0.60 | `PI_L` |
| Intercepto de la demanda, α | 0.50 | `ALPHA` |
| Pendiente de la demanda, β | 0.08 | `BETA` |
| Semilla | 42 | `SEED` |

`P ~ Erlang(60, λ=3)` tiene media `k/λ = 20.00` y desviación estándar `√k/λ = 2.582`. **El precio
de referencia `S0 = 19.90` está 0.10 por debajo del valor esperado verdadero**, y ese sesgo no es
accidental: es lo que hace que el lado del ask cargue más pérdida por selección adversa que el
lado del bid.

## Resultados principales

**Cotizaciones óptimas con `π_I = 0.40`:**

| | Valor |
|---|---|
| Bid óptimo `B*` | **16.45** |
| Ask óptimo `A*` | **23.43** |
| Spread total | **6.98** |
| Utilidad esperada por trade `Π(A*,B*)` | **0.84** |

El optimizador converge (`CONVERGENCE: NORM OF PROJECTED GRADIENT <= PGTOL`) y el resultado se
verifica contra un barrido en malla fina de 0.01, independiente del gradiente: coincide dentro de
0.0023.

**Simulación, 10,000 trades por régimen (`forzar_ejecucion=True`):**

| Régimen | Bid / Ask | P&L total | P&L por trade | P&L vs. liquidez | P&L vs. informados |
|---|---|---:|---:|---:|---:|
| Óptimo | 16.45 / 23.43 | **+19,911.79** | +1.9912 | +20,809.76 | −897.98 |
| Estrecho | 19.75 / 20.05 | **−6,887.78** | −0.6888 | +894.90 | −7,782.68 |
| Amplio | 18.40 / 21.40 | **+5,246.39** | +0.5246 | +8,949.00 | −3,702.61 |

**Monte Carlo, 1,000 corridas de 1,000 trades por régimen:**

| Régimen | P&L promedio | Desv. estándar | Prob. de pérdida |
|---|---:|---:|---:|
| Óptimo | +2,009.03 | 60.44 | **0.000** |
| Estrecho | −672.75 | 45.71 | **1.000** |
| Amplio | +542.75 | 46.38 | **0.000** |

---

# Análisis

## 1. ¿Por qué los traders informados generan la necesidad de un spread?

Porque **cotizar en firme es regalar una opción**, y el informado la ejerce siempre en contra. El
régimen estrecho lo muestra con toda claridad.

Con bid 19.75 y ask 20.05, el medio spread es de **0.15 por lado**. Cada trader de liquidez que
cruza le deja al formador exactamente 0.15, sin excepción. Pero la pérdida esperada frente a
informados con esas cotizaciones, calculada con las integrales del modelo, es:

```
lado ask   E[(P − 20.05)⁺] = 1.0047
lado bid   E[(19.75 − P)⁺] = 0.9042
total                        1.9089
```

Ponderando por las probabilidades de llegada, la cuenta por trade no cierra ni de cerca:

```
ganancia esperada de liquidez   π_L × 0.15   = 0.60 × 0.15   = +0.0900
pérdida esperada de informados  π_I × 1.9089 = 0.40 × 1.9089 = −0.7636
                                                     Π(A,B)  = −0.6736
```

**La pérdida es 8.5 veces mayor que la ganancia.** La simulación lo confirma: de los 10,000
trades, 5,966 fueron de liquidez y dejaron +894.90 en total; 3,843 informados ejecutaron y se
llevaron −7,782.68, o sea **−2.03 por cada informado que cruzó**. Para pagar un solo informado se
necesitarían 13.5 trades de liquidez, pero por cada informado solo llegan 1.5 traders de liquidez
(`π_L/π_I = 0.6/0.4`). El régimen cierra en **−6,887.78** y pierde en **las 1,000 corridas** del
Monte Carlo, sin una sola excepción.

El spread es lo que el formador cobra para financiar esa opción. No es un margen comercial: en
este modelo **no hay costos de procesamiento ni de inventario, así que el spread entero es
información asimétrica**.

## 2. ¿Cómo cambia el costo de selección adversa conforme se amplía el spread?

Cae rápido y de forma no lineal. Esta es la pérdida esperada frente a informados, evaluada a medio
spread simétrico creciente alrededor de `S0` (salida de la sección 2 de `main.py`):

| Medio spread | Bid | Ask | Lado ask | Lado bid | **Total** | vs. estrecho |
|---:|---:|---:|---:|---:|---:|---:|
| 0.15 | 19.75 | 20.05 | 1.0047 | 0.9042 | **1.9089** | — |
| 0.50 | 19.40 | 20.40 | 0.8477 | 0.7463 | **1.5940** | −16% |
| 1.00 | 18.90 | 20.90 | 0.6551 | 0.5534 | **1.2085** | −37% |
| 1.50 | 18.40 | 21.40 | 0.4971 | 0.3976 | **0.8947** | −53% |
| 2.00 | 17.90 | 21.90 | 0.3704 | 0.2759 | **0.6463** | −66% |
| 3.00 | 16.90 | 22.90 | 0.1947 | 0.1181 | **0.3129** | −84% |
| 3.50 | 16.40 | 23.40 | 0.1374 | 0.0724 | **0.2098** | −89% |
| 4.00 | 15.90 | 23.90 | 0.0952 | 0.0423 | **0.1375** | −93% |

Tres cosas que se leen de la tabla:

- **La caída es convexa, no proporcional.** Multiplicar el medio spread por 10 (de 0.15 a 1.50)
  reduce el costo apenas a la mitad; multiplicarlo por 27 (a 4.00) lo reduce 93%. La razón es que
  la pérdida es la cola de una Erlang, que decae exponencialmente, así que los primeros centavos
  de spread compran mucha menos protección que los últimos.
- **El costo nunca llega a cero.** Con medio spread 4.00 todavía quedan 0.1375 de pérdida
  esperada: la Erlang tiene soporte infinito por la derecha, así que siempre existe un estado del
  mundo donde el informado gana.
- **El lado del ask siempre pesa más que el del bid**, y la brecha se ensancha con el spread (1.11×
  a medio spread 0.15, 2.25× a 4.00). Es el efecto de `S0 = 19.90 < E[P] = 20.00` combinado con
  el sesgo a la derecha de la Erlang.

Por eso el óptimo no está ni en el extremo estrecho ni en el ancho: **en `A* = 23.43 / B* = 16.45`
la pérdida esperada es 0.2110, un 89% menos que en el régimen estrecho**, y el costo de esa
protección es la ganancia de liquidez que se deja de capturar.

## 3. ¿Cuál régimen acumula el mayor desbalance de inventario y por qué?

**El régimen óptimo**, y no por poco. Descomponiendo el inventario por tipo de trader:

| Régimen | Inv. final | \|Inv\| máx | \|Inv\| promedio | Aporte de informados | Aporte de liquidez |
|---|---:|---:|---:|---:|---:|
| Óptimo | **−105** | **148** | **92.9** | **−95** | −10 |
| Estrecho | −51 | 117 | 60.5 | −41 | −10 |
| Amplio | +1 | 88 | 34.5 | +11 | −10 |

El aporte de liquidez es **idéntico (−10) en los tres**: comparten semilla, la dirección se sortea
50/50 y con `forzar_ejecucion=True` todos ejecutan, así que ese componente es literalmente la
misma caminata aleatoria. **Todo el desbalance viene de los informados**, y el mecanismo es la
asimetría de la Erlang:

| Régimen | `P(P > A)` | `P(P < B)` | Razón | Deriva teórica por 10,000 trades |
|---|---:|---:|---:|---:|
| Óptimo | 0.0966 | 0.0776 | **1.245** | **−76.2** |
| Estrecho | 0.4751 | 0.4784 | 0.993 | +13.1 |
| Amplio | 0.2834 | 0.2764 | 1.025 | −28.0 |

La deriva esperada es `−n · π_I · [P(P>A) − P(P<B)]`. Verificada sobre **200 semillas**
independientes, el inventario final promedio es **−71.5 ± 6.2** en el óptimo, **+22.1 ± 7.2** en
el estrecho y **−20.9 ± 6.5** en el amplio: la deriva del régimen óptimo es la única
estadísticamente distinta de cero por un margen amplio.

**Por qué pasa.** La Erlang tiene sesgo a la derecha. Al cotizar cerca de `S0` (régimen estrecho),
ambas colas son casi mitad y mitad y los informados compran y venden en proporciones parecidas.
Al alejar las cotizaciones, la cola derecha —más pesada— domina en términos relativos: en el
óptimo llegan **1.25 informados comprando por cada uno vendiendo** (404 compras contra 309 ventas
en la corrida base), y cada compra le resta una unidad al inventario del formador. Es un goteo
persistente en una sola dirección, no ruido.

**El riesgo real que el modelo no captura.** El modelo maximiza utilidad **por trade** y trata cada
trade como independiente: un inventario de −105 unidades no le cuesta absolutamente nada en
`Π(A,B)`. En la realidad esa es una **posición corta de 105 unidades a ~19.90 = 2,090 de exposición
direccional**, sujeta a margen, a límites de riesgo y a la posibilidad de que el precio se mueva en
contra antes de poder deshacerla. Y hay algo peor que el tamaño: la posición corta se acumula
justamente **porque los informados están comprando**, o sea porque el valor verdadero está por
encima del ask. El formador termina corto exactamente en el escenario en que el activo vale más.
Ese es el riesgo de inventario correlacionado con la información, y un formador real lo maneja
sesgando sus cotizaciones (*inventory skewing*) o cubriéndose, dos cosas que este modelo ni
contempla.

## 4. ¿Cómo se comporta el spread óptimo al variar `π_I`? ¿Coincide con la teoría?

Crece con `π_I`, la utilidad cae, y **sí coincide con la teoría — con residuo de orden 1e−6**.

| `π_I` | Bid | Ask | Spread | Utilidad esperada |
|---:|---:|---:|---:|---:|
| 0.1 | 16.7088 | 23.1065 | **6.3977** | 1.3787 |
| 0.4 | 16.4517 | 23.4277 | **6.9760** | 0.8403 |
| 0.7 | 16.0070 | 24.0008 | **7.9939** | 0.3366 |

**La predicción teórica.** Derivando `Π(A,B)` respecto de `A`, con `a = A − S0` y usando que
`d/dA ∫_A^∞ (P−A)f(P)dP = −(1−F(A))`:

```
∂Π/∂A = π_L·(α − 2β·a) + π_I·(1 − F(A)) = 0
```

que es exactamente la CPO de la sesión de Copeland-Galai del curso (allá, con distribución
discreta, se escribe `0.7(0.5 − 0.1d) + 0.3(0.10) = 0`). Despejando:

```
a*  =   α/(2β)    +   (π_I/π_L) · (1 − F(A*)) / (2β)
      monopolista       prima de selección adversa
```

El primer término **no depende de `π_I`** y vale `0.50/(2×0.08) = 3.125` siempre. El segundo es
todo el efecto de la información asimétrica. Contrastando contra el óptimo numérico:

| `π_I` | `a*` numérico | Monopolista | Prima | `a*` teórico | Residuo |
|---:|---:|---:|---:|---:|---:|
| 0.0 | 3.1250 | 3.1250 | 0.0000 | 3.1250 | 5.2e−07 |
| 0.1 | 3.2065 | 3.1250 | 0.0815 | 3.2065 | 2.7e−07 |
| 0.4 | 3.5277 | 3.1250 | 0.4027 | 3.5277 | 1.0e−06 |
| 0.7 | 4.1008 | 3.1250 | 0.9758 | 4.1008 | 1.7e−06 |

El óptimo numérico y la predicción teórica **son el mismo punto**. Y la descomposición dice algo
que la tabla de spreads sola no dice: con `π_I = 0.4` la prima de selección adversa es el **11.4%**
del medio spread; con `π_I = 0.7` sube al **23.8%**. Casi un cuarto de lo que cobra el formador
existe únicamente para pagar información.

Dos consecuencias que caen solas de la fórmula:

- **Con `π_I = 0` el término derecho se anula** y queda `a* = α/(2β) = 3.125` por lado, o sea 6.25
  de spread total: el resultado del monopolista, que es justamente la prueba obligatoria
  `test_spread_optimo_con_pi_i_cero_es_el_del_monopolista`.
- **El óptimo está a la derecha del vértice de la parábola de ingreso de liquidez**, no en él. El
  vértice sería el óptimo solo si no hubiera informados. Esto contradice la intuición de que "si
  hay riesgo hay que ser conservador y cotizar cerca": cotizar cerca es lo que **expone**, porque
  reduce lo que se cobra y a la vez amplía el conjunto de estados en que el informado gana.

> **Matiz honesto.** La identidad es **implícita**, no una fórmula cerrada: `(1 − F(A*))` depende
> del `A*` que se quiere despejar. En el ejemplo discreto de clase ese término es la constante
> 0.10 y por eso ahí sí sale `d* = 5 + π_I/π_L`; con la Erlang continua no existe tal despeje. Por
> eso la fórmula se evalúa **en** el óptimo numérico: sirve para verificar que el optimizador
> encontró un punto estacionario del problema correcto, no para reemplazarlo. Está implementada en
> `prediccion_teorica_spread()` de `src/model.py` y verificada en
> `test_prediccion_teorica_coincide_con_el_optimo_numerico`.

## 5. Tres limitaciones de este modelo para un formador de mercado real

**1. No hay riesgo de inventario, aunque el inventario exista.** El modelo maximiza utilidad por
trade y trata cada trade como independiente, así que las −105 unidades de inventario que acumula
el régimen óptimo no entran en `Π(A,B)` con ningún signo. Nuestra propia Figura 3 muestra un
problema que la función objetivo no penaliza: el formador termina sistemáticamente corto (deriva
de −76 unidades por cada 10,000 trades) **y precisamente en el escenario donde el activo vale
más**, porque son los informados comprando quienes lo empujan ahí. Un formador real cotiza
asimétricamente para descargar inventario o se cubre; aquí no puede hacer ni una cosa ni la otra.

**2. El formador nunca aprende del flujo.** `S0 = 19.90` está clavado durante los 10,000 trades.
En la corrida del régimen óptimo, 404 informados compraron al ask de 23.43 — una señal
inequívoca de que el valor verdadero está muy por encima de la referencia— y el formador no mueve
sus cotizaciones ni un centavo. Eso es lo que el modelo de **Glosten y Milgrom (1985)** corrige con
actualización bayesiana secuencial: ahí cada trade es una observación que mueve la creencia sobre
`P`. Copeland-Galai es un modelo de un solo período, y por eso se puede resolver en forma cerrada,
pero el costo del supuesto es exactamente esa ceguera.

**3. Es un monopolio sin competencia, sin tiempo y sin fricciones de mercado.** El spread óptimo
de **6.98 sobre un precio de 19.90 es el 35% del valor del activo**. Ningún mercado real tolera
eso: otro formador cotizaría 6.90 y se llevaría todo el flujo. El modelo tampoco tiene tick size
(el óptimo cae en 16.451678, un precio que no existe en ningún libro de órdenes), ni tamaño de
orden, ni costos de procesamiento, ni límite de tiempo. Y la métrica es **rentabilidad por trade,
no por unidad de tiempo**, lo que se detalla abajo.

---

## ⚠ Advertencia de interpretación (obligatoria)

**Todos los resultados de la simulación son rentabilidad por trade, no por unidad de tiempo.** Esto
favorece artificialmente al régimen amplio, y en este proyecto no nos limitamos a mencionarlo:
está medido.

La simulación del enunciado corre con `forzar_ejecucion=True`, o sea que el trader de liquidez
**siempre** cruza. Pero `Π(A,B)` pondera la ganancia de liquidez por `prob_ejecucion(s)`, es decir
supone que el trader de liquidez puede **no** ejecutar. Son dos objetos distintos. Poniéndolos
lado a lado en el régimen óptimo:

| | P&L por trade |
|---|---:|
| Utilidad esperada del modelo, `Π(A*,B*)` | **0.8403** |
| Simulación con `forzar_ejecucion=False` (300,000 trades) | **0.8397** — error relativo **0.065%** |
| Simulación con `forzar_ejecucion=True` (10,000 trades) | **1.9912** — **2.37×** el modelo |

La primera línea es el resultado que sostiene todo el laboratorio: **con ejecución sorteada, la
simulación reproduce el modelo dentro del error de muestreo**. Modelo y simulador son el mismo
objeto, no dos implementaciones que casualmente corren. Es lo que verifica
`test_simulacion_converge_a_la_utilidad_esperada`.

La tercera línea es la advertencia. Al forzar la ejecución se está ignorando justamente el término
que **castiga** al spread ancho, así que el sesgo no es uniforme: infla más el P&L mientras más
ancho es el spread. En el régimen amplio el medio spread es 1.50, donde `prob_ejecucion = 0.38`
en vez de `α = 0.50`: forzar la ejecución le regala un 32% de flujo que en el modelo no tendría.
En un mercado real ese régimen haría muchos menos trades por hora que los otros dos, y la
comparación "por trade" de la tabla de resultados lo esconde por completo.

---

## Supuestos declarados

Puntos donde el enunciado admite más de una lectura. Se documentan en vez de resolverse en
silencio, porque un supuesto declarado se puede defender y uno tácito no.

**O1 — "El spread del monopolista es `0.50/0.08` por lado".** Con `π_I = 0` la utilidad es
separable y cada lado maximiza `(0.50 − 0.08·s)·s`, cuya CPO es `0.50 − 0.16·s = 0`, o sea
`s* = 3.125` de medio spread **por lado** y `6.25` de spread **total**. `0.50/0.08 = 6.25` es
entonces el total, no el de cada lado. La prueba obligatoria verifica **las dos cifras** con
tolerancia 1e−3 y pasa bajo cualquiera de las dos lecturas.

**O2 — El informado cuando `B ≤ P ≤ A`.** No tiene incentivo de ningún lado: comprar al ask le
costaría más de lo que vale y vender al bid le pagaría menos. La convención adoptada es dejar la
fila con `ejecutado=False`, `direccion='ninguna'` y P&L cero. Esto tensiona la frase del enunciado
"la simulación fuerza la ejecución de un trade en cada iteración", pero las alternativas son
peores: re-samplear `P` sesgaría la Erlang, y forzar una dirección al azar le regalaría P&L
positivo al formador, que es precisamente lo que un informado nunca hace. Se aplica solo a
informados; los traders de liquidez sí ejecutan siempre bajo `forzar_ejecucion=True`.

**O3 — La predicción teórica de la Sesión 04. RESUELTO.** Es la condición de primer orden
`π_L·(α − 2β·a) + π_I·(1 − F(A)) = 0`, la misma CPO de la sesión de Copeland-Galai del curso.
Está implementada, comparada numéricamente y probada; ver la pregunta 4.

**O4 — Cuántas figuras.** El código genera **cinco**: las cuatro de la sección 3.4 más la de
spread óptimo contra `π_I` que pide la 3.5. Cuántas van a las diapositivas es decisión de la
presentación, no del código.

**O5 — Dónde viven las figuras.** En `docs/figuras/`, en PNG a 150 dpi. **Los PNG se versionan**,
aunque `main.py` los regenere en cada corrida, para que el repositorio se pueda revisar sin
instalar nada. `main.py` crea la carpeta con `mkdir(parents=True, exist_ok=True)`, así que el
comando también corre en un clon limpio.

**O7 — Mecanismo de semilla.** Ver la sección *Semilla aleatoria* arriba.

**Desviación de la asignación de archivos.** `prediccion_teorica_spread()` se agregó a
`src/model.py` desde la rama de P4. Es matemática del modelo y `main.py` no implementa nada, así
que ese es su lugar natural; `src/model.py` es de P1, pero P1 y P4 son del mismo integrante, así
que no hubo riesgo de conflicto con el trabajo de la otra parte.

## Estructura del repositorio

```
Lab01_MYST_Equipo6/
├── README.md               # este archivo
├── requirements.txt        # dependencias con versiones fijadas
├── .gitignore
├── main.py                 # orquesta y reporta; no implementa nada
├── CLAUDE.md               # convenciones internas del equipo
├── src/
│   ├── model.py            # parámetros, utilidad esperada, optimización, CPO
│   ├── simulation.py       # simulador de trades y Monte Carlo
│   └── plots.py            # las cinco figuras (devuelven Figure, no guardan)
├── tests/
│   ├── test_model.py       # 14 pruebas de pytest
│   └── pruebasp1.py        # script de verificación manual de P1 (no es entregable)
├── notebooks/
│   └── analysis.ipynb      # solo análisis y figuras, sin lógica
└── docs/
    ├── presentacion.pdf
    ├── figuras/            # salida de main.py, versionada
    └── instrucciones/      # instrucciones por parte, uso interno del equipo
```

Toda la lógica vive en `src/`. El notebook importa y grafica; `main.py` orquesta e imprime. Las
firmas entre módulos están congeladas en `CLAUDE.md`, que es lo que permitió escribir las cuatro
partes en paralelo.

## Uso de asistencia de IA

Se usó **Claude (Anthropic)**, a través de Claude Code, en las cuatro partes del proyecto. En
concreto:

- **Redacción del código de `src/model.py`, `src/simulation.py`, `src/plots.py`, `main.py` y
  `tests/test_model.py`**, a partir de especificaciones que el equipo escribió antes en
  `docs/instrucciones/`: qué funciones debía haber, qué firma tenía cada una, qué contabilidad
  seguir y qué verificar.
- **Explicación de la teoría**: la derivación de la condición de primer orden, por qué el óptimo
  queda a la derecha del vértice de la parábola de ingreso, y por qué la asimetría contable entre
  liquidez (marcada contra `S0`) e informados (marcada contra `P`) *es* la selección adversa.
- **Detección de errores sutiles**: la parametrización `scale=1/λ` de `scipy.stats.erlang`, el
  factor 2 en la probabilidad de ejecución condicional a la dirección, y el riesgo de leer `PI_L`
  de la constante global en lugar de calcular `1 − π_I` en el análisis de sensibilidad.
- **Redacción de este README** y de la narrativa del notebook.

**Los números no se generaron con IA:** todos los resultados de este documento salen de ejecutar
`python main.py` y `pytest` en el repositorio, y son reproducibles con esos dos comandos. Las
decisiones de modelado que el enunciado dejaba abiertas se tomaron en equipo y están documentadas
arriba como supuestos declarados.

**Ambos integrantes pueden explicar todo el código del proyecto**, incluida la parte que no
escribieron: Gonzalo la simulación y el Monte Carlo de Milca, y Milca la optimización y la
condición de primer orden de Gonzalo.

## Referencias

- Copeland, T. E., & Galai, D. (1983). Information Effects on the Bid-Ask Spread. *The Journal of
  Finance*, 38(5), 1457–1469.
- Glosten, L. R., & Milgrom, P. R. (1985). Bid, Ask and Transaction Prices in a Specialist Market
  with Heterogeneously Informed Traders. *Journal of Financial Economics*, 14(1), 71–100.
- Bagehot, W. [pseud.] (1971). The Only Game in Town. *Financial Analysts Journal*, 27(2), 12–14.
