# P2 — Simulador de trades y análisis de Monte Carlo

**Responsable: Milca. Rama: `feat/p2-simulacion`. Archivo único: `src/simulation.py`.**

Hereda todo lo del `CLAUDE.md` de la raíz, incluidas las firmas congeladas y la tabla de
contabilidad del P&L. Además, antes de empezar se lee `contabilidad_pnl.md`, que tiene los dos
casos frontera de esta parte.

Esta parte se puede escribir **sin esperar a que P1 esté terminada**: se programa contra el
contrato de `src.model`, no contra su implementación. Mientras P1 no esté fusionada, se prueba
con un bid y un ask cualesquiera (por ejemplo 19.0 y 20.8) pasados como argumento. En ningún caso
`simulation.py` reimplementa la Erlang ni las constantes: las importa.

## Las tareas (copiadas tal cual del enunciado, 3.3)

> Debe simular 10,000 trades bajo tres regímenes de cotización:
>
> | Régimen | Bid | Ask | Propósito |
> |---|---|---|---|
> | Óptimo | Resultado de 3.2 | Resultado de 3.2 | Referencia del modelo |
> | Estrecho (tight) | 19.75 | 20.05 | Exposición a selección adversa |
> | Amplio (wide) | 18.40 | 21.40 | Protección excesiva |
>
> En cada trade debe registrar, como mínimo: P&L del trade, cambio de inventario, si el trader
> fue informado o de liquidez, y si fue compra o venta.
>
> **Análisis de Monte Carlo.** Adicionalmente, ejecute 1,000 corridas independientes de 1,000
> trades cada una, para los tres regímenes. Reporte para cada régimen: P&L promedio, desviación
> estándar del P&L y probabilidad de pérdida (proporción de corridas con P&L final negativo).

Y la advertencia obligatoria de la sección 4 del enunciado:

> La simulación fuerza la ejecución de un trade en cada iteración, por lo que los resultados
> representan rentabilidad por trade y no rentabilidad por unidad de tiempo. Un spread muy amplio
> que casi nunca se ejecutaría se ve favorecido bajo esta métrica.

## Cómo encaja con las convenciones del proyecto

- **La contabilidad del P&L está en el `CLAUDE.md` y en `contabilidad_pnl.md`, y no se negocia
  aquí.** Si te parece
  que otra convención tiene más sentido, plantéalo antes de implementarla, porque rompe la
  comparabilidad con Pi(A,B).

- **Sampleo del valor verdadero:** `distribucion_valor().rvs(size=n, random_state=rng)`, con la
  distribución importada de `src.model`. No construyas una Erlang nueva aquí.

- **Aleatoriedad:** un solo `rng = np.random.default_rng(seed)` por llamada a `simular_trades`, y
  todos los sorteos salen de ese generador. Nada de `np.random.seed` global disperso ni de
  `random.random()`. Con un `Generator` explícito la reproducibilidad se verifica corriendo dos
  veces y comparando los DataFrames.

- **Vectoriza, no iteres.** Son 10,000 trades por tres regímenes, más 3 millones de trades en el
  Monte Carlo. Un `for` en Python por trade hace que `python main.py` tarde minutos. Sortea tipo
  de trader, valores verdaderos y direcciones como arrays completos y resuelve el P&L con
  `np.where`. El inventario y el P&L acumulado salen con `cumsum`.

- **El Monte Carlo reutiliza `simular_trades`, no duplica su lógica.** Si te encuentras
  reescribiendo la contabilidad dentro de `monte_carlo`, la refactorización está mal hecha. Cada
  corrida usa una semilla derivada y determinista (`seed + i`), documentada.

- **`monte_carlo` devuelve solo el P&L final de cada corrida** (array de 1,000 floats). No
  devuelvas 1,000 DataFrames completos: son 3 millones de filas que no hacen falta para nada de
  lo que pide el enunciado.

- **Las tres métricas del Monte Carlo son sobre las corridas, no sobre los trades.** El P&L
  promedio es la media de los 1,000 P&L finales; la desviación estándar es la de esos mismos
  1,000 valores; la probabilidad de pérdida es la proporción de corridas con P&L final
  estrictamente negativo. Calcular la desviación estándar sobre los trades individuales da un
  número distinto y responde otra pregunta.

- **`forzar_ejecucion` es un parámetro, con `True` por defecto.** El default es lo que pide el
  enunciado. La versión con `False`, donde la ejecución del trader de liquidez se sortea contra
  `prob_ejecucion`, existe para poder mostrar el sesgo del régimen amplio en vez de solo
  mencionarlo.

- **El informado dentro de la banda es el punto abierto O2.** Implementa la convención por
  defecto (fila con `ejecutado=False`, `pnl=0.0`, `delta_inventario=0`) y deja el comportamiento
  aislado en una sola rama del código, para que cambiarlo cuando el profesor responda sea
  trivial.

- **Dirección del trader de liquidez:** sorteo 50/50 entre compra y venta. Es simétrico y es lo
  que corresponde a un flujo no informado. Documéntalo como supuesto explícito: la rúbrica premia
  declarar supuestos y castiga dejarlos implícitos.

- **`direccion` es desde la perspectiva del trader que llega**, no del formador de mercado. Si el
  trader compra, el formador vende y su inventario baja. Confundir el signo del inventario es el
  error más común en esta parte y sale a la vista en la Figura 3.

## Entregable

- `src/simulation.py`, con las seis funciones del contrato y docstrings en las principales.
- Sin figuras, sin prints, sin lógica del modelo, sin `if __name__ == '__main__'`.
- Si necesitas una dependencia nueva, avísale a Gonzalo: `requirements.txt` es de P4.
- Pull Request a `main` con Gonzalo como reviewer.

## Checklist

- [ ] `simular_trades` devuelve exactamente las 10 columnas del contrato, en ese orden
- [ ] Dos llamadas con la misma semilla devuelven DataFrames idénticos (`df1.equals(df2)`)
- [ ] Dos llamadas con semillas distintas devuelven DataFrames distintos
- [ ] La proporción de `tipo_trader == 'informado'` en 10,000 trades está entre 0.38 y 0.42
- [ ] `delta_inventario` es -1 cuando `direccion == 'compra'` y +1 cuando es `'venta'`, siempre
- [ ] `inventario` es el `cumsum` de `delta_inventario` y `pnl_acumulado` el de `pnl`
- [ ] Todo `pnl` de filas informadas y ejecutadas es menor o igual a 0
- [ ] Todo `pnl` de liquidez en el régimen amplio es exactamente 1.50
- [ ] Con `forzar_ejecucion=False`, el P&L promedio por iteración en el régimen óptimo coincide
      con `utilidad_esperada(ask, bid)` con error relativo menor al 2%
- [ ] `construir_regimenes` devuelve las tres llaves con los valores del enunciado sin redondear
- [ ] `monte_carlo` devuelve un array de forma (1000,) y no un DataFrame
- [ ] `resumen_monte_carlo` devuelve 3 filas con las cuatro columnas exactas
- [ ] `prob_perdida` está entre 0 y 1 en los tres regímenes
- [ ] El bloque completo (3 regímenes por 10,000 más el Monte Carlo) corre en menos de 30 segundos
- [ ] Milca puede explicar sin ver el código por qué el P&L de liquidez se marca contra S0 y el
      de informados contra P, y por qué el régimen amplio se ve mejor de lo que sería en realidad
