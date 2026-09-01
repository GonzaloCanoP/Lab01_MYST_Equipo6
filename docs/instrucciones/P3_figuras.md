# P3 — Figuras obligatorias y notebook de análisis

**Responsable: Milca. Rama: `feat/p3-figuras`. Archivos: `src/plots.py`, `notebooks/analysis.ipynb`.**

Hereda todo lo del `CLAUDE.md` de la raíz, incluidas las firmas congeladas de la sección
Contratos entre módulos.

Esta parte pesa doble en la rúbrica: alimenta el criterio C (resultados, 20 pts) y es
prácticamente todo el criterio G (calidad de las visualizaciones, 5 pts). Además las figuras son
lo que se proyecta en la exposición: si no se leen desde el fondo del salón, no sirven.

## Las tareas (copiadas tal cual del enunciado, 3.4)

> Debe incluir exactamente estas cuatro figuras, con título, ejes etiquetados y leyenda:
>
> - Probabilidad de ejecución contra spread, marcando el punto donde la probabilidad llega a cero.
> - P&L acumulado a lo largo de los 10,000 trades, con las tres curvas (óptimo, estrecho, amplio)
>   en los mismos ejes.
> - Inventario acumulado a lo largo de los 10,000 trades, con los tres regímenes.
> - Histograma de la distribución de P&L final del análisis de Monte Carlo, con los tres
>   regímenes.

Más, de 3.5:

> Grafique el spread óptimo contra pi_i y compare el resultado numérico contra la predicción
> teórica vista en la Sesión 04.

Y el notebook, de 2.3:

> `notebooks/analysis.ipynb` — solo análisis y figuras, sin lógica.

## Cómo encaja con las convenciones del proyecto

- **Cada función devuelve un `Figure` y no guarda nada.** Guardar es de `main.py`, vía
  `guardar_figura(fig, nombre)`. Así el notebook las muestra inline y `main.py` las escribe a
  disco sin duplicar una sola línea. No metas `plt.show()` dentro de las funciones de `plots.py`.

- **`plots.py` no calcula nada.** Recibe los DataFrames y arrays que producen P1 y P2 y los
  dibuja. La única excepción razonable es `fig_prob_ejecucion`, que llama a `model.prob_ejecucion`
  sobre un `linspace` para trazar la curva; eso es evaluar una función existente, no implementar
  lógica nueva.

- **El notebook importa de `src/` y nada más.** Ni una definición de función, ni una fórmula
  inline, ni un `np.random` suelto. Un notebook con lógica se califica Deficiente en Estructura
  del Proyecto; es una penalización nombrada explícitamente en el enunciado.

- **El notebook debe correr de arriba a abajo con "Restart & Run All"** después de un
  `python main.py` limpio. Se guarda con las salidas ejecutadas, para que el profesor pueda
  abrirlo sin correrlo.

- **Figura 1, probabilidad de ejecución contra spread.** El eje x es el medio spread `s`, la
  desviación respecto a S0, porque así está definida `prob_ejecucion(s)` en el enunciado. Dilo en
  la etiqueta del eje: la palabra "spread" a secas es ambigua y el profesor va a preguntar. Marca
  `s = 6.25` con una línea vertical y una anotación. Vale la pena marcar también dónde caen los
  tres regímenes: se ve de un golpe que el "amplio" (s = 1.50) está lejísimos del punto donde la
  ejecución se anula, y eso conecta directo con la advertencia de rentabilidad por trade.

- **Figuras 2 y 3, P&L e inventario acumulado.** Tres curvas en los mismos ejes, con colores
  consistentes entre las dos figuras y entre todas las del proyecto: define un diccionario
  `COLORES = {'optimo': ..., 'estrecho': ..., 'amplio': ...}` al inicio de `plots.py` y úsalo
  siempre. Que el régimen óptimo sea azul en una figura y naranja en otra confunde en la
  exposición. En la Figura 3, línea horizontal en cero: el inventario es un desbalance con signo
  y el cero es la referencia.

- **Figura 4, histograma del Monte Carlo.** Tres distribuciones en los mismos ejes, con
  transparencia (`alpha` alrededor de 0.6) y **el mismo binning para las tres** (calcula los
  bordes una vez sobre el rango conjunto). Con bins distintos por serie las alturas no son
  comparables y la figura miente. Marca el cero con una vertical: la probabilidad de pérdida es
  exactamente la masa a la izquierda de esa línea, así que la figura responde sola una de las
  preguntas de análisis.

- **Figura 5, sensibilidad.** Spread óptimo contra pi_i, con los tres puntos calculados y
  marcados. Con solo tres valores de pi_i, unir con línea recta sugiere una linealidad que no
  está demostrada: usa marcadores visibles y, si unes, línea punteada. La curva teórica está
  bloqueada por el punto abierto O3. No inventes una fórmula para tener algo que graficar.

- **Estándar mínimo de toda figura:** título, etiqueta en ambos ejes con unidades, leyenda cuando
  hay más de una serie, `figsize` de al menos (10, 6), fuente de al menos 11 pt y grid tenue. Sin
  estilos exóticos ni fondos de color. La rúbrica pide legibilidad desde el fondo del salón, no
  diseño.

- **El notebook es también el guion de la exposición.** Estructúralo con encabezados en markdown
  siguiendo el orden sugerido de la presentación: planteamiento, optimización, simulación y
  comparación, sensibilidad y conclusiones. Cada figura va acompañada de dos o tres líneas que
  digan **qué se ve y por qué pasa**. "Se observa que el régimen estrecho pierde dinero" describe;
  "el régimen estrecho pierde porque su medio spread de 0.15 es menor que la pérdida esperada por
  trade informado" explica. La rúbrica distingue explícitamente entre las dos cosas: describir
  sin explicar es "Regular".

## Entregable

- `src/plots.py` con las seis funciones del contrato.
- `notebooks/analysis.ipynb`, ejecutado de principio a fin y guardado con salidas.
- Ninguna figura guardada a mano en el repo: todas se regeneran con `python main.py`.
- Pull Request a `main` con Gonzalo como reviewer, fusionado después de P1 y P2.

## Checklist

- [ ] Las cinco funciones de figura devuelven `Figure` y ninguna llama a `savefig` o `show`
- [ ] `grep -n "def \|scipy" notebooks/analysis.ipynb` no muestra definiciones ni cálculos
- [ ] Las cinco figuras tienen título, ambos ejes etiquetados con unidades, y leyenda si aplica
- [ ] Los colores por régimen son idénticos en las figuras 2, 3 y 4
- [ ] Figura 1: el eje x dice explícitamente que es el medio spread, y `s = 6.25` está marcado
- [ ] Figura 3: hay línea horizontal en inventario cero
- [ ] Figura 4: los tres histogramas comparten los mismos bordes de bin y el cero está marcado
- [ ] Figura 5: tres puntos marcados, sin curva teórica inventada
- [ ] Ninguna figura tiene texto por debajo de 11 pt
- [ ] "Restart & Run All" del notebook corre sin errores tras un `python main.py` limpio
- [ ] Cada figura del notebook tiene 2 o 3 líneas de markdown que explican por qué, no solo qué
- [ ] El notebook no contiene ni una fórmula inline ni una definición de función
- [ ] Milca puede explicar cada figura sin verla, incluyendo qué cambiaría si pi_i subiera a 0.7
