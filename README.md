# Lab01 — Cotizaciones óptimas de un formador de mercado

Laboratorio 01 de Microestructuras y Sistemas de Trading (IT1731B, ITESO). Equipo 6.

> **Estado: en construcción.** Solo existe la estructura del repositorio. El contenido
> completo de este README (integrantes con usuario de GitHub, las cinco preguntas de
> análisis con cifras propias, la advertencia de interpretación y la declaración de uso
> de IA) es entregable de la parte P4 y requiere resultados que todavía no existen.
> Ver `docs/instrucciones/P4_infra.md`.

## Estructura

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
    ├── figuras/               # salida de plots.py, la crea main.py
    └── instrucciones/         # instrucciones por parte, uso interno del equipo
```

## Instalación

Requiere Python 3.12.

```bash
python3 -m venv .venv
source .venv/bin/activate          # en Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Reproducir los resultados

```bash
python main.py
```

## Semilla

`SEED = 42`, definida una sola vez en `src/model.py` e importada por los demás módulos.
Ningún módulo define su propia semilla local. El mecanismo exacto está pendiente de
confirmar (punto abierto O7 del `CLAUDE.md`).

## Integrantes

| Integrante | GitHub |
|------------|--------|
| Gonzalo    |        |
| Milca      |        |
