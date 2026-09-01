# P4 — Pruebas, orquestación y reporte

**Responsable: Gonzalo. Rama: `feat/p4-infra`.**
**Archivos: `tests/test_model.py`, `main.py`, `README.md`, `requirements.txt`, `.gitignore`.**

Hereda todo lo del `CLAUDE.md` de la raíz, incluidas las firmas congeladas y la tabla de
contabilidad del P&L. Para las pruebas que verifican la simulación, lee también
`contabilidad_pnl.md`.

Esta parte concentra tres de las penalizaciones explícitas del enunciado: repositorio que no
corre con el comando documentado (−10), README incompleto (criterio A) y declaración de uso de IA
ausente (criterio D). Son puntos que se pierden sin equivocarse en nada matemático.

Se fusiona al final, porque `main.py` importa de los tres módulos.

## Las tareas (copiadas tal cual del enunciado)

De 3.6:

> El archivo `tests/test_model.py` debe contener al menos tres pruebas que se ejecuten con pytest:
>
> - Que pi_LB(s) y pi_LS(s) nunca devuelvan un valor negativo.
> - Que la pérdida esperada frente a informados sea decreciente en A (verificar con al menos tres
>   valores de A).
> - Que con pi_i = 0 el spread óptimo coincida con el resultado analítico del monopolista, que es
>   s* = 0.50/0.08 por lado.

De 2.3:

> `main.py` debe ejecutar el proyecto completo con un solo comando: `python main.py`
>
> `README.md` debe contener: nombre de los integrantes, descripción del proyecto en un párrafo,
> instrucciones de instalación, y el comando exacto para reproducir todos los resultados.
>
> La semilla aleatoria debe estar fijada (`np.random.seed`) y documentada en el README.

De la sección 4, las cinco preguntas de análisis, que van en el README y en la presentación:

1. ¿Por qué los traders informados generan la necesidad de un spread? Explíquelo con sus cifras
   del régimen estrecho.
2. ¿Cómo cambia el costo de selección adversa conforme se amplía el spread? Muéstrelo, no lo
   afirme.
3. ¿Cuál régimen acumula el mayor desbalance de inventario y por qué? ¿A qué riesgo real lo
   expone eso, que el modelo no captura?
4. ¿Cómo se comporta el spread óptimo al variar pi_i? ¿Coincide con la teoría?
5. Mencione tres limitaciones de este modelo para un formador de mercado real.

De la sección 6:

> El README debe incluir una sección breve indicando en qué partes del proyecto se usó asistencia
> de IA.

## Cómo encaja con las convenciones del proyecto

### Pruebas

- **Prueba 1, no negatividad.** Evalúa `prob_ejecucion` sobre un `linspace` que rebase
  holgadamente el punto de truncamiento (por ejemplo de 0 a 20) y verifica que ningún valor es
  negativo. Prueba también el escalar y el array: si la función no está vectorizada, esta prueba
  lo detecta, y P3 la necesita vectorizada para la Figura 1.

- **Prueba 2, monotonía de la pérdida.** La pérdida esperada frente a informados del lado del ask
  es decreciente en A: mientras más arriba cotizas, menos te pega el informado que compra.
  Verifica con al menos tres valores crecientes de A (por ejemplo 20.0, 21.0, 22.0) que la
  sucesión es estrictamente decreciente. Usa el primer elemento de la tupla que devuelve
  `perdida_informados`, no la suma de ambos lados, porque el lado del bid se mueve en dirección
  contraria.

- **Prueba 3, el monopolista, con el matiz del punto abierto O1.** Escríbela verificando las dos
  cosas: que el medio spread es `0.50/(2*0.08) = 3.125` con tolerancia 1e-3, y que el spread
  total es `0.50/0.08 = 6.25` con la misma tolerancia. Son la misma afirmación matemática bajo
  lecturas distintas de "por lado", y escrita así pasa sin importar cuál sea la intención del
  enunciado. Agrega un comentario con la derivación
  (`d/ds[(0.5 − 0.08s)s] = 0.5 − 0.16s = 0`), porque esa prueba es candidata directa a pregunta
  en la exposición.

- **Pruebas adicionales recomendadas**, aunque el enunciado pida solo tres: reproducibilidad de
  `simular_trades` con la misma semilla, y coherencia entre la simulación con
  `forzar_ejecucion=False` y `utilidad_esperada` (error relativo menor al 2%). Esta última es la
  única prueba del proyecto que verifica que el modelo y la simulación son el mismo objeto, y es
  lo que separa "pruebas triviales" de "pruebas significativas" en el criterio D. El enunciado
  nombra `tests/test_model.py` como archivo único, así que van ahí mismo.

### `main.py`

- Orquesta y reporta. **No implementa nada.**
- Secuencia: optimizar el caso base, imprimir bid, ask, spread y utilidad con dos decimales,
  construir los regímenes, simular los tres a 10,000 trades, correr el Monte Carlo, imprimir la
  tabla resumen, correr el análisis de sensibilidad, y generar y guardar las cinco figuras.
