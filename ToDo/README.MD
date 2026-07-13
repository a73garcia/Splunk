# Task Planner Pro

## Descripción

Task Planner Pro es una aplicación de escritorio desarrollada en
**Python + Tkinter** para gestionar tareas, proyectos y seguimiento
diario, almacenando la información en un archivo **Excel (.xlsx)**
mediante **openpyxl**.

## Características

-   Calendario de tareas.
-   Dashboard de indicadores.
-   Gestión de responsables.
-   Seguimiento diario.
-   Exportación a Excel, CSV y PDF.
-   Integración con Power BI.
-   Copias de seguridad.
-   Vista Kanban.
-   Vista Gantt.

## Estructura

``` text
TaskPlannerPro/
│
├── TaskPlanner.py
├── ui.py
├── config.py
├── models.py
├── excel_manager.py
├── metrics_manager.py
├── powerbi_manager.py
├── report_manager.py
├── backup_manager.py
├── notification_manager.py
├── dashboard_panel.py
├── calendar_panel.py
├── kanban_panel.py
├── gantt_panel.py
├── dialogs.py
├── requirements.txt
├── LICENSE
└── README.md
```

## Requisitos

-   Python 3.11+
-   openpyxl

## Ejecución

``` bash
python TaskPlanner.py
```

## Plan de desarrollo

1.  Configuración
2.  Modelos
3.  Gestor Excel
4.  Interfaz
5.  Paneles
6.  Informes
7.  Power BI
8.  Pruebas
