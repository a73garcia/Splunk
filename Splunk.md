# 📖 Guía Unificada de Búsquedas en Splunk (Cisco ESA / Correo + Red)

Esta guía recopila ejemplos prácticos de **búsquedas, filtrados, estadísticas y visualizaciones en Splunk**, aplicados a **logs de correo (Cisco ESA)** y **tráfico de red**.  
Incluye desde lo básico hasta consultas avanzadas y casos especiales (como correos sin adjuntos y grandes).  

---

## 📚 Tabla de contenidos
- [0. Cómo usar esta guía](#0-cómo-usar-esta-guía)
- [1. Búsquedas básicas](#1-búsquedas-básicas)
- [2. Campos útiles](#2-campos-útiles)
- [3. Tablas personalizadas](#3-tablas-personalizadas)
- [4. Estadísticas y conteos](#4-estadísticas-y-conteos)
- [5. Filtrados avanzados](#5-filtrados-avanzados)
- [6. Opciones de red](#6-opciones-de-red)
  - [6.1 Filtrados de red](#61-filtrados-de-red)
  - [6.2 Estadísticas](#62-estadísticas)
  - [6.3 Visualización](#63-visualización)
  - [6.4 Reputación y anomalías](#64-reputación-y-anomalías)
- [7. Extracción de dominios](#7-extracción-de-dominios)
- [8. Manejo de fechas y tiempos](#8-manejo-de-fechas-y-tiempos)
- [9. Consultas avanzadas](#9-consultas-avanzadas)
  - [9.1 Normalización y extracción](#91-normalización-y-extracción)
  - [9.2 Correlación por MID](#92-correlación-por-mid)
  - [9.3 Ventanas móviles y rachas](#93-ventanas-móviles-y-rachas)
  - [9.4 Picos y outliers](#94-picos-y-outliers)
  - [9.5 Cardinalidad y distintos](#95-cardinalidad-y-distintos)
  - [9.6 Enriquecimiento (GeoIP/ASN/IOC)](#96-enriquecimiento-geoipasnioc)
  - [9.7 Lookups y tablas maestras](#97-lookups-y-tablas-maestras)
- [10. Estadísticas avanzadas y KPIs](#10-estadísticas-avanzadas-y-kpis)
- [11. Casos especiales: correos sin adjuntos >2 MB](#11-casos-especiales-correos-sin-adjuntos-2-mb)
- [12. Guardar búsquedas y alertas](#12-guardar-búsquedas-y-alertas)
- [13. Buenas prácticas y macros](#13-buenas-prácticas-y-macros)

---

## 0. Cómo usar esta guía
- Ajusta siempre `index="siem-eu-mta"` al índice real en tu Splunk.
- Usa rangos de tiempo (`earliest=-24h latest=now`) para optimizar búsquedas.
- Campos habituales:  
  - `suser` → remitente  
  - `duser` → destinatario  
  - `internal_message_id` (`mid`) → ID de correo  
  - `host` → ESA que procesó el correo  
  - `signature` → estado (accepted/rejected)  
  - `ESA*` → veredictos/políticas  
  - `src`/`dest` → IP origen/destino  

---

## 1. Búsquedas básicas
```spl
index="siem-eu-mta"                              /* todo en el índice */
index="siem-eu-mta" suser="usuario@dominio.com"  /* por remitente */
index="siem-eu-mta" duser="destino@dominio.com"  /* por destinatario */
index="siem-eu-mta" earliest=-24h latest=now     /* últimas 24h */
```

---

## 2. Campos útiles
- `suser` → remitente  
- `duser` → destinatario  
- `internal_message_id` → ID mensaje  
- `host` → ESA  
- `signature` → estado de verificación  
- `ESAOFVerdict` → veredicto  
- `src`, `dest` → IP origen/destino  

---

## 3. Tablas personalizadas
```spl
| rename suser AS Sender, duser AS Recipient, internal_message_id AS MID
| table MID Sender Recipient host
```

Separar fecha en día y hora:
```spl
| eval start_ts=strptime(start,"%a %b %e %H:%M:%S %Y")
| eval Dia=strftime(start_ts,"%Y-%m-%d"), Hora=strftime(start_ts,"%H:%M:%S")
| table Dia Hora MID suser duser host
```

---

## 4. Estadísticas y conteos
Correos por remitente:
```spl
| stats count BY suser | sort - count
```

Correos por dominio:
```spl
| rex field=suser "@(?<domain>[^> ]+)$"
| stats count BY domain | sort - count
```

Mensajes por hora:
```spl
| timechart span=1h count
```

---

## 5. Filtrados avanzados
```spl
signature="rejected"    /* rechazados */
signature="accepted"    /* aceptados */
ESAOFVerdict="NEGATIVE" /* veredicto negativo */
host="CIOBI301926B"     /* por host ESA */
```

---

## 6. Opciones de red

### 6.1 Filtrados de red
```spl
src="180.205.32.105"                /* IP exacta */
src="192.168.1.0/24"                /* rango CIDR */
(src="1.1.1.1" OR src="2.2.2.2")    /* varias IPs */
NOT src="10.*" NOT src="192.168.*"  /* solo públicas */
```

### 6.2 Estadísticas
```spl
| stats count BY src | sort - count | head 20
| stats count BY dest | sort - count | head 20
| stats count BY host | sort - count
```

### 6.3 Visualización
```spl
| timechart span=15m count BY src limit=10
| table _time src dest suser duser host
```

### 6.4 Reputación y anomalías
Detección de spraying:
```spl
| stats dc(duser) AS destinatarios count BY src
| where destinatarios>50
```

IPs con ratio de rechazo:
```spl
| stats sum(eval(signature="rejected")) AS rechazados count AS total BY src
| eval ratio_rechazo=round(rechazados/total*100,2)
| where total>=50 AND ratio_rechazo>=20
```

---

## 7. Extracción de dominios
```spl
| rex field=suser "@(?<sender_domain>[^> ]+)$" | stats count BY sender_domain
| rex field=duser "@(?<recipient_domain>[^> ]+)$" | stats count BY recipient_domain
```

Top 10:
```spl
| rex field=suser "@(?<domain>[^> ]+)$"
| stats count BY domain | sort - count | head 10
```

---

## 8. Manejo de fechas y tiempos
```spl
| eval start_ts=strptime(start,"%a %b %e %H:%M:%S %Y")
| eval Fecha=strftime(start_ts,"%Y-%m-%d"), Mes=strftime(start_ts,"%Y-%m"), Hora=strftime(start_ts,"%H:%M:%S"), DiaSemana=strftime(start_ts,"%A")
```

Agrupar:
```spl
| stats count BY Mes | sort Mes
| stats count BY Hora | sort Hora
```

---

## 9. Consultas avanzadas

### 9.1 Normalización y extracción
Extraer IPs desde `_raw`:
```spl
| rex field=_raw "src=(?<src>(?:\d{1,3}\.){3}\d{1,3})"
```

### 9.2 Correlación por MID
```spl
| transaction internal_message_id startswith=signature="accepted" endswith=signature="delivered" maxspan=2h
```

### 9.3 Ventanas móviles
```spl
| bin _time span=1m | stats count AS c BY _time
| streamstats window=30 avg(c) AS avg30 stdev(c) AS sd30
```

### 9.4 Outliers
```spl
| timechart span=5m count | eventstats avg(count) AS media stdev(count) AS sigma
| where count>media+3*sigma
```

### 9.5 Cardinalidad
```spl
| stats count dc(duser) AS destinatarios_unicos BY suser
```

### 9.6 Enriquecimiento
```spl
| lookup geoip ip AS src OUTPUTNEW country
```

### 9.7 Lookups y tablas maestras
```spl
| lookup whitelist_senders suser OUTPUTNEW tag AS wl_tag | where isnull(wl_tag)
```

---

## 10. Estadísticas avanzadas y KPIs
Ratios de rechazo:
```spl
| rex field=suser "@(?<domain>[^> ]+)$"
| stats sum(eval(signature="rejected")) AS rechazados count AS total BY domain
| eval ratio_rechazo=round(rechazados/total*100,2)
```

Percentiles de tamaño:
```spl
| stats avg(msg_size) AS avg p95(msg_size) AS p95 max(msg_size) AS max
```

---

## 11. Casos especiales: correos sin adjuntos >2 MB
Varias formas:
```spl
| eval size_bytes=coalesce(msg_size,message_size,bytes)
| where size_bytes>2097152
| where attachment_count=0 OR isnull(attachment_count)
```

Si no hay campo de adjuntos → buscar en `_raw`:
```spl
| rex field=_raw max_match=0 "(?i)(Content-Disposition:\s*attachment|filename=)"
| eval attachment_count=mvcount(match)
| where attachment_count=0
```

---

## 12. Guardar búsquedas y alertas
1. Ejecutar búsqueda  
2. **Save As → Report / Alert**  
3. Configurar permisos y condiciones  

---

## 13. Buenas prácticas y macros
- Prefiere `stats` sobre `transaction` en grandes volúmenes.  
- Usa `timechart` con `limit` y `useother=t`.  
- Normaliza fechas con `strftime`.  

Macros útiles:
- `` `idx_mta()` `` → `index="siem-eu-mta"`  
- `` `extraer_dominio(field,out)` `` → `rex field=$field$ "@(?<$out$>[^> ]+)$"`

---

📌 Esta guía consolidada sirve como **manual de referencia rápido** y **colección de consultas listas para usar en Splunk**.
