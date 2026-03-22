import csv
import os
from datetime import datetime, timedelta

import os

FILE = "teletrabajo_registro.csv"
ESTADOS = ["oficina", "teletrabajo", "festivo", "vacaciones"]


def init_file():
    if not os.path.exists(FILE):
        with open(FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["fecha", "estado"])


def leer_datos():
    datos = {}
    if os.path.exists(FILE):
        with open(FILE, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                fecha = row.get("fecha", "").strip()
                estado = row.get("estado", "").strip()
                if fecha and estado:
                    datos[fecha] = estado
    return datos


def guardar_datos(datos):
    with open(FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["fecha", "estado"])
        for fecha, estado in sorted(datos.items()):
            writer.writerow([fecha, estado])


def validar_fecha(fecha_txt):
    try:
        datetime.strptime(fecha_txt, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def pedir_fecha(mensaje="Fecha (YYYY-MM-DD): "):
    while True:
        fecha = input(mensaje).strip()
        if validar_fecha(fecha):
            return fecha
        print("Fecha no valida. Usa formato YYYY-MM-DD")


def pedir_estado():
    print("Selecciona estado:")
    for i, estado in enumerate(ESTADOS, start=1):
        print(f"{i}. {estado}")

    while True:
        opcion = input("Opcion: ").strip()
        if opcion.isdigit():
            indice = int(opcion) - 1
            if 0 <= indice < len(ESTADOS):
                return ESTADOS[indice]
        print("Opcion no valida, intenta de nuevo")


def obtener_periodo_trimestre(fecha):
    trimestre = ((fecha.month - 1) // 3) + 1
    mes_inicio = (trimestre - 1) * 3 + 1
    inicio = fecha.replace(month=mes_inicio, day=1)
    if mes_inicio + 2 == 12:
        fin = fecha.replace(month=12, day=31)
    else:
        primer_dia_siguiente = fecha.replace(month=mes_inicio + 3, day=1)
        fin = primer_dia_siguiente - timedelta(days=1)
    return trimestre, inicio, fin


def contar_periodo(datos, inicio, fin):
    tt = 0
    of = 0
    fest = 0
    vac = 0

    actual = inicio
    while actual <= fin:
        fecha_str = actual.strftime("%Y-%m-%d")
        estado = datos.get(fecha_str)

        if estado == "teletrabajo":
            tt += 1
        elif estado == "oficina":
            of += 1
        elif estado == "festivo":
            fest += 1
        elif estado == "vacaciones":
            vac += 1

        actual += timedelta(days=1)

    laborables_registrados = tt + of
    return {
        "teletrabajo": tt,
        "oficina": of,
        "festivo": fest,
        "vacaciones": vac,
        "laborables_registrados": laborables_registrados,
    }


def mostrar_resumen_periodo(nombre, datos_periodo):
    tt = datos_periodo["teletrabajo"]
    of = datos_periodo["oficina"]
    fest = datos_periodo["festivo"]
    vac = datos_periodo["vacaciones"]
    total = datos_periodo["laborables_registrados"]

    print(f"\n--- {nombre} ---")
    print(f"Teletrabajo: {tt}")
    print(f"Oficina: {of}")
    print(f"Festivo: {fest}")
    print(f"Vacaciones: {vac}")

    if total > 0:
        pct_tt = (tt / total) * 100
        pct_of = (of / total) * 100
        print(f"% teletrabajo: {pct_tt:.2f}%")
        print(f"% oficina: {pct_of:.2f}%")

        if pct_tt < 60:
            print("Estado objetivo: por debajo del 60% de teletrabajo")
        elif pct_tt > 60:
            print("Estado objetivo: por encima del 60% de teletrabajo")
        else:
            print("Estado objetivo: exacto 60/40")
    else:
        print("Sin dias laborables registrados")


def estimacion_semanal(datos):
    hoy = datetime.today()
    inicio_semana = hoy - timedelta(days=hoy.weekday())
    fin_semana = inicio_semana + timedelta(days=6)

    resumen = contar_periodo(datos, inicio_semana, fin_semana)
    tt = resumen["teletrabajo"]
    of = resumen["oficina"]
    fest = resumen["festivo"]
    vac = resumen["vacaciones"]
    total_registrado = tt + of
    dias_no_laborables = fest + vac

    print("\n--- RECOMENDACION SEMANAL ---")
    print(
        f"Semana actual: {inicio_semana.strftime('%Y-%m-%d')} a {fin_semana.strftime('%Y-%m-%d')}"
    )

    if total_registrado > 0:
        pct_tt = (tt / total_registrado) * 100
        print(f"Teletrabajo actual: {pct_tt:.2f}%")
    else:
        print("Teletrabajo actual: sin datos laborables")

    dias_semana = 7
    dias_pendientes = 0
    dias_pendientes_laborables = 0

    for i in range(dias_semana):
        dia = inicio_semana + timedelta(days=i)
        fecha_str = dia.strftime("%Y-%m-%d")
        if fecha_str not in datos:
            dias_pendientes += 1
            if dia.weekday() < 5:
                dias_pendientes_laborables += 1

    print(f"Dias laborables registrados: {total_registrado}")
    print(f"Dias no laborables registrados: {dias_no_laborables}")
    print(f"Dias sin registrar: {dias_pendientes}")
    print(f"Dias laborables sin registrar: {dias_pendientes_laborables}")

    if total_registrado == 0:
        print("Aun no hay base suficiente para calcular una recomendacion precisa")
        print("Recomendacion: registra la semana y apunta al objetivo 60% teletrabajo / 40% oficina")
        return

    total_final_estimado = total_registrado + dias_pendientes_laborables
    objetivo_tt_final = round(total_final_estimado * 0.6)
    recomendados_tt = max(0, objetivo_tt_final - tt)

    if dias_pendientes_laborables == 0:
        objetivo_actual = round(total_registrado * 0.6)
        diferencia = tt - objetivo_actual
        if diferencia < 0:
            print(f"Esta semana te han faltado {abs(diferencia)} dias de teletrabajo para el objetivo")
        elif diferencia > 0:
            print(f"Esta semana te has pasado en {diferencia} dias de teletrabajo")
        else:
            print("Esta semana has quedado justo en el objetivo 60/40")
        return

    recomendados_of = max(0, dias_pendientes_laborables - recomendados_tt)

    if recomendados_tt > dias_pendientes_laborables:
        recomendados_tt = dias_pendientes_laborables
        recomendados_of = 0

    print("Recomendacion para lo que queda de semana:")
    print(f"- Teletrabajo: {recomendados_tt} dia(s)")
    print(f"- Oficina: {recomendados_of} dia(s)")


def stats(datos):
    hoy = datetime.today()

    inicio_mes = hoy.replace(day=1)
    if hoy.month == 12:
        fin_mes = hoy.replace(month=12, day=31)
    else:
        primer_dia_mes_siguiente = hoy.replace(month=hoy.month + 1, day=1)
        fin_mes = primer_dia_mes_siguiente - timedelta(days=1)

    trimestre, inicio_trimestre, fin_trimestre = obtener_periodo_trimestre(hoy)

    print("\n==============================")
    print("ESTADISTICAS")
    print("==============================")

    mostrar_resumen_periodo(
        f"MES ACTUAL ({hoy.strftime('%Y-%m')})",
        contar_periodo(datos, inicio_mes, fin_mes),
    )

    mostrar_resumen_periodo(
        f"TRIMESTRE ACTUAL (T{trimestre} {hoy.year})",
        contar_periodo(datos, inicio_trimestre, fin_trimestre),
    )

    estimacion_semanal(datos)
    print("")


def mostrar_hoy(datos):
    hoy = datetime.today().strftime("%Y-%m-%d")

    print("\n==============================")
    print("REGISTRO DE HOY")
    print("==============================")

    if hoy in datos:
        print(f"Hoy ({hoy}) tienes: {datos[hoy]}")
        mod = input("Quieres modificarlo? (s/n): ").strip().lower()
        if mod == "s":
            datos[hoy] = pedir_estado()
            guardar_datos(datos)
            print("Dato actualizado")
    else:
        print(f"Hoy ({hoy}) no tiene registro")
        datos[hoy] = pedir_estado()
        guardar_datos(datos)
        print("Dato guardado")


def anadir_dato(datos):
    fecha = pedir_fecha("Fecha (YYYY-MM-DD): ")
    datos[fecha] = pedir_estado()
    guardar_datos(datos)
    print("Dato guardado")


def modificar_dato(datos):
    fecha = pedir_fecha("Fecha a modificar (YYYY-MM-DD): ")
    if fecha in datos:
        print(f"Valor actual: {datos[fecha]}")
        datos[fecha] = pedir_estado()
        guardar_datos(datos)
        print("Dato actualizado")
    else:
        print("No existe esa fecha")


def menu(datos):
    while True:
        print("\n--- MENU ---")
        print("1. Anadir dato")
        print("2. Modificar dato")
        print("3. Ver estadisticas")
        print("ESC. Salir")

        opcion = input("Opcion: ").strip().lower()

        if opcion == "1":
            anadir_dato(datos)
        elif opcion == "2":
            modificar_dato(datos)
        elif opcion == "3":
            stats(datos)
        elif opcion == "esc":
            guardar_datos(datos)
            print("Saliendo...")
            break
        else:
            print("Opcion no valida")


def main():
    init_file()
    datos = leer_datos()
    mostrar_hoy(datos)
    stats(datos)
    menu(datos)


if __name__ == "__main__":
    main()
