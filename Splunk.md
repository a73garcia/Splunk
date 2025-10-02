# 📊 Guía de Búsquedas en Splunk

[![Splunk](https://img.shields.io/badge/Splunk-Search-blue)](https://www.splunk.com)

## 📌 Tabla de Contenidos
- [Introducción](#introducción)
- [Consultas Básicas](#consultas-básicas)
- [Consultas Intermedias](#consultas-intermedias)
- [Consultas Avanzadas](#consultas-avanzadas)
- [Buenas Prácticas y KPIs](#buenas-prácticas-y-kpis)

---

## 🔹 Introducción
Esta guía recopila ejemplos de búsquedas en **Splunk** para análisis de correo electrónico.  
Las consultas están clasificadas por nivel y pensadas para usarse en **dashboards y macros**.

---

<details>
<summary>⚡ Consultas Básicas</summary>

### Buscar por host
```spl
index=mail_logs host="servidor1"
```

### Campos día y hora
```spl
index=mail_logs 
| eval dia=strftime(_time,"%d-%m-%Y"), hora=strftime(_time,"%H:%M:%S")
| table dia hora sender recipient subject
```

### Filtrar campos nulos
```spl
index=mail_logs NOT [ search adjunto=* ]
```
</details>

---

<details>
<summary>📊 Consultas Intermedias</summary>

### Estadísticas por política
```spl
index=mail_logs | stats count by policy
```

### Correos grandes sin adjuntos
```spl
index=mail_logs size>2000000 NOT adjunto=*
```
</details>

---

<details>
<summary>🚀 Consultas Avanzadas</summary>

### Extraer dominio del remitente
```spl
index=mail_logs 
| rex field=sender "(?<dominio>@.*)$"
| stats count by dominio
```

### Agrupar por cluster
```spl
index=mail_logs 
| rex field=host "(?<cluster>[^.]+\.cluster)"
| stats count by cluster
```
</details>

---

## ✅ Buenas Prácticas y KPIs
- Guardar búsquedas con nombres claros: `Mail_SinAdjunto_+2MB`.  
- Añadir parámetros (`$cluster$`, `$host$`) en dashboards.  
- Reglas para KPIs:  
  - **Volumen de correos/hora** (`timechart span=1h count`).  
  - **Top 20 dominios emisores** (`stats count by dominio`).  
  - **Correos con/ sin adjunto** (`stats count by adjunto`).  
