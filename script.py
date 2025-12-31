# pip install openpyxl

import re
import calendar
from datetime import datetime, date
from openpyxl import load_workbook

FILE_PATH = r"C:\usuario\95677\local.xlsx"
SHEET_NAME = "Trimestral"

MONTHS = [m for m in calendar.month_name if m]  # January..December
MONTH_PATTERN = re.compile(r"\b(" + "|".join(MONTHS) + r")\b", flags=re.IGNORECASE)


def next_month_name(month_name: str) -> str:
    idx = {m.lower(): i for i, m in enumerate(MONTHS, start=1)}.get(month_name.lower())
    if not idx:
        return month_name
    next_idx = 1 if idx == 12 else idx + 1
    return MONTHS[next_idx - 1]


def replace_month_with_next(value):
    if value is None:
        return value

    if isinstance(value, (datetime, date)):
        return next_month_name(MONTHS[value.month - 1])

    if isinstance(value, str):
        m = MONTH_PATTERN.search(value)
        if not m:
            return value
        found = m.group(1)
        nxt = next_month_name(found)
        return MONTH_PATTERN.sub(nxt, value, count=1)

    return value


def main():
    # Libro para ESCRIBIR (mantiene fórmulas existentes; no copiamos fórmulas)
    wb = load_workbook(FILE_PATH)
    if SHEET_NAME not in wb.sheetnames:
        raise ValueError(f"No existe la hoja '{SHEET_NAME}'. Hojas: {wb.sheetnames}")
    ws = wb[SHEET_NAME]

    # Libro para LEER valores calculados (cacheados) de fórmulas
    wb_vals = load_workbook(FILE_PATH, data_only=True)
    ws_vals = wb_vals[SHEET_NAME]

    # 1) A2:A10 -> mes siguiente (inglés)
    for r in range(2, 11):
        ws[f"A{r}"].value = replace_month_with_next(ws[f"A{r}"].value)

    # 2) Copia C5:E10 -> C2:E7 como VALORES (nunca fórmulas)
    src_min_row, src_max_row = 5, 10
    dst_min_row = 2
    cols = ["C", "D", "E"]

    missing_cached = []

    for i in range(src_max_row - src_min_row + 1):  # 6 filas
        src_row = src_min_row + i
        dst_row = dst_min_row + i
        for col in cols:
            v = ws_vals[f"{col}{src_row}"].value  # resultado cacheado
            if v is None:
                # jamás copiar fórmula: si no hay valor cacheado, dejar en blanco
                ws[f"{col}{dst_row}"].value = None
                missing_cached.append(f"{col}{src_row}")
            else:
                ws[f"{col}{dst_row}"].value = v

    # Sobrescribe el mismo archivo
    wb.save(FILE_PATH)

    print(f"OK: actualizado {FILE_PATH} (hoja '{SHEET_NAME}').")
    if missing_cached:
        print(
            "AVISO: Algunas celdas origen no tenían resultado cacheado (data_only=True devolvió None).\n"
            "No se copió ninguna fórmula; esas celdas destino se dejaron en blanco.\n"
            f"Celdas afectadas: {', '.join(missing_cached)}\n"
            "Solución: abre el XLSX en Excel, recalcula si hace falta y guarda; luego ejecuta de nuevo."
        )


if __name__ == "__main__":
    main()