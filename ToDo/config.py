from pathlib import Path

APP_NAME="Task Planner Pro"
APP_VERSION="2.0.0"

BASE_DIR=Path(__file__).resolve().parent
DATA_DIR=BASE_DIR/"data"
BACKUP_DIR=BASE_DIR/"backup"
EXPORT_DIR=BASE_DIR/"export"
REPORTS_DIR=BASE_DIR/"reports"

for d in (DATA_DIR,BACKUP_DIR,EXPORT_DIR,REPORTS_DIR):
    d.mkdir(parents=True, exist_ok=True)

EXCEL_FILE=DATA_DIR/"Tareas.xlsx"

SHEET_TASKS="Tareas"
SHEET_HISTORY="Seguimiento"
SHEET_METRICS="Metricas"
SHEET_CATEGORIES="Categorias"
SHEET_OWNERS="Responsables"
SHEET_CALENDAR="Calendario"
SHEET_CONFIG="Configuracion"

DATE_FORMAT="%d/%m/%Y"
DATETIME_FORMAT="%d/%m/%Y %H:%M:%S"

STATUS_PENDING="Pendiente"
STATUS_PROGRESS="En curso"
STATUS_BLOCKED="Bloqueada"
STATUS_DONE="Finalizada"

PRIORITY_LOW="Baja"
PRIORITY_MEDIUM="Media"
PRIORITY_HIGH="Alta"
PRIORITY_CRITICAL="Crítica"
