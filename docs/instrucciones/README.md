# Instrucciones del proyecto

Esta carpeta es material de trabajo del equipo, no un entregable evaluado. Contiene las
instrucciones detalladas de cada parte del Lab y las convenciones compartidas.

Las convenciones globales viven en el `CLAUDE.md` de la raíz, que Claude Code carga en cada
sesión: reglas duras, parámetros del caso base, **contratos entre módulos**, tabla de
contabilidad del P&L, reparto, Git y puntos abiertos. Esas no se duplican aquí. En esta carpeta
va solo lo que hace falta cuando se está trabajando en una parte concreta.

## Qué hay aquí

| Archivo | Cuándo leerlo |
|---|---|
| `contabilidad_pnl.md` | Antes de tocar `src/simulation.py` o sus pruebas. |
| `P1_modelo.md` | Al trabajar en `src/model.py`. Responsable: Gonzalo. |
| `P2_simulacion.md` | Al trabajar en `src/simulation.py`. Responsable: Milca. |
| `P3_figuras.md` | Al trabajar en `src/plots.py` o el notebook. Responsable: Milca. |
| `P4_infra.md` | Al trabajar en pruebas, `main.py`, README o requirements. Responsable: Gonzalo. |
| `definicion_de_terminado.md` | Antes de dar el Lab por cerrado. |

## Cómo se usan

Al iniciar una sesión de trabajo, identifica en qué parte estás (por la rama actual o por los
archivos que vas a tocar) y lee el archivo correspondiente. No hace falta leer los cuatro:
cada uno es autocontenido salvo por lo que hereda del `CLAUDE.md`.

Cada archivo de parte tiene la misma estructura: las tareas copiadas tal cual del enunciado,
cómo encajan con las convenciones del proyecto, el entregable exacto, y un checklist donde cada
punto se puede marcar como cierto o falso sin interpretación.

## Si algo aquí queda desactualizado

Estos archivos son la fuente de verdad sobre cómo se hace cada parte. Si durante la
implementación se toma una decisión distinta a lo que dice el archivo, se actualiza el archivo
en el mismo commit. Un documento que miente es peor que no tenerlo.
