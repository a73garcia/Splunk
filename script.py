#!/usr/bin/env python3
# pip install openpyxl

import argparse
import re
import calendar
from datetime import datetime, date
from openpyxl import load_workbook

MONTHS = [m for m in calendar.month_name if m]  # January..December
MONTH_PATTERN = re.compile(r"\b(" + "|".join(MONTHS) + r")\b", flags=re.IGNORECASE)


def prev_month_name(month_name: str) -> str:
    idx = {m.lower(): i for i, m in enumerate(MONTHS, start=1)}.get(month_name.lower())
    if not idx:
        return month_name
    prev_idx = 12 if idx == 1 else idx - 1
    return MONTHS[prev_idx - 1]


def replace_month_with_previous(value):
    if value is None:
        return value
    if isinstance(value, (datetime, date)):
        return prev_month_name(MONTHS[value.month - 1])
    if isinstance(value, str):
        m = MONTH_PATTERN.search(value)
        if not m:
            return value
        found = m.group(1)
        prev = prev_month_name(found)
        return MONTH_PATTERN.sub(prev, value, count=1)
    return value


def main():
    parser = argparse.ArgumentParser(
        description="A2:A10 -> mes anterior (EN). Copia C5:E10 -> C2:E7 PEGANDO SOLO VALORES (nunca fórmulas)."
    )
    parser.add_argument("input_xlsx", help="Ruta del .xlsx de entrada")
    parser.add_argument("-o", "--output", default=None, help="Ruta del .xlsx de salida (por defecto añade _mod)")
    parser.add_argument("-s", "--sheet", default=None, help="Nombre de hoja (por defecto, activa)")
    args = parser.parse_args()

    in_path = args.input_xlsx
    out_path = args.output or (
        in_path[:-5] + "_mod.xlsx" if in_path.lower().endswith(".xlsx") else in_path + "_mod.xlsx"
    )

    # Libro para ESCRIBIR (mantiene fórmulas donde existan, pero NO las copiaremos)
    wb = load_workbook(in_path)
    ws = wb[args.sheet] if args.sheet else wb.active

    # Libro para LEER resultados cacheados de fórmulas
    wb_vals = load_workbook(in_path, data_only=True)
    ws_vals = wb_vals[args.sheet] if args.sheet else wb_vals.active

    # 1) A2:A10 -> mes anterior (inglés)
    for r in range(2, 11):
        ws[f"A{r}"].value = replace_month_with_previous(ws[f"A{r}"].value)

    # 2) C5:E10 -> C2:E7 (SIEMPRE valores)
    src_min_row, src_max_row = 5, 10   # 6 filas
    dst_min_row = 2
    cols = ["C", "D", "E"]

    missing_cached = []  # para avisar si faltan valores cacheados

    for i in range(src_max_row - src_min_row + 1):  # 0..5
        src_row = src_min_row + i
        dst_row = dst_min_row + i
        for col in cols:
            v = ws_vals[f"{col}{src_row}"].value  # valor (resultado), nunca fórmula
            if v is None:
                # NO copiamos fórmula jamás: dejamos vacío y registramos aviso
                missing_cached.append(f"{col}{src_row}")
                ws[f"{col}{dst_row}"].value = None
            else:
                ws[f"{col}{dst_row}"].value = v

    wb.save(out_path)

    print(f"OK. Guardado: {out_path}")
    if missing_cached:
        print(
            "AVISO: Algunas celdas origen parecen no tener resultado cacheado (data_only=True devolvió None).\n"
            "No se ha copiado ninguna fórmula; esas celdas destino se dejaron en blanco.\n"
            f"Celdas afectadas: {', '.join(missing_cached)}\n"
            "Solución: abre el XLSX en Excel, recalcula (si hace falta) y guarda; luego ejecuta de nuevo."
        )


if __name__ == "__main__":
    main()