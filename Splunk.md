# 📊 Guía de Búsquedas en Splunk (Cisco ESA / Correo + Red)

[![Splunk](https://img.shields.io/badge/Splunk-Search-blue)](https://www.splunk.com)

## 📌 Tabla de Contenidos
- [Cómo usar esta guía](#-cómo-usar-esta-guía)
- [Búsquedas Básicas](#-búsquedas-básicas)
- [Campos Útiles](#-campos-útiles)
- [Tablas Personalizadas](#-tablas-personalizadas)
- [Estadísticas y Conteos](#-estadísticas-y-conteos)
- [Filtrados Avanzados](#-filtrados-avanzados)
- [Ejemplos Prácticos](#-ejemplos-prácticos)
- [Opciones de Red](#-opciones-de-red)
- [Extracción de Dominios](#-extracción-de-dominios)
- [Manejo de Fechas y Tiempos](#-manejo-de-fechas-y-tiempos)
- [Consultas Avanzadas](#-consultas-avanzadas)
- [Estadísticas Avanzadas y KPIs](#-estadísticas-avanzadas-y-kpis)
- [Casos Especiales](#-casos-especiales-correos-sin-adjuntos--2-mb)
- [Guardar Búsquedas y Alertas](#-guardar-búsquedas-y-alertas)
- [Macros y Buenas Prácticas](#-macros-y-buenas-prácticas)

---

## 🔹 Cómo usar esta guía
- Ajusta siempre `index="siem-eu-mta"` al índice real en tu Splunk.
- Si `start` viene como texto (`Wed Oct 1 14:45:43 2025`), conviértelo con `strptime` + `strftime`.
- Campos habituales: `suser`, `duser`, `internal_message_id`, `host`, `signature`, `ESA*`, `src`, `dest`.

---

<details>
<summary>⚡ Búsquedas Básicas</summary>

```spl
index="siem-eu-mta"                              # todo en el índice
index="siem-eu-mta" suser="usuario@dominio.com"  # por remitente
index="siem-eu-mta" duser="destino@dominio.com"  # por destinatario
index="siem-eu-mta" earliest=-24h latest=now     # últimas 24h
```
</details>

---

<details>
<summary>📌 Campos Útiles</summary>

- `suser` → remitente  
- `duser` → destinatario  
- `internal_message_id` → ID mensaje (MID)  
- `host` → ESA  
- `start` → fecha/hora evento  
- `signature` → estado (accepted/rejected)  
- `ESAOFVerdict` → veredicto (NEGATIVE, SKIPPED…)  
- `src`, `dest` → IPs  
</details>

---

<details>
<summary>📋 Tablas Personalizadas</summary>

```spl
index="siem-eu-mta"
| rename suser AS Sender, duser AS Recipient, internal_message_id AS MID
| table MID Sender Recipient host
```

Separar fecha en día y hora:

```spl
| eval start_ts=strptime(start,"%a %b %e %H:%M:%S %Y")
| eval Dia=strftime(start_ts,"%Y-%m-%d"), Hora=strftime(start_ts,"%H:%M:%S")
| table Dia Hora MID suser duser host
```
</details>

---

<details>
<summary>📊 Estadísticas y Conteos</summary>

```spl
| stats count BY suser | sort - count
| rex field=suser "@(?<domain>[^> ]+)$" | stats count BY domain | sort - count
| timechart span=1h count
```
</details>

---

<details>
<summary>🔎 Filtrados Avanzados</summary>

```spl
signature="rejected"    # rechazados
signature="accepted"    # aceptados
ESAOFVerdict="NEGATIVE" # veredicto negativo
host="CIOBI301926B"     # por host ESA
```
</details>

---

<details>
<summary>🧪 Ejemplos Prácticos</summary>

Ver MIDs de un remitente:

```spl
| table _time internal_message_id duser signature
```

Top remitentes sospechosos:

```spl
| stats count BY suser | sort - count | head 10
```

Flujo de correos aceptados por hora:

```spl
signature="accepted" | timechart span=1h count
```
</details>

---

<details>
<summary>🌐 Opciones de Red</summary>

Filtrados de red:

```spl
src="180.205.32.105"            
src="192.168.1.0/24"            
(src="x.x.x.x" OR src="y.y.y.y")
NOT src="10.*" NOT src="192.168.*"
```

Estadísticas:

```spl
| stats count BY src | sort - count | head 20
| stats count BY dest | sort - count | head 20
| stats count BY host | sort - count
```

Visualización:

```spl
| stats count BY src host | xyseries src host count
```
</details>

---

<details>
<summary>🏷️ Extracción de Dominios</summary>

```spl
| rex field=suser "@(?<sender_domain>[^> ]+)$" | stats count BY sender_domain
| rex field=duser "@(?<recipient_domain>[^> ]+)$" | stats count BY recipient_domain
| rex field=suser "@(?<domain>[^> ]+)$" | stats count BY domain | sort - count | head 10
```
</details>

---

<details>
<summary>🕒 Manejo de Fechas y Tiempos</summary>

```spl
| eval start_ts=strptime(start,"%a %b %e %H:%M:%S %Y")
| eval Fecha=strftime(start_ts,"%Y-%m-%d"), Mes=strftime(start_ts,"%Y-%m"), Hora=strftime(start_ts,"%H:%M:%S"), DiaSemana=strftime(start_ts,"%A")
| stats count BY Mes | sort Mes
| eval Hora=strftime(start_ts,"%H") | stats count BY Hora | sort Hora
```
</details>

---

<details>
<summary>🚀 Consultas Avanzadas</summary>

### Normalización y extracción
```spl
| rex field=_raw "src=(?<src>(?:\d{1,3}\.){3}\d{1,3})"
| rex field=_raw "dst=(?<dest>(?:\d{1,3}\.){3}\d{1,3})"
```

### Correlación por MID
```spl
| transaction internal_message_id startswith=signature="accepted" endswith=signature="delivered" keepevicted=t maxspan=2h
```

### Ventanas móviles y outliers
```spl
| bin _time span=1m | stats count AS c BY _time
| streamstats window=30 avg(c) AS avg30 stdev(c) AS sd30
| eval z=if(sd30>0,(c-avg30)/sd30,null())
```
</details>

---

<details>
<summary>📈 Estadísticas Avanzadas y KPIs</summary>

```spl
| rex field=suser "@(?<domain>[^> ]+)$"
| stats sum(eval(signature="rejected")) AS rechazados count AS total BY domain
| eval ratio_rechazo=round(rechazados/total*100,2)
```

Percentiles de tamaño:

```spl
| stats avg(msg_size) AS avg p95(msg_size) AS p95 max(msg_size) AS max
```

Top remitentes con bucket “otros”:

```spl
| stats count BY suser | sort - count | head 9
| appendpipe [ stats sum(count) AS count | eval suser="otros" ]
```
</details>

---

<details>
<summary>📧 Casos Especiales: correos sin adjuntos > 2 MB</summary>

```spl
| eval size_bytes=coalesce(msg_size,message_size,bytes)
| where size_bytes>2097152
| where attachment_count=0 OR isnull(attachment_count)
```

Alternativa con regex en `_raw`:

```spl
| rex field=_raw max_match=0 "(?i)(Content-Disposition:\s*attachment|filename=)"
| eval attachment_count=mvcount(match)
| where attachment_count=0
```
</details>

---

<details>
<summary>💾 Guardar Búsquedas y Alertas</summary>

1. Ejecutar búsqueda  
2. **Save As → Report / Alert**  
3. Configurar permisos y condiciones  
</details>

---

<details>
<summary>🛠️ Macros y Buenas Prácticas</summary>

- Prefiere `stats` sobre `transaction` en grandes volúmenes.  
- Usa `timechart` con `limit` y `useother=t`.  
- Evita `join` en datasets grandes.  
- Normaliza fechas a ISO (`%Y-%m-%d`).  
- Guarda búsquedas frecuentes como Report; condiciones → Alert.  

Macros:

```spl
`idx_mta()` → index="siem-eu-mta"
`extraer_dominio(field,out)` → rex field=$field$ "@(?<$out$>[^> ]+)$"
`solo_publicas(field)` → NOT $field$="10.*" NOT $field$="192.168.*"
```
</details>