- Salida en consola legible y con encabezados de sección. El profesor va a correr esto una vez y
  lo que vea impreso es la primera impresión del trabajo.
- Crea `docs/figuras/` si no existe (`Path.mkdir(parents=True, exist_ok=True)`), para que el
  comando corra en un clon limpio.
- Usa el backend `Agg` de matplotlib, para que no intente abrir ventanas en una máquina sin
  entorno gráfico.
- Que corra en menos de un minuto. Si tarda más, casi siempre es que la simulación no está
  vectorizada; eso es problema de P2, no se resuelve bajando el número de corridas.

### `README.md`

- Integrantes: Gonzalo y Milca, con nombres completos y usuario de GitHub de cada uno.
- Un párrafo de descripción del proyecto.
- Instalación y comando exacto de reproducción, verificados en un clon limpio en carpeta nueva.
  No basta con que funcione en tu máquina.
- Semilla documentada: `SEED = 42`, dónde está definida y qué garantiza.
- Las cinco preguntas de análisis, cada una con **cifras propias del equipo**. Una respuesta
  genérica sin números es "Regular" por definición. Para la pregunta 2 el enunciado dice
  "muéstrelo, no lo afirme": ahí va la tabla de pérdida esperada frente a informados evaluada en
  varios spreads, no una frase.
- **La advertencia obligatoria de interpretación**: los resultados son rentabilidad por trade y
  no por unidad de tiempo, y por eso el régimen amplio se ve favorecido. Si la simulación con
  `forzar_ejecucion=False` está implementada, aquí es donde los dos números se ponen lado a lado
  y la advertencia deja de ser una disculpa y pasa a ser un resultado.
- Sección de uso de IA: qué partes se hicieron con asistencia, en qué consistió, y la afirmación
  de que ambos integrantes pueden explicar todo el código. Concreto y honesto; es un requisito
  del enunciado, no una confesión.
- Los puntos abiertos del `CLAUDE.md` que no se hayan resuelto se documentan aquí como supuestos
  declarados. Un supuesto declarado suma en el criterio B; el mismo supuesto sin declarar resta.

### `requirements.txt` y `.gitignore`

- `requirements.txt` con versiones fijadas (`numpy==`, `scipy==`, `pandas==`, `matplotlib==`,
  `pytest==`, `jupyter==`). Sin fijar versiones, "reproducible" es una promesa vacía.
- Es el único archivo donde se agregan dependencias, y lo edita solo P4.
- `.gitignore` con `__pycache__/`, `.ipynb_checkpoints/`, `.pytest_cache/`, entornos virtuales y
  `.DS_Store`. **No ignores `docs/instrucciones/`**: varias plantillas de Python ignoran carpetas
  de documentación, y si se cuela, Milca clona el repo sin ninguna instrucción. Verifícalo con
  `git status` después de crear la carpeta.
- Decide si `docs/figuras/` se versiona o se regenera siempre, y déjalo escrito en el README.

## Entregable

- `tests/test_model.py`, `main.py`, `README.md`, `requirements.txt`, `.gitignore`.
- Verificado en un clon limpio, en carpeta nueva, con entorno virtual nuevo.
- Pull Request a `main` con Milca como reviewer, fusionado al final.

## Checklist

- [ ] `pytest` pasa con las tres pruebas obligatorias, con nombres que dicen qué verifican
- [ ] La prueba del monopolista verifica medio spread 3.125 **y** spread total 6.25
- [ ] La prueba de monotonía usa al menos tres valores de A y solo el componente del ask
- [ ] La prueba de no negatividad evalúa escalar y array
- [ ] En un clon limpio, `pip install -r requirements.txt && python main.py` corre sin errores
- [ ] `main.py` no define ninguna función de modelo, simulación ni graficado
- [ ] `main.py` corre en menos de 60 segundos y genera las cinco figuras en `docs/figuras/`
- [ ] Dos corridas consecutivas de `main.py` imprimen exactamente los mismos números
- [ ] El README nombra a Gonzalo y a Milca con sus usuarios de GitHub
- [ ] Las cinco preguntas están respondidas y cada una contiene al menos un número del proyecto
- [ ] La advertencia de rentabilidad por trade vs por unidad de tiempo está en el README
- [ ] La sección de uso de IA existe y es específica
- [ ] `requirements.txt` tiene versiones fijadas con `==`
- [ ] `git check-ignore docs/instrucciones/README.md` no devuelve nada
- [ ] `git log --pretty='%an'` muestra commits de ambos integrantes, balanceados
- [ ] `docs/presentacion.pdf` está subida antes de la exposición
- [ ] Gonzalo puede explicar la simulación de Milca y Milca la optimización de Gonzalo
