# Contabilidad del P&L — casos frontera

Documento de referencia compartido: aplica a P2 y a las pruebas que verifican la simulación.

**La regla general y la tabla de las cuatro situaciones están en el `CLAUDE.md` de la raíz,
sección "Contabilidad del P&L". No se repiten aquí.** Este archivo cubre solo los dos casos que
la tabla no resuelve y que hay que decidir explícitamente al escribir el simulador.

## El informado que no opera

Si `B <= P <= A`, el trader informado no tiene incentivo para operar de ningún lado: el ask está
por encima del valor verdadero y el bid por debajo.

Convención por defecto: se registra la fila con `ejecutado=False`, `direccion='ninguna'`,
`pnl=0.0`, `delta_inventario=0`.

Las alternativas se descartaron y conviene poder decir por qué:

- **Re-samplear P hasta que caiga fuera de la banda** sesga la distribución del valor verdadero.
  Ya no estarías simulando una Erlang(60, 3) sino una Erlang truncada, y el P&L esperado deja de
  corresponder al modelo.
- **Forzar una dirección al azar** le regala P&L positivo al formador en trades donde el modelo
  dice que no debería haber operación, e infla artificialmente el resultado.

Esto choca de frente con la frase del enunciado "la simulación fuerza la ejecución de un trade en
cada iteración", y por eso es el **punto abierto O2** del `CLAUDE.md`. Implementa la convención
por defecto, pero deja el comportamiento aislado en una sola rama del código para que cambiarlo
cuando el profesor responda sea trivial.

## La ejecución forzada y el sesgo del régimen amplio

Con `forzar_ejecucion=True`, que es el default que pide el enunciado, el trader de liquidez
siempre opera y se ignora `prob_ejecucion(s)`.

La consecuencia es la que el enunciado obliga a declarar: los resultados son rentabilidad **por
trade**, no por unidad de tiempo. Un spread absurdamente amplio se ve artificialmente bien bajo
esa métrica, porque en la realidad casi nunca se ejecutaría. Con los números del Lab: en el
régimen amplio cada trade de liquidez deja 1.50 al formador, pero la probabilidad de ejecución en
ese medio spread de 1.50 es de 0.38, así que en tiempo real llegarían bastantes menos trades de
los que la simulación asume.

Con `forzar_ejecucion=False` la ejecución del trader de liquidez se sortea contra
`prob_ejecucion(s)`, y entonces sí se cumple que el P&L promedio por iteración converge a
Pi(A,B). Esa versión existe por dos razones:

1. Es la única forma de **verificar** que el simulador y el modelo son el mismo objeto. La prueba
   correspondiente vive en `tests/test_model.py` (parte P4) y compara el promedio simulado contra
   `utilidad_esperada` con tolerancia relativa del 2%.
2. Correr las dos versiones y poner los números lado a lado convierte la advertencia obligatoria
   del enunciado en un resultado propio del equipo, en vez de una disculpa copiada. La rúbrica
   distingue explícitamente entre describir un efecto y mostrarlo.

El régimen óptimo y el estrecho también cambian al desactivar la ejecución forzada, pero mucho
menos que el amplio, porque sus spreads son más chicos y su probabilidad de ejecución más alta.
Esa diferencia en la magnitud del cambio es el resultado interesante.
