#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Monitor ESA - Interfaz gráfica (Tkinter)

Convierte el monitor en consola a una aplicación de escritorio con:
- Pantalla resumen por cluster
- Estado de nodos
- Salud operativa
- Incidencias y hallazgos
- Picos históricos
- Refresco automático y manual
- Exportación CSV por cluster

Requisitos:
- Python 3.10+
- requests

Archivo de credenciales:
credentials.env
GLOBAL_USERNAME=usuario
GLOBAL_PASSWORD=clave
"""

import os
import csv
import threading
import queue
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Tuple
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
import urllib3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# =========================================================
# CONFIG
# =========================================================
APP_TITLE = "Monitor Colas ESA - GUI"
CREDENTIALS_FILE = "credentials.env"
CSV_OUTPUT_DIR = "csv_clusters_gui"

TIMEOUT_SECONDS = 12
MAX_WORKERS = 12
RETRIES = 2

REFRESH_SECONDS_NORMAL = 600
REFRESH_SECONDS_INCIDENT = 180

VERIFY_SSL = False
if not VERIFY_SSL:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

GROUPS = [
    {"cluster": "Europa",       "pattern": "https://xxx{idx}yyy", "start": 1, "end": 20},
    {"cluster": "America",      "pattern": "https://xxx{idx}zzz", "start": 1, "end": 20},
    {"cluster": "Brasil",       "pattern": "https://xxx{idx}zzz", "start": 1, "end": 20},
    {"cluster": "Aplicaciones", "pattern": "https://xxx{idx}yyy", "start": 1, "end": 20},
]


CLUSTER_FARM_MAP = {
    "Europa": {
        "F10": {"ESA01", "ESA03", "ESA05", "ESA07", "ESA09", "ESA11", "ESA13", "ESA15", "ESA17", "ESA19"},
        "F11": {"ESA02", "ESA04", "ESA06", "ESA08", "ESA10", "ESA12", "ESA14", "ESA16", "ESA18", "ESA20"},
    },
    "America": {
        "F4": {"ESA01", "ESA02", "ESA03", "ESA04", "ESA05", "ESA06", "ESA07", "ESA08", "ESA09", "ESA10"},
        "F5": {"ESA11", "ESA12", "ESA13", "ESA14", "ESA15", "ESA16", "ESA17", "ESA18", "ESA19", "ESA20"},
    },
    "Brasil": {
        "F4": {"ESA01", "ESA02", "ESA03", "ESA04", "ESA05", "ESA06", "ESA07", "ESA08", "ESA09", "ESA10"},
        "F5": {"ESA11", "ESA12", "ESA13", "ESA14", "ESA15", "ESA16", "ESA17", "ESA18", "ESA19", "ESA20"},
    },
    "Aplicaciones": {
        "F10": {"ESA01", "ESA02", "ESA03", "ESA04", "ESA05", "ESA06", "ESA07", "ESA15", "ESA16", "ESA17"},
        "F11": {"ESA08", "ESA09", "ESA10", "ESA11", "ESA12", "ESA13", "ESA14", "ESA18", "ESA19", "ESA20"},
    },
}

CLUSTER_THRESHOLDS = {
    "Europa":       {"warning": 500, "critical": 3000,  "total_warning": 2000,  "total_critical": 10000},
    "America":      {"warning": 500, "critical": 3000,  "total_warning": 2000,  "total_critical": 10000},
    "Brasil":       {"warning": 500, "critical": 3000,  "total_warning": 2000,  "total_critical": 10000},
    "Aplicaciones": {"warning": 500, "critical": 15000, "total_warning": 25000, "total_critical": 80000},
}

ADV_THRESHOLDS = {
    "cpu_warning": 85,
    "cpu_critical": 95,
    "ram_warning": 85,
    "ram_critical": 95,
    "conn_warning": 75,
    "conn_critical": 90,
    "growth_warning": 100,
    "growth_critical": 300,
    "active_recips_warning": 25000,
    "smtp_low_conn_out": 5,
    "smtp_high_conn_out": 60,
    "imbalance_ratio_warning": 2.0,
    "imbalance_ratio_critical": 3.0,
    "stuck_min_queue": 500,
    "stuck_cycles": 3,
}

CSV_HEADERS = [
    "fecha","hora","timestamp","cluster","nodo","status","encolados","cpu","ram",
    "conn_in","conn_out","active_recips","inj_msgs_1m","inj_msgs_5m","inj_msgs_15m",
    "delivered_recips_1m","delivered_recips_5m","delivered_recips_15m",
    "inj_recips_1m","inj_recips_5m","inj_recips_15m",
    "completed_recips_1m","completed_recips_5m","completed_recips_15m",
    "soft_bounced_evts_1m","soft_bounced_evts_5m","soft_bounced_evts_15m","error",
]

# =========================================================
# DATA CLASS
# =========================================================
@dataclass
class Result:
    timestamp: str
    nodo: str
    cluster: str
    status: str
    encolados: int
    cpu: int
    ram: int
    conn_in: int
    conn_out: int
    active_recips: int
    inj_msgs_1m: int
    inj_msgs_5m: int
    inj_msgs_15m: int
    delivered_recips_1m: int
    delivered_recips_5m: int
    delivered_recips_15m: int
    inj_recips_1m: int
    inj_recips_5m: int
    inj_recips_15m: int
    completed_recips_1m: int
    completed_recips_5m: int
    completed_recips_15m: int
    soft_bounced_evts_1m: int
    soft_bounced_evts_5m: int
    soft_bounced_evts_15m: int
    error: Optional[str] = None


# =========================================================
# HELPERS
# =========================================================
def cluster_order() -> List[str]:
    return ["Europa", "America", "Brasil", "Aplicaciones"]

def nodo_from_index(idx: int) -> str:
    return f"ESA{idx:02d}"

def fmt_num_dot(n: int) -> str:
    return f"{n:,}".replace(",", ".")

def to_int(value: Optional[str]) -> int:
    if value is None:
        return 0
    s = str(value).strip()
    if not s or s.upper() == "N/A":
        return 0
    digits = []
    for ch in s:
        if ch.isdigit() or ch == ".":
            digits.append(ch)
        else:
            break
    try:
        return int(float("".join(digits))) if digits else 0
    except Exception:
        return 0

def load_env_file(path: str) -> Dict[str, str]:
    data: Dict[str, str] = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            data[k.strip()] = v.strip()
    return data

def safe_cluster_filename(cluster: str) -> str:
    return (
        cluster.lower()
        .replace("á", "a").replace("é", "e").replace("í", "i")
        .replace("ó", "o").replace("ú", "u").replace(" ", "_")
    )

def ensure_csv_dir() -> None:
    Path(CSV_OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

def build_cluster_csv_path(cluster: str, now: datetime) -> str:
    filename = f"{now.strftime('%Y_%m')}_{safe_cluster_filename(cluster)}.csv"
    return str(Path(CSV_OUTPUT_DIR) / filename)

def append_cluster_csv(cluster: str, results_map: Dict[str, Result], now: datetime) -> None:
    ensure_csv_dir()
    path = build_cluster_csv_path(cluster, now)
    file_exists = os.path.exists(path)

    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";")
        if not file_exists:
            writer.writerow(CSV_HEADERS)

        for nodo in sorted(results_map.keys()):
            r = results_map[nodo]
            writer.writerow([
                now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S"), r.timestamp, r.cluster, r.nodo,
                r.status, r.encolados, r.cpu, r.ram, r.conn_in, r.conn_out, r.active_recips,
                r.inj_msgs_1m, r.inj_msgs_5m, r.inj_msgs_15m,
                r.delivered_recips_1m, r.delivered_recips_5m, r.delivered_recips_15m,
                r.inj_recips_1m, r.inj_recips_5m, r.inj_recips_15m,
                r.completed_recips_1m, r.completed_recips_5m, r.completed_recips_15m,
                r.soft_bounced_evts_1m, r.soft_bounced_evts_5m, r.soft_bounced_evts_15m,
                r.error or "",
            ])

def persist_current_data_to_csv(current_data: Dict[str, Dict[str, Result]], now: datetime) -> None:
    for cluster, results_map in current_data.items():
        append_cluster_csv(cluster, results_map, now)

def total_status_text(cluster: str, total: int) -> str:
    th = CLUSTER_THRESHOLDS[cluster]
    if total >= th["total_critical"]:
        return "CRITICAL"
    if total >= th["total_warning"]:
        return "WARNING"
    return "OK"

def get_prev_queue(previous_data: Dict[str, Dict[str, int]], cluster: str, nodo: str) -> int:
    return previous_data.get(cluster, {}).get(nodo, 0)

def health_score(r: Result, prev_queue: int) -> int:
    score = 100
    q_th = CLUSTER_THRESHOLDS[r.cluster]
    if r.encolados >= q_th["critical"]:
        score -= 35
    elif r.encolados >= q_th["warning"]:
        score -= 20
    if r.cpu >= ADV_THRESHOLDS["cpu_critical"]:
        score -= 20
    elif r.cpu >= ADV_THRESHOLDS["cpu_warning"]:
        score -= 10
    if r.ram >= ADV_THRESHOLDS["ram_critical"]:
        score -= 15
    elif r.ram >= ADV_THRESHOLDS["ram_warning"]:
        score -= 8
    if r.conn_out >= ADV_THRESHOLDS["conn_critical"]:
        score -= 10
    elif r.conn_out >= ADV_THRESHOLDS["conn_warning"]:
        score -= 5

    growth = r.encolados - prev_queue
    if growth >= ADV_THRESHOLDS["growth_critical"]:
        score -= 15
    elif growth >= ADV_THRESHOLDS["growth_warning"]:
        score -= 8

    if r.active_recips >= ADV_THRESHOLDS["active_recips_warning"]:
        score -= 7

    if r.error or str(r.status).lower() != "online":
        score = min(score, 20)
    return max(0, min(100, score))

def diagnose_node(r: Result, prev_queue: int) -> str:
    growth = r.encolados - prev_queue
    if r.error:
        return "Sin respuesta"
    if str(r.status).lower() != "online":
        return f"Status={r.status}"
    if r.encolados >= ADV_THRESHOLDS["stuck_min_queue"] and r.conn_out <= ADV_THRESHOLDS["smtp_low_conn_out"]:
        return "Queue sin salida"
    if growth >= ADV_THRESHOLDS["growth_critical"] and r.conn_out >= ADV_THRESHOLDS["smtp_high_conn_out"]:
        return "Queue creciendo"
    if r.cpu >= ADV_THRESHOLDS["cpu_critical"]:
        return "CPU alta"
    if r.ram >= ADV_THRESHOLDS["ram_critical"]:
        return "RAM alta"
    if r.conn_out >= ADV_THRESHOLDS["conn_critical"]:
        return "Salida alta"
    if r.active_recips >= ADV_THRESHOLDS["active_recips_warning"] and r.encolados >= 50:
        return "Muchos recips"
    if r.encolados == 0 and r.conn_in == 0 and r.conn_out == 0:
        return "Sin actividad"
    return "OK"

def natural_risk_text(cluster: str, nodo: str, diag: str) -> str:
    if diag == "Sin respuesta":
        return f"{nodo} de {cluster} sin respuesta"
    mapping = {
        "Salida alta": f"Salida alta en {nodo} ({cluster})",
        "CPU alta": f"CPU alta en {nodo} ({cluster})",
        "RAM alta": f"RAM alta en {nodo} ({cluster})",
        "Queue sin salida": f"Queue sin salida en {nodo} ({cluster})",
        "Queue creciendo": f"Cola creciendo en {nodo} ({cluster})",
        "Muchos recips": f"Muchos destinatarios en {nodo} ({cluster})",
        "Sin actividad": f"Sin actividad en {nodo} ({cluster})",
    }
    if diag.startswith("Status="):
        status = diag.split("=", 1)[1]
        return f"{nodo} de {cluster}: status {status}"
    return mapping.get(diag, f"{diag} en {nodo} ({cluster})")

def cluster_rate_tendency(
    msg_in_1m: int, msg_in_5m: int, comp_1m: int, comp_5m: int,
    comp_15m: int, queue_delta: int, active_recips: int, bounce_1m: int
) -> str:
    if queue_delta >= ADV_THRESHOLDS["growth_critical"]:
        return "Cola creciendo"
    if queue_delta <= -ADV_THRESHOLDS["growth_warning"]:
        return "Cola drenando"
    if active_recips >= ADV_THRESHOLDS["active_recips_warning"] * 2:
        if comp_1m < comp_5m:
            return "Carga alta con proceso bajo"
        return "Carga activa elevada"
    if bounce_1m >= 1000:
        return "Rebotes temporales altos"

    up_5 = comp_1m / max(comp_5m, 1)
    up_15 = comp_1m / max(comp_15m, 1)
    if up_5 >= 1.20 and up_15 >= 1.20:
        return "Procesamiento acelerando"
    if up_5 <= 0.80 and up_15 <= 0.80:
        return "Procesamiento cayendo"

    msg_ratio = msg_in_1m / max(msg_in_5m, 1)
    if msg_ratio >= 1.20 and queue_delta >= 0:
        return "Tráfico creciendo"
    if msg_ratio <= 0.80 and queue_delta <= 0:
        return "Entrada moderándose"
    return "Estable"

def has_incidents(current_data: Dict[str, Dict[str, Result]]) -> bool:
    for cluster in cluster_order():
        for nodo in current_data.get(cluster, {}):
            r = current_data[cluster][nodo]
            if r.error:
                return True
            if str(r.status).lower() != "online":
                return True
            th = CLUSTER_THRESHOLDS[cluster]
            if r.encolados >= th["warning"]:
                return True
            if r.cpu >= ADV_THRESHOLDS["cpu_warning"]:
                return True
            if r.ram >= ADV_THRESHOLDS["ram_warning"]:
                return True
            if r.conn_out >= ADV_THRESHOLDS["conn_warning"]:
                return True
    return False

def update_cluster_peaks(
    current_data: Dict[str, Dict[str, Result]],
    node_peaks: Dict[str, Dict[str, Dict[str, object]]],
    total_peaks: Dict[str, Dict[str, object]],
    timestamp: str,
) -> None:
    for cluster, nodo_map in current_data.items():
        if cluster not in node_peaks:
            node_peaks[cluster] = {}
        if cluster not in total_peaks:
            total_peaks[cluster] = {"total": 0, "hora": "--:--"}

        total_cluster = 0
        for nodo, r in nodo_map.items():
            total_cluster += r.encolados
            prev_peak = node_peaks[cluster].get(nodo)
            if prev_peak is None or r.encolados > int(prev_peak["encolados"]):
                node_peaks[cluster][nodo] = {"hora": timestamp, "encolados": r.encolados}

        if total_cluster > int(total_peaks[cluster]["total"]):
            total_peaks[cluster] = {"hora": timestamp, "total": total_cluster}

# =========================================================
# XML / NETWORK
# =========================================================
def parse_status(xml_text: str) -> Tuple[str, Dict[str, int]]:
    root = ET.fromstring(xml_text)
    system_status = "unknown"
    sys_node = root.find(".//system")
    if sys_node is not None:
        system_status = sys_node.attrib.get("status", system_status)

    gauges = {
        "msgs_in_work_queue": 0,
        "cpu_utilization": 0,
        "ram_utilization": 0,
        "conn_in": 0,
        "conn_out": 0,
        "active_recips": 0,
    }
    for gauge in root.findall(".//gauge"):
        name = gauge.attrib.get("name")
        if name in gauges:
            gauges[name] = to_int(gauge.attrib.get("current"))

    rate_names = ["inj_msgs", "inj_recips", "soft_bounced_evts", "completed_recips", "delivered_recips"]
    rates: Dict[str, int] = {}
    for name in rate_names:
        rates[f"{name}_1m"] = 0
        rates[f"{name}_5m"] = 0
        rates[f"{name}_15m"] = 0

    for rate in root.findall(".//rate"):
        name = rate.attrib.get("name")
        if name in rate_names:
            rates[f"{name}_1m"] = to_int(rate.attrib.get("last_1_min"))
            rates[f"{name}_5m"] = to_int(rate.attrib.get("last_5_min"))
            rates[f"{name}_15m"] = to_int(rate.attrib.get("last_15_min"))

    return system_status, {**gauges, **rates}

def fetch_one(
    session: requests.Session, url: str, auth: Tuple[str, str], timestamp: str, cluster: str, idx: int
) -> Result:
    nodo = nodo_from_index(idx)
    last_err: Optional[str] = None
    for _ in range(RETRIES + 1):
        try:
            r = session.get(
                url,
                auth=auth,
                timeout=TIMEOUT_SECONDS,
                verify=VERIFY_SSL,
                headers={"Accept": "application/xml"},
            )
            if r.status_code != 200:
                return Result(timestamp, nodo, cluster, "offline", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, f"HTTP {r.status_code}")

            status, m = parse_status(r.text)
            return Result(
                timestamp=timestamp, nodo=nodo, cluster=cluster, status=status,
                encolados=m["msgs_in_work_queue"], cpu=m["cpu_utilization"], ram=m["ram_utilization"],
                conn_in=m["conn_in"], conn_out=m["conn_out"], active_recips=m["active_recips"],
                inj_msgs_1m=m["inj_msgs_1m"], inj_msgs_5m=m["inj_msgs_5m"], inj_msgs_15m=m["inj_msgs_15m"],
                delivered_recips_1m=m["delivered_recips_1m"], delivered_recips_5m=m["delivered_recips_5m"], delivered_recips_15m=m["delivered_recips_15m"],
                inj_recips_1m=m["inj_recips_1m"], inj_recips_5m=m["inj_recips_5m"], inj_recips_15m=m["inj_recips_15m"],
                completed_recips_1m=m["completed_recips_1m"], completed_recips_5m=m["completed_recips_5m"], completed_recips_15m=m["completed_recips_15m"],
                soft_bounced_evts_1m=m["soft_bounced_evts_1m"], soft_bounced_evts_5m=m["soft_bounced_evts_5m"], soft_bounced_evts_15m=m["soft_bounced_evts_15m"],
                error=None,
            )
        except requests.exceptions.RequestException as e:
            last_err = str(e)
        except ET.ParseError as e:
            last_err = f"XML ParseError: {e}"

    return Result(
        timestamp=timestamp, nodo=nodo, cluster=cluster, status="offline",
        encolados=0, cpu=0, ram=0, conn_in=0, conn_out=0, active_recips=0,
        inj_msgs_1m=0, inj_msgs_5m=0, inj_msgs_15m=0,
        delivered_recips_1m=0, delivered_recips_5m=0, delivered_recips_15m=0,
        inj_recips_1m=0, inj_recips_5m=0, inj_recips_15m=0,
        completed_recips_1m=0, completed_recips_5m=0, completed_recips_15m=0,
        soft_bounced_evts_1m=0, soft_bounced_evts_5m=0, soft_bounced_evts_15m=0,
        error=last_err or "RequestException",
    )

def fetch_cluster(
    session: requests.Session, group: Dict, auth: Tuple[str, str], timestamp: str
) -> List[Result]:
    cluster = group["cluster"]
    pattern = group["pattern"]
    start = group.get("start", 1)
    end = group.get("end", 20)
    results: List[Result] = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = [
            ex.submit(fetch_one, session, pattern.format(idx=i), auth, timestamp, cluster, i)
            for i in range(start, end + 1)
        ]
        for fut in as_completed(futures):
            results.append(fut.result())

    return sorted(results, key=lambda r: r.nodo)

# =========================================================
# APLICACIÓN GUI
# =========================================================
class MonitorGUI(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1500x900")
        self.minsize(1200, 700)

        self.auth = self.load_credentials()

        self.previous_data: Dict[str, Dict[str, int]] = {}
        self.current_data: Dict[str, Dict[str, Result]] = {}
        self.queue_history: Dict[str, Dict[str, List[int]]] = {}
        self.node_peaks: Dict[str, Dict[str, Dict[str, object]]] = {}
        self.total_peaks: Dict[str, Dict[str, object]] = {}

        self.worker_thread: Optional[threading.Thread] = None
        self.stop_flag = threading.Event()
        self.is_fetching = False
        self.ui_queue: "queue.Queue[Tuple[str, object]]" = queue.Queue()

        self.next_refresh_job = None
        self.countdown_job = None
        self.seconds_remaining = 0

        self._build_style()

        # Variables UI
        self.cluster_var_nodes = tk.StringVar(value="Europa")
        self.cluster_var_health = tk.StringVar(value="Europa")
        self.cluster_var_peaks = tk.StringVar(value="Europa")
        self.node_var_nodes = tk.StringVar(value="Todos")
        self.window_var_nodes = tk.StringVar(value="6")
        self._build_ui()
        self.after(200, self.process_ui_queue)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.after(400, self.start_monitor)

    # ---------------- UI ----------------
    def _build_style(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure("Treeview", rowheight=24, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
        style.configure("TButton", font=("Segoe UI", 10))
        style.configure("Header.TLabel", font=("Segoe UI", 12, "bold"))
        style.configure("Status.TLabel", font=("Segoe UI", 10, "bold"))

    def _build_ui(self) -> None:
        main = ttk.Frame(self, padding=10)
        main.pack(fill="both", expand=True)

        # Top controls
        top = ttk.Frame(main)
        top.pack(fill="x", pady=(0, 10))

        ttk.Button(top, text="Iniciar", command=self.start_monitor).pack(side="left", padx=4)
        ttk.Button(top, text="Detener", command=self.stop_monitor).pack(side="left", padx=4)
        ttk.Button(top, text="Refrescar ahora", command=self.manual_refresh).pack(side="left", padx=4)
        ttk.Button(top, text="Abrir carpeta CSV", command=self.open_csv_folder).pack(side="left", padx=4)
        ttk.Button(top, text="Exportar resumen", command=self.export_summary_csv).pack(side="left", padx=4)
        ttk.Button(top, text="Cerrar aplicación", command=self.on_close).pack(side="left", padx=4)

        self.status_var = tk.StringVar(value="Estado: detenido")
        self.mode_var = tk.StringVar(value="Modo: normal")
        self.updated_var = tk.StringVar(value="Última actualización: --")
        self.countdown_var = tk.StringVar(value="Próxima actualización: --")

        info = ttk.Frame(main)
        info.pack(fill="x", pady=(0, 8))
        ttk.Label(info, textvariable=self.status_var, style="Status.TLabel").pack(side="left", padx=(0, 15))
        ttk.Label(info, textvariable=self.mode_var, style="Status.TLabel").pack(side="left", padx=(0, 15))
        ttk.Label(info, textvariable=self.updated_var).pack(side="left", padx=(0, 15))
        ttk.Label(info, textvariable=self.countdown_var).pack(side="left")

        menubar = tk.Menu(self)
        menu_archivo = tk.Menu(menubar, tearoff=0)
        menu_archivo.add_command(label="Cerrar aplicación", command=self.on_close)
        menubar.add_cascade(label="Archivo", menu=menu_archivo)
        self.config(menu=menubar)

        # Notebook
        self.nb = ttk.Notebook(main)
        self.nb.pack(fill="both", expand=True)

        self.tab_summary = ttk.Frame(self.nb, padding=8)
        self.tab_nodes = ttk.Frame(self.nb, padding=8)
        self.tab_health = ttk.Frame(self.nb, padding=8)
        self.tab_incidents = ttk.Frame(self.nb, padding=8)
        self.tab_peaks = ttk.Frame(self.nb, padding=8)

        self.nb.add(self.tab_summary, text="Resumen")
        self.nb.add(self.tab_nodes, text="Nodos")
        self.nb.add(self.tab_health, text="Salud")
        self.nb.add(self.tab_incidents, text="Incidencias")
        self.nb.add(self.tab_peaks, text="Picos")

        self._build_summary_tab()
        self._build_nodes_tab()
        self._build_health_tab()
        self._build_incidents_tab()
        self._build_peaks_tab()

    def _new_tree(self, parent, columns, stretch_last=True, height=20):
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True)

        tree = ttk.Treeview(frame, columns=columns, show="headings", height=height)
        ysb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        xsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=ysb.set, xscrollcommand=xsb.set)

        tree.grid(row=0, column=0, sticky="nsew")
        ysb.grid(row=0, column=1, sticky="ns")
        xsb.grid(row=1, column=0, sticky="ew")

        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        for idx, col in enumerate(columns):
            width = 120
            anchor = "center"
            if col in ("Cluster", "Nodo", "Estado", "Diagnóstico", "Tendencia", "Hora", "Nivel"):
                anchor = "w"
            if col in ("Error", "Riesgo", "Detalle", "Hallazgo"):
                anchor = "w"
                width = 400
            if idx == len(columns) - 1 and stretch_last:
                tree.column(col, width=220, anchor=anchor, stretch=True)
            else:
                tree.column(col, width=width, anchor=anchor, stretch=False)
            tree.heading(col, text=col)

        return tree

    def _build_summary_tab(self) -> None:
        top = ttk.Label(self.tab_summary, text="Resumen por cluster", style="Header.TLabel")
        top.pack(anchor="w", pady=(0, 6))

        cols = ("Cluster", "Total cola", "Estado", "Variación", "Msg In 1m", "Rec Proc 1m", "Active", "Bounce", "Tendencia")
        self.summary_tree = self._new_tree(self.tab_summary, cols)

        farms_outer = ttk.Frame(self.tab_summary)
        farms_outer.pack(fill="x", padx=4, pady=(8, 4))

        row1 = ttk.Frame(farms_outer)
        row1.pack(fill="x", expand=True)
        row2 = ttk.Frame(farms_outer)
        row2.pack(fill="x", expand=True, pady=(6, 0))

        cluster_rows = [("Europa", row1), ("America", row1), ("Brasil", row2), ("Aplicaciones", row2)]
        for cluster_name, parent_row in cluster_rows:
            box = ttk.LabelFrame(parent_row, text=cluster_name)
            box.pack(side="left", fill="both", expand=True, padx=4, pady=2)
            tree = ttk.Treeview(box, columns=("farm", "encolados"), show="headings", height=2)
            tree.heading("farm", text="Farm")
            tree.heading("encolados", text="Total encolados")
            tree.column("farm", width=80, anchor="center")
            tree.column("encolados", width=140, anchor="center")
            tree.pack(fill="both", expand=True, padx=4, pady=4)
            setattr(self, f"summary_farm_tree_{cluster_name.lower()}", tree)

    def _build_nodes_tab(self) -> None:
        top = ttk.Label(self.tab_nodes, text="Estado detallado por nodo", style="Header.TLabel")
        top.pack(anchor="w", pady=(0, 6))

        controls = ttk.Frame(self.tab_nodes)
        controls.pack(fill="x", pady=(0, 8))

        ttk.Label(controls, text="Cluster:").pack(side="left")
        self.nodes_cluster_combo = ttk.Combobox(
            controls, textvariable=self.cluster_var_nodes, values=cluster_order(),
            width=14, state="readonly"
        )
        self.nodes_cluster_combo.pack(side="left", padx=(6, 12))
        self.nodes_cluster_combo.bind("<<ComboboxSelected>>", lambda e: self.on_nodes_cluster_changed())

        ttk.Label(controls, text="Nodo:").pack(side="left")
        self.nodes_node_combo = ttk.Combobox(
            controls, textvariable=self.node_var_nodes, values=["Todos"],
            width=16, state="readonly"
        )
        self.nodes_node_combo.pack(side="left", padx=(6, 12))
        self.nodes_node_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_nodes_tab())

        ttk.Label(controls, text="Horas:").pack(side="left")
        self.nodes_window_combo = ttk.Combobox(
            controls, textvariable=self.window_var_nodes, values=["1", "3", "6", "12", "24"],
            width=6, state="readonly"
        )
        self.nodes_window_combo.pack(side="left", padx=(6, 12))
        self.nodes_window_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_nodes_chart())

        cols = ("Cluster", "Nodo", "Status", "Encolados", "Anterior", "Var", "CPU", "RAM", "Conn In", "Conn Out", "Active Recips", "Error")
        table_frame = ttk.Frame(self.tab_nodes)
        table_frame.pack(fill="both", expand=True)
        self.nodes_tree = self._new_tree(table_frame, cols)
        self.nodes_tree.bind('<<TreeviewSelect>>', self.on_nodes_tree_select)
        self.nodes_tree.bind('<Escape>', self.on_nodes_escape)

        chart_wrap = ttk.Labelframe(self.tab_nodes, text="Histórico de encolados")
        chart_wrap.pack(fill="both", expand=False, pady=(8, 0))
        self.nodes_chart_canvas = tk.Canvas(chart_wrap, height=280, bg="white", highlightthickness=1, highlightbackground="#cccccc")
        self.nodes_chart_canvas.pack(fill="both", expand=True)
        self.nodes_chart_canvas.bind("<Configure>", lambda e: self.refresh_nodes_chart())

    def _build_health_tab(self) -> None:
        top = ttk.Label(self.tab_health, text="Salud operativa y diagnóstico", style="Header.TLabel")
        top.pack(anchor="w", pady=(0, 6))
        controls = ttk.Frame(self.tab_health)
        controls.pack(fill="x", pady=(0, 8))
        ttk.Label(controls, text="Cluster:").pack(side="left")
        self.health_cluster_combo = ttk.Combobox(
            controls, textvariable=self.cluster_var_health, values=cluster_order(),
            width=14, state="readonly"
        )
        self.health_cluster_combo.pack(side="left", padx=(6, 12))
        self.health_cluster_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_health_tab())

        cols = ("Cluster", "Nodo", "Health", "Diagnóstico", "Status", "CPU", "RAM", "Conn Out", "Active Recips")
        self.health_tree = self._new_tree(self.tab_health, cols)

    def _build_incidents_tab(self) -> None:
        split = ttk.Panedwindow(self.tab_incidents, orient="vertical")
        split.pack(fill="both", expand=True)

        topf = ttk.Labelframe(split, text="Incidencias")
        botf = ttk.Labelframe(split, text="Hallazgos avanzados")
        split.add(topf, weight=1)
        split.add(botf, weight=1)

        self.incidents_tree = self._new_tree(topf, ("Cluster", "Nodo", "Tipo", "Detalle"))
        self.findings_tree = self._new_tree(botf, ("Cluster", "Nodo", "Hallazgo"))

    def _build_peaks_tab(self) -> None:
        controls = ttk.Frame(self.tab_peaks)
        controls.pack(fill="x", pady=(0, 8))
        ttk.Label(controls, text="Cluster (solo picos por nodo):").pack(side="left")
        self.peaks_cluster_combo = ttk.Combobox(
            controls, textvariable=self.cluster_var_peaks, values=cluster_order(),
            width=14, state="readonly"
        )
        self.peaks_cluster_combo.pack(side="left", padx=(6, 12))
        self.peaks_cluster_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_peaks_tab())

        split = ttk.Panedwindow(self.tab_peaks, orient="vertical")
        split.pack(fill="both", expand=True)

        topf = ttk.Labelframe(split, text="Picos por nodo")
        botf = ttk.Labelframe(split, text="Picos totales por cluster")
        split.add(topf, weight=4)
        split.add(botf, weight=1)

        self.node_peaks_tree = self._new_tree(topf, ("Cluster", "Nodo", "Hora pico", "Encolados pico"), height=20)
        self.total_peaks_tree = self._new_tree(botf, ("Cluster", "Hora pico", "Total pico"), height=4)
        self.after(100, lambda: split.sashpos(0, 460))

    # ---------------- Monitor lifecycle ----------------
    def load_credentials(self) -> Tuple[str, str]:
        if not os.path.exists(CREDENTIALS_FILE):
            messagebox.showerror(
                "Credenciales no encontradas",
                f"No existe '{CREDENTIALS_FILE}'. Debe contener GLOBAL_USERNAME y GLOBAL_PASSWORD."
            )
            raise SystemExit(1)

        creds = load_env_file(CREDENTIALS_FILE)
        if "GLOBAL_USERNAME" not in creds or "GLOBAL_PASSWORD" not in creds:
            messagebox.showerror(
                "Credenciales incompletas",
                "Faltan GLOBAL_USERNAME o GLOBAL_PASSWORD en credentials.env"
            )
            raise SystemExit(1)
        return creds["GLOBAL_USERNAME"], creds["GLOBAL_PASSWORD"]

    def start_monitor(self) -> None:
        if self.is_fetching:
            return
        self.stop_flag.clear()
        self.status_var.set("Estado: iniciando...")
        self.fetch_cycle(manual=True)

    def stop_monitor(self) -> None:
        self.stop_flag.set()
        self.is_fetching = False
        self.cancel_timers()
        self.status_var.set("Estado: detenido")
        self.countdown_var.set("Próxima actualización: --")

    def manual_refresh(self) -> None:
        if self.is_fetching:
            return
        self.fetch_cycle(manual=True)

    def cancel_timers(self) -> None:
        if self.next_refresh_job:
            self.after_cancel(self.next_refresh_job)
            self.next_refresh_job = None
        if self.countdown_job:
            self.after_cancel(self.countdown_job)
            self.countdown_job = None

    def fetch_cycle(self, manual: bool = False) -> None:
        if self.is_fetching:
            return
        self.cancel_timers()
        self.is_fetching = True
        self.status_var.set("Estado: consultando nodos...")
        self.mode_var.set(f"Modo: {'manual' if manual else 'automático'}")

        self.worker_thread = threading.Thread(target=self._worker_fetch, args=(manual,), daemon=True)
        self.worker_thread.start()

    def _worker_fetch(self, manual: bool) -> None:
        now = datetime.now()
        timestamp = now.strftime("%H:%M")
        current_data: Dict[str, Dict[str, Result]] = {}

        try:
            with requests.Session() as session:
                with ThreadPoolExecutor(max_workers=len(GROUPS)) as ex:
                    fut_map = {
                        ex.submit(fetch_cluster, session, g, self.auth, timestamp): g["cluster"]
                        for g in GROUPS
                    }
                    for fut in as_completed(fut_map):
                        if self.stop_flag.is_set():
                            return
                        cluster = fut_map[fut]
                        results = fut.result()
                        current_data[cluster] = {r.nodo: r for r in results}

            persist_current_data_to_csv(current_data, now)

            for cluster, nodo_map in current_data.items():
                self.queue_history.setdefault(cluster, {})
                for nodo, r in nodo_map.items():
                    self.queue_history[cluster].setdefault(nodo, []).append((now, r.encolados))
                    self.queue_history[cluster][nodo] = self.queue_history[cluster][nodo][-500:]

            update_cluster_peaks(current_data, self.node_peaks, self.total_peaks, timestamp)
            incidents_active = has_incidents(current_data)
            refresh_seconds = REFRESH_SECONDS_INCIDENT if incidents_active else REFRESH_SECONDS_NORMAL

            payload = {
                "current_data": current_data,
                "timestamp": timestamp,
                "now": now,
                "incidents_active": incidents_active,
                "refresh_seconds": refresh_seconds,
                "manual": manual,
            }
            self.ui_queue.put(("update", payload))
        except Exception as e:
            self.ui_queue.put(("error", str(e)))

    def process_ui_queue(self) -> None:
        try:
            while True:
                msg_type, payload = self.ui_queue.get_nowait()
                if msg_type == "update":
                    self._apply_update(payload)
                elif msg_type == "error":
                    self.is_fetching = False
                    self.status_var.set("Estado: error")
                    messagebox.showerror("Error", str(payload))
        except queue.Empty:
            pass
        finally:
            self.after(200, self.process_ui_queue)

    def _apply_update(self, payload: Dict[str, object]) -> None:
        self.is_fetching = False
        self.current_data = payload["current_data"]  # type: ignore[assignment]
        timestamp = payload["timestamp"]             # type: ignore[assignment]
        now = payload["now"]                         # type: ignore[assignment]
        incidents_active = payload["incidents_active"]  # type: ignore[assignment]
        refresh_seconds = payload["refresh_seconds"]    # type: ignore[assignment]
        manual = payload["manual"]                      # type: ignore[assignment]

        self.updated_var.set(f"Última actualización: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        self.status_var.set("Estado: monitor activo")
        self.mode_var.set(f"Modo: {'incidencias' if incidents_active else 'normal'}")

        self.refresh_summary_tab()
        self.refresh_nodes_tab()
        self.refresh_nodes_chart()
        self.refresh_health_tab()
        self.refresh_incidents_tab()
        self.refresh_peaks_tab()

        self.previous_data = {
            c: {n: r.encolados for n, r in m.items()}
            for c, m in self.current_data.items()
        }

        if not self.stop_flag.is_set():
            self.seconds_remaining = int(refresh_seconds)
            self.update_countdown()
            self.next_refresh_job = self.after(int(refresh_seconds * 1000), self.fetch_cycle)

    def update_countdown(self) -> None:
        mins, secs = divmod(max(0, self.seconds_remaining), 60)
        self.countdown_var.set(f"Próxima actualización: {mins:02d}:{secs:02d}")
        if self.seconds_remaining > 0 and not self.stop_flag.is_set():
            self.seconds_remaining -= 1
            self.countdown_job = self.after(1000, self.update_countdown)

    # ---------------- Refresh tabs ----------------
    def clear_tree(self, tree: ttk.Treeview) -> None:
        for item in tree.get_children():
            tree.delete(item)

    def row_tag_status(self, state: str) -> str:
        return state

    def configure_common_tags(self, tree: ttk.Treeview) -> None:
        tree.tag_configure('ok', foreground='#008000')
        tree.tag_configure('warning', foreground='#ff8c00')
        tree.tag_configure('critical', foreground='#cc0000')
        tree.tag_configure('error', foreground='#cc0000')
        tree.tag_configure('totals', foreground='#000000', background='#d9d9d9')

    def refresh_summary_tab(self) -> None:
        self.clear_tree(self.summary_tree)
        self.configure_common_tags(self.summary_tree)

        for cluster in cluster_order():
            rows = list(self.current_data.get(cluster, {}).values())
            total_queue = sum(r.encolados for r in rows)
            estado = total_status_text(cluster, total_queue)

            cur_total = sum(r.encolados for r in self.current_data.get(cluster, {}).values())
            prev_total = sum(self.previous_data.get(cluster, {}).values()) if cluster in self.previous_data else 0
            delta = cur_total - prev_total
            delta_txt = f"{delta:+,}".replace(",", ".")

            msg_in = sum(r.inj_msgs_1m for r in rows)
            rec_proc = sum(r.completed_recips_1m for r in rows)
            active = sum(r.active_recips for r in rows)
            bounce = sum(r.soft_bounced_evts_1m for r in rows)

            tendency = cluster_rate_tendency(
                msg_in, max(sum(r.inj_msgs_5m for r in rows), 1), rec_proc,
                max(sum(r.completed_recips_5m for r in rows), 1),
                max(sum(r.completed_recips_15m for r in rows), 1),
                delta, active, bounce
            )

            tag = "ok"
            if estado == "WARNING":
                tag = "warning"
            elif estado == "CRITICAL":
                tag = "critical"

            self.summary_tree.insert(
                "", "end",
                values=(
                    cluster, fmt_num_dot(total_queue), estado, delta_txt,
                    fmt_num_dot(msg_in), fmt_num_dot(rec_proc), fmt_num_dot(active),
                    fmt_num_dot(bounce), tendency
                ),
                tags=(tag,)
            )

        try:
            self._populate_summary_farm_tables()
        except Exception:
            pass

    def refresh_nodes_tab(self) -> None:
        self.clear_tree(self.nodes_tree)
        self.configure_common_tags(self.nodes_tree)

        cluster = self.cluster_var_nodes.get() or 'Europa'
        all_nodes = sorted(self.current_data.get(cluster, {}).keys())
        combo_values = ['Todos'] + all_nodes
        try:
            self.nodes_node_combo['values'] = combo_values
        except Exception:
            pass
        selected_node = self.node_var_nodes.get() or 'Todos'
        if selected_node not in combo_values:
            selected_node = 'Todos'
            self.node_var_nodes.set('Todos')

        shown_rows = []
        for nodo in all_nodes:
            if selected_node != 'Todos' and nodo != selected_node:
                continue
            r = self.current_data[cluster][nodo]
            prev = get_prev_queue(self.previous_data, cluster, nodo)
            diff = r.encolados - prev
            shown_rows.append(r)

            tag = 'ok'
            if r.error:
                tag = 'error'
            elif r.encolados >= CLUSTER_THRESHOLDS[cluster]['critical']:
                tag = 'critical'
            elif r.encolados >= CLUSTER_THRESHOLDS[cluster]['warning']:
                tag = 'warning'
            elif str(r.status).lower() not in ('online', 'ok'):
                tag = 'warning'

            self.nodes_tree.insert('', 'end', values=(
                cluster, nodo, r.status, fmt_num_dot(r.encolados), fmt_num_dot(prev),
                f"{diff:+,}".replace(',', '.'), f"{r.cpu}%", f"{r.ram}%",
                fmt_num_dot(r.conn_in), fmt_num_dot(r.conn_out), fmt_num_dot(r.active_recips), r.error or ''
            ), tags=(tag,))

        total_queue = sum(r.encolados for r in shown_rows)
        total_prev = sum(get_prev_queue(self.previous_data, cluster, r.nodo) for r in shown_rows)
        total_diff = total_queue - total_prev
        self.nodes_tree.insert('', 'end', values=(
            cluster, 'TOTAL', '', fmt_num_dot(total_queue), fmt_num_dot(total_prev),
            f"{total_diff:+,}".replace(',', '.'), '', '', '', '', '', ''
        ), tags=('totals',))

        self.refresh_nodes_chart()

    def refresh_health_tab(self) -> None:
        self.clear_tree(self.health_tree)
        self.configure_common_tags(self.health_tree)

        cluster = self.cluster_var_health.get() or "Europa"
        for nodo in sorted(self.current_data.get(cluster, {}).keys()):
            r = self.current_data[cluster][nodo]
            prev = get_prev_queue(self.previous_data, cluster, nodo)
            hs = health_score(r, prev)
            diag = diagnose_node(r, prev)

            tag = "ok"
            if r.error:
                tag = "error"
            elif hs < 60:
                tag = "critical"
            elif hs < 80:
                tag = "warning"

            self.health_tree.insert(
                "", "end",
                values=(
                    cluster, nodo, f"{hs}%", diag, r.status, f"{r.cpu}%",
                    f"{r.ram}%", fmt_num_dot(r.conn_out), fmt_num_dot(r.active_recips)
                ),
                tags=(tag,)
            )

    def refresh_incidents_tab(self) -> None:
        self.clear_tree(self.incidents_tree)
        self.clear_tree(self.findings_tree)
        self.configure_common_tags(self.incidents_tree)
        self.configure_common_tags(self.findings_tree)

        # Incidencias
        found_incident = False
        for cluster in cluster_order():
            for nodo in sorted(self.current_data.get(cluster, {}).keys()):
                r = self.current_data[cluster][nodo]
                if r.error:
                    found_incident = True
                    self.incidents_tree.insert("", "end", values=(cluster, nodo, "Error", r.error), tags=("error",))
                    continue
                if str(r.status).lower() != "online":
                    found_incident = True
                    self.incidents_tree.insert("", "end", values=(cluster, nodo, "Status", r.status), tags=("warning",))

        if not found_incident:
            self.incidents_tree.insert("", "end", values=("-", "-", "OK", "No se han detectado incidencias"), tags=("ok",))

        # Hallazgos avanzados
        findings_added = False
        for cluster in cluster_order():
            rows = list(self.current_data.get(cluster, {}).values())
            if not rows:
                continue

            queues = [r.encolados for r in rows]
            max_q = max(queues) if queues else 0
            avg_q = int(sum(queues) / len(queues)) if queues else 0
            zero_nodes = sum(1 for q in queues if q == 0)
            loaded_nodes = sum(1 for q in queues if q > 0)

            if max_q >= CLUSTER_THRESHOLDS[cluster]["critical"] and avg_q > 0 and max_q >= avg_q * 3:
                findings_added = True
                self.findings_tree.insert("", "end", values=(cluster, "-", f"Desbalanceado crítico (máx={fmt_num_dot(max_q)}, media={fmt_num_dot(avg_q)})"), tags=("critical",))

            if zero_nodes > 0 and loaded_nodes > 0:
                findings_added = True
                self.findings_tree.insert("", "end", values=(cluster, "-", "Hay nodos vacíos y nodos cargados a la vez"), tags=("warning",))

            for r in rows:
                prev = get_prev_queue(self.previous_data, cluster, r.nodo)
                growth = r.encolados - prev
                hist = self.queue_history.get(cluster, {}).get(r.nodo, [])

                if len(hist) >= ADV_THRESHOLDS["stuck_cycles"]:
                    last = hist[-ADV_THRESHOLDS["stuck_cycles"]:]
                    if all((v[1] if isinstance(v, tuple) else v) >= ADV_THRESHOLDS["stuck_min_queue"] for v in last) and r.conn_out <= ADV_THRESHOLDS["smtp_low_conn_out"]:
                        findings_added = True
                        self.findings_tree.insert("", "end", values=(cluster, r.nodo, f"Cola atascada ({fmt_num_dot(r.encolados)} en cola, salida {r.conn_out})"), tags=("critical",))

                if growth >= ADV_THRESHOLDS["growth_critical"]:
                    findings_added = True
                    self.findings_tree.insert("", "end", values=(cluster, r.nodo, f"Crecimiento brusco {growth:+}"), tags=("warning",))

                if r.conn_out > 0:
                    imbalance = r.conn_in / float(r.conn_out)
                    if imbalance >= ADV_THRESHOLDS["imbalance_ratio_critical"]:
                        findings_added = True
                        self.findings_tree.insert("", "end", values=(cluster, r.nodo, f"Desequilibrio In/Out {imbalance:.2f} ({r.conn_in}/{r.conn_out})"), tags=("warning",))

        if not findings_added:
            self.findings_tree.insert("", "end", values=("-", "-", "Sin hallazgos avanzados relevantes"), tags=("ok",))

    def refresh_peaks_tab(self) -> None:
        self.clear_tree(self.node_peaks_tree)
        self.clear_tree(self.total_peaks_tree)
        self.configure_common_tags(self.node_peaks_tree)
        self.configure_common_tags(self.total_peaks_tree)

        selected_cluster = self.cluster_var_peaks.get() or "Europa"

        ranking = []
        for nodo, info in self.node_peaks.get(selected_cluster, {}).items():
            ranking.append((nodo, str(info["hora"]), int(info["encolados"])))
        ranking.sort(key=lambda x: x[0])

        if not ranking:
            self.node_peaks_tree.insert("", "end", values=(selected_cluster, "-", "--:--", "0"), tags=("ok",))
        else:
            for nodo, hora, enc in ranking[:20]:
                tag = "ok"
                if enc >= CLUSTER_THRESHOLDS[selected_cluster]["critical"]:
                    tag = "critical"
                elif enc >= CLUSTER_THRESHOLDS[selected_cluster]["warning"]:
                    tag = "warning"
                self.node_peaks_tree.insert("", "end", values=(selected_cluster, nodo, hora, fmt_num_dot(enc)), tags=(tag,))

        for cluster in cluster_order():
            total_info = self.total_peaks.get(cluster, {"hora": "--:--", "total": 0})
            total = int(total_info["total"])
            tag = "ok"
            if total >= CLUSTER_THRESHOLDS[cluster]["total_critical"]:
                tag = "critical"
            elif total >= CLUSTER_THRESHOLDS[cluster]["total_warning"]:
                tag = "warning"
            self.total_peaks_tree.insert("", "end", values=(cluster, total_info["hora"], fmt_num_dot(total)), tags=(tag,))

    # ---------------- Utils ----------------

    def open_csv_folder(self) -> None:
        ensure_csv_dir()
        path = str(Path(CSV_OUTPUT_DIR).resolve())
        messagebox.showinfo("Carpeta CSV", f"Los CSV se guardan en:\n{path}")

    def export_summary_csv(self) -> None:
        if not self.current_data:
            messagebox.showwarning("Sin datos", "Todavía no hay datos para exportar.")
            return

        file_path = filedialog.asksaveasfilename(
            title="Guardar resumen",
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile=f"resumen_monitor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        )
        if not file_path:
            return

        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(["Cluster", "Total cola", "Estado", "Variación", "Msg In 1m", "Rec Proc 1m", "Active", "Bounce", "Tendencia"])

            for cluster in cluster_order():
                rows = list(self.current_data.get(cluster, {}).values())
                total_queue = sum(r.encolados for r in rows)
                estado = total_status_text(cluster, total_queue)
                cur_total = sum(r.encolados for r in self.current_data.get(cluster, {}).values())
                prev_total = sum(self.previous_data.get(cluster, {}).values()) if cluster in self.previous_data else 0
                delta = cur_total - prev_total
                msg_in = sum(r.inj_msgs_1m for r in rows)
                rec_proc = sum(r.completed_recips_1m for r in rows)
                active = sum(r.active_recips for r in rows)
                bounce = sum(r.soft_bounced_evts_1m for r in rows)
                tendency = cluster_rate_tendency(
                    msg_in, max(sum(r.inj_msgs_5m for r in rows), 1), rec_proc,
                    max(sum(r.completed_recips_5m for r in rows), 1),
                    max(sum(r.completed_recips_15m for r in rows), 1),
                    delta, active, bounce
                )
                writer.writerow([
                    cluster, total_queue, estado, delta, msg_in, rec_proc, active, bounce, tendency
                ])

        messagebox.showinfo("Exportación completada", f"Archivo guardado en:\n{file_path}")


    def _load_history_from_csv(self, cluster: str, nodo: str, hours: int) -> List[Tuple[datetime, int]]:
        points: List[Tuple[datetime, int]] = []
        now = datetime.now()
        cutoff = now - timedelta(hours=hours)
        path = Path(build_cluster_csv_path(cluster, now))
        if not path.exists():
            return points
        try:
            with open(path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter=';')
                for row in reader:
                    if row.get('nodo') != nodo:
                        continue
                    ts_text = row.get('timestamp') or ''
                    try:
                        ts = datetime.strptime(f"{now.strftime('%Y-%m-%d')} {ts_text}", '%Y-%m-%d %H:%M')
                    except Exception:
                        try:
                            ts = datetime.strptime(f"{row.get('fecha','')} {row.get('hora','')}", '%Y-%m-%d %H:%M:%S')
                        except Exception:
                            continue
                    if ts >= cutoff:
                        points.append((ts, to_int(row.get('encolados'))))
        except Exception:
            return []
        return points

    def _merge_history_points(self, cluster: str, nodo: str, hours: int) -> List[Tuple[datetime, int]]:
        points = self._load_history_from_csv(cluster, nodo, hours)
        cutoff = datetime.now() - timedelta(hours=hours)
        for item in self.queue_history.get(cluster, {}).get(nodo, []):
            if isinstance(item, tuple) and len(item) == 2:
                ts, val = item
                if isinstance(ts, datetime) and ts >= cutoff:
                    points.append((ts, int(val)))
        dedup = {}
        for ts, val in points:
            dedup[ts.strftime('%Y-%m-%d %H:%M:%S')] = (ts, val)
        merged = sorted(dedup.values(), key=lambda x: x[0])
        return merged

    def on_nodes_cluster_changed(self) -> None:
        cluster = self.cluster_var_nodes.get() or 'Europa'
        nodes = sorted(self.current_data.get(cluster, {}).keys())
        values = ['Todos'] + nodes
        self.nodes_node_combo['values'] = values
        if self.node_var_nodes.get() not in values:
            self.node_var_nodes.set('Todos')
        self.refresh_nodes_tab()

    def on_nodes_tree_select(self, event=None) -> None:
        try:
            selection = self.nodes_tree.selection()
            if not selection:
                return
            item = selection[0]
            values = self.nodes_tree.item(item, 'values')
            if not values:
                return
            nodo = str(values[1]) if len(values) > 1 else ''
            if nodo and nodo != 'TOTAL':
                self.node_var_nodes.set(nodo)
                self.refresh_nodes_chart()
        except Exception:
            pass

    def on_nodes_escape(self, event=None) -> None:
        try:
            for item in self.nodes_tree.selection():
                self.nodes_tree.selection_remove(item)
            self.node_var_nodes.set('Todos')
            self.refresh_nodes_tab()
        except Exception:
            pass

    def refresh_nodes_chart(self) -> None:
        canvas = getattr(self, 'nodes_chart_canvas', None)
        if canvas is None:
            return
        canvas.delete('all')
        width = max(canvas.winfo_width(), 400)
        height = max(canvas.winfo_height(), 220)
        left, top, right, bottom = 55, 20, width - 15, height - 35
        canvas.create_rectangle(left, top, right, bottom, outline='#bbbbbb')

        cluster = self.cluster_var_nodes.get() or 'Europa'
        node = self.node_var_nodes.get() or 'Todos'
        try:
            hours = max(1, int(self.window_var_nodes.get() or '6'))
        except Exception:
            hours = 6

        if node == 'Todos':
            node_list = sorted(self.current_data.get(cluster, {}).keys())
        else:
            node_list = [node] if node in self.current_data.get(cluster, {}) else []

        all_series = []
        max_y = 0
        start = datetime.now() - timedelta(hours=hours)
        for nodo in node_list:
            pts = self._merge_history_points(cluster, nodo, hours)
            if pts:
                all_series.append((nodo, pts))
                max_y = max(max_y, max(v for _, v in pts))

        if not all_series:
            canvas.create_text(width/2, height/2, text='Sin histórico para mostrar', fill='#666666', font=('Segoe UI', 11))
            return

        max_y = max(max_y, 1)
        # axes labels
        for i in range(5):
            y = bottom - (bottom-top) * i/4
            val = int(max_y * i/4)
            canvas.create_line(left-4, y, left, y, fill='#777777')
            canvas.create_text(left-8, y, text=fmt_num_dot(val), anchor='e', font=('Segoe UI', 8), fill='#555555')
        for i in range(hours+1):
            x = left + (right-left) * (i/max(hours,1))
            canvas.create_line(x, bottom, x, bottom+4, fill='#777777')
            label_time = (start + timedelta(hours=i)).strftime('%H:%M')
            canvas.create_text(x, bottom+14, text=label_time, anchor='n', font=('Segoe UI', 8), fill='#555555')

        palette = ['#1f77b4','#2ca02c','#d62728','#9467bd','#ff7f0e','#17becf','#8c564b','#e377c2']
        for idx, (nodo, pts) in enumerate(all_series):
            color = palette[idx % len(palette)]
            prev_xy = None
            for ts, val in pts:
                total_seconds = max(hours * 3600, 1)
                ratio = max(0.0, min(1.0, (ts - start).total_seconds() / total_seconds))
                x = left + ratio * (right-left)
                y = bottom - (val / max_y) * (bottom-top)
                if prev_xy is not None:
                    canvas.create_line(prev_xy[0], prev_xy[1], x, y, fill=color, width=2)
                prev_xy = (x, y)
            if pts:
                canvas.create_text(right - 4, top + 12 + idx*14, text=nodo, anchor='e', font=('Segoe UI', 8), fill=color)

    def _farm_totals_for_cluster(self, cluster_name: str) -> List[Tuple[str, int]]:
        rows_dict = self.current_data.get(cluster_name, {})
        out: List[Tuple[str, int]] = []
        for farm_name, nodes in CLUSTER_FARM_MAP.get(cluster_name, {}).items():
            total = sum(rows_dict[n].encolados for n in rows_dict if n in nodes)
            out.append((farm_name, total))
        return out

    def _populate_summary_farm_tables(self) -> None:
        for cluster_name in cluster_order():
            attr = f'summary_farm_tree_{cluster_name.lower()}'
            tree = getattr(self, attr, None)
            if tree is None:
                continue
            self.clear_tree(tree)
            self.configure_common_tags(tree)
            for farm_name, total in self._farm_totals_for_cluster(cluster_name):
                tag = 'ok'
                if total >= CLUSTER_THRESHOLDS[cluster_name]['total_critical']:
                    tag = 'critical'
                elif total >= CLUSTER_THRESHOLDS[cluster_name]['total_warning']:
                    tag = 'warning'
                tree.insert('', 'end', values=(farm_name, fmt_num_dot(total)), tags=(tag,))

    def on_close(self) -> None:
        self.stop_monitor()
        self.destroy()


def main() -> None:
    ensure_csv_dir()
    app = MonitorGUI()
    app.mainloop()

if __name__ == "__main__":
    main()
