# P1 — Modelo de Copeland-Galai y optimización de cotizaciones

**Responsable: Gonzalo. Rama: `feat/p1-modelo`. Archivo único: `src/model.py`.**

Hereda todo lo del `CLAUDE.md` de la raíz, incluidas las firmas congeladas de la sección
Contratos entre módulos. Aquí van solo los requisitos puntuales de esta parte; no se repite nada
que ya esté allá.

Esta es la parte de la que dependen las otras tres. Si el contrato de `src/model.py` cambia, se
avisa antes, no después.

## Las tareas (copiadas tal cual del enunciado, 3.2 y 3.5)

3. Implemente f(P) usando `scipy.stats.erlang` con los parámetros indicados.
4. Implemente las dos integrales de pérdida usando `scipy.integrate.quad`. No use aproximaciones
   por sumas discretas.
5. Implemente la función objetivo como el negativo de Pi(A,B), para poder minimizarla.
6. Optimice con `scipy.optimize.minimize` usando las restricciones B en (0, S0] y A en [S0, inf).
7. Reporte el Bid óptimo, el Ask óptimo, el spread resultante y la utilidad esperada por trade,
   todos con dos decimales.

Y de 3.5:

> Repita la optimización para pi_i en {0.1, 0.4, 0.7}. Grafique el spread óptimo contra pi_i y
> compare el resultado numérico contra la predicción teórica vista en la Sesión 04.

La gráfica es de P3. Aquí solo se produce el DataFrame que la alimenta.

## Cómo encaja con las convenciones del proyecto

- **Todas las constantes del caso base se definen aquí y solo aquí.** `simulation.py`,
  `plots.py`, `tests/` y `main.py` las importan de `src.model`.

- **La distribución del valor vive en una sola función**, `distribucion_valor()`, que devuelve un
  objeto congelado de scipy. P2 la usa para samplear el valor verdadero P. Que las dos partes
  usen literalmente el mismo objeto es lo que garantiza que modelo y simulación sean comparables.

- **Verificación de la Erlang al importar el módulo.** Un assert de módulo comprobando que
  `distribucion_valor().mean()` es 20.0 con tolerancia 1e-9. Es la protección contra el error de
  `scale=3` en vez de `scale=1/3`, que no lanza excepción y contamina todo el proyecto.

- **`prob_ejecucion` truncada en cero y vectorizable.** `np.maximum(0.0, ALPHA - BETA*s)`. P3 la
  llama con un `np.linspace` para la Figura 1, así que tiene que aceptar arrays. Una de las tres
  pruebas obligatorias verifica que nunca devuelve negativo.

- **`perdida_informados(A, B)` devuelve una tupla de dos elementos, no la suma.** El desglose por
  lado se usa en el análisis y en la exposición: permite mostrar de qué lado duele más la
  selección adversa. Cada integral con `quad`, con `np.inf` como límite superior en el lado del
  ask y `0` como límite inferior en el lado del bid.

- **Revisa el segundo valor que devuelve `quad`** (la estimación de error absoluto). Si supera
  1e-8 se imprime una advertencia. No se silencia.

- **`utilidad_esperada` recibe `pi_i` y calcula `pi_l = 1 - pi_i` internamente.** No leas `PI_L`
  de la constante global dentro de la función: si lo haces, el análisis de sensibilidad queda mal
  y el error es invisible, porque para `pi_i = 0.4` los números coinciden.

- **Optimizador:** `minimize` con `method='L-BFGS-B'` y `bounds=[(S0, None), (1e-6, S0)]` para
  `x = [A, B]`. Punto inicial `x0 = [S0 + 1.0, S0 - 1.0]`. Si `res.success` es False se registra
  en la llave `convergio` y se imprime `res.message`. No se devuelve un resultado no convergido
  como si fuera bueno.

- **Verificación por malla, obligatoria.** Como `quad` introduce ruido numérico en el gradiente,
  el óptimo se contrasta contra un barrido en malla fina (paso 0.01 por lado, en un rango
  razonable alrededor del óptimo). Si el mejor punto de la malla difiere en más de 0.02 en
  cualquiera de los dos lados, se investiga antes de seguir. Esta verificación va como función
  auxiliar, no dentro de `optimizar_cotizaciones`, para no encarecer cada llamada.

- **Redondeo:** el reporte a dos decimales es para la salida impresa. `optimizar_cotizaciones`
  devuelve precisión completa; P2 usa esos valores como precios de ejecución y redondear ahí
  introduce un sesgo pequeño pero real en el P&L acumulado de 10,000 trades.

- **`analisis_sensibilidad` llama a `optimizar_cotizaciones` una vez por cada `pi_i`** y arma el
  DataFrame con las columnas del contrato. Nada más. La comparación contra la teoría de la
  Sesión 04 está bloqueada por el punto abierto O3.

## Entregable

- `src/model.py`, con todas las funciones del contrato y docstrings en las principales.
- Sin figuras, sin prints fuera de las funciones de reporte, sin `if __name__ == '__main__'`.
- Las pruebas de este módulo las escribe P4, no P1. Aun así, `pytest` debe pasar antes de abrir
  el Pull Request.
- Pull Request a `main` con Milca como reviewer.

## Checklist

- [ ] `from src.model import *` no lanza y el assert de la media en 20.0 está activo
- [ ] `prob_ejecucion(np.array([0, 3, 6.25, 10]))` da `[0.5, 0.26, 0.0, 0.0]` sin negativos
- [ ] `prob_ejecucion(6.25)` es exactamente 0.0 y `prob_ejecucion(6.24)` es positivo
- [ ] Ambas integrales usan `quad`; `grep -n "trapz\|cumsum" src/model.py` no devuelve nada
- [ ] `perdida_informados` devuelve tupla de dos floats, ambos mayores o iguales a 0
- [ ] El error absoluto reportado por `quad` es menor a 1e-8 en ambas integrales en el óptimo
- [ ] `utilidad_esperada` no usa `PI_L`: verificado leyendo el cuerpo de la función
- [ ] Con `pi_i=0.0`, `ask - S0` y `S0 - bid` valen 3.125 con error menor a 1e-3 (ver O1)
- [ ] Con `pi_i=0.4`, el óptimo coincide con el de la malla de paso 0.01 dentro de 0.02
- [ ] `optimizar_cotizaciones` devuelve las siete llaves exactas del contrato
- [ ] `analisis_sensibilidad()` devuelve 3 filas, seis columnas exactas, spread creciente en pi_i
- [ ] `convergio` es True en las cuatro optimizaciones (caso base más las tres de sensibilidad)
- [ ] Gonzalo puede explicar sin ver el código por qué el segundo corchete de Pi lleva signo
      negativo y por qué la integral del ask va de A a infinito y no de S0 a infinito
