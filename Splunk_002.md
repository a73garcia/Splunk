# 📖 Guía de Búsquedas en Splunk


---

## 0. Cómo usar esta guía
- Sustituye `index="siem-cisco"` por tu índice real si aplica.
- Si `start` viene como texto (`Wed Oct 1 14:45:43 2025`), conviértelo primero con `strptime` y formatea con `strftime`.
- Campos habituales: `suser` (remitente), `duser` (destinatario), `internal_message_id` o `mid` (ID), `host` (ESA), `signature` (accepted/rejected), `src`/`dest` (red).

---

## 1. Búsquedas básicas
```spl
index="siem-cisco"                              /* todo en el índice */
index="siem-cisco" suser="usuario@dominio.com"  /* remitente */
index="siem-cisco" duser="destino@dominio.com"  /* destinatario */
index="siem-cisco" earliest=-24h latest=now     /* últimas 24h */
```

---

## 2. Campos útiles
- `suser` → Remitente  
- `duser` → Destinatario  
- `internal_message_id` → ID del mensaje (MID)  
- `host` → Gateway o ESA que procesó el correo  
- `start` → Fecha/hora del evento (texto)  
- `signature` → Estado (accepted / rejected)  
- `ESAOFVerdict` → Veredicto (NEGATIVE, SKIPPED, …)  
- `src`, `dest` → IP origen/destino (si aplica)

---

## 3. Tablas personalizadas
```spl
index="siem-cisco"
   | rename suser AS Sender, duser AS Recipient, internal_message_id AS MID
   | table MID Sender Recipient host
```

Separar fecha en día y hora (ISO ordenable):
```spl
index="siem-cisco"
   | eval start_ts=strptime(start,"%a %b %e %H:%M:%S %Y")
   | eval Dia=strftime(start_ts,"%Y-%m-%d"), Hora=strftime(start_ts,"%H:%M:%S")
   | table Dia Hora MID suser duser host
```

---

## 4. Estadísticas y conteos (básico)

Correos por remitente:

```spl
index="siem-cisco"
    | stats count BY suser
    | sort - count
```

Correos por dominio:

```spl
index="siem-cisco"
   | rex field=suser "@(?<domain>[^> ]+)$"
   | stats count BY domain | sort - count
```

Mensajes por horas:

```spl
index="siem-cisco"
   | timechart span=1h count
```

---

## 5. Filtrados avanzados
```spl
index="siem-eu-mta" signature="rejected"       /* rechazados */
index="siem-eu-mta" signature="accepted"       /* aceptados */
index="siem-eu-mta" ESAOFVerdict="NEGATIVE"    /* veredicto negativo */
index="siem-eu-mta" host="CIOBI301926B"        /* por host ESA */
```

---

## 6. Ejemplos prácticos

Ver MIDs de un remitente:
```spl
index="siem-cisco"
   | table _time internal_message_id duser signature
```

Top remitentes sospechosos:
```spl
index="siem-cisco"
   | stats count BY suser
   | sort - count
   | head 10
```

Flujo de correos aceptados por hora:
```spl
index="siem-cisco" signature="accepted"
   | timechart span=1h count
```

---

## 6. Opciones de red

### 6.1 Filtrados de red
```spl
index="siem-cisco" src="180.205.32.105"                 /* IP exacta */
index="siem-cisco" src="192.168.1.0/24"                 /* rango CIDR */
index="siem-cisco" (src="x.x.x.x" OR src="y.y.y.y").    /* varias IPs */
index="siem-cisco" NOT src="10.*" NOT src="192.168.*"   /* públicas */
```

### 6.2 Estadísticas de red

Top IP origen
```spl
index="siem-cisco"
   | stats count BY src
   | sort - count
   | head 20
```

Top IP destino
```spl
index="siem-cisco"
   | stats count BY dest
   | sort - count
   | head 20
```

carga por host
```spl
index="siem-cisco"
   | stats count BY host
   | sort - count
```

### 6.3 Visualización de tráfico

```spl
index="siem-cisco"
   | timechart span=15m count BY src limit=10
```

```spl
index="siem-cisco"
   | table _time src dest suser duser host
```

### 6.4 Reputación y anomalías
```spl
index="siem-cisco"
   | stats dc(duser) AS destinatarios count BY src
   | where destinatarios>50
   | sort - destinatarios
```
```spl
index="siem-cisco"
   | stats sum(eval(signature="rejected")) AS rechazados count AS total BY src
   | eval ratio_rechazo=round(rechazados/total*100,2)
   | where total>=50 AND ratio_rechazo>=20
   | sort - ratio_rechazo
```

```spl
index="siem-cisco" NOT src="10.*" NOT src="192.168.*"            # solo públicas
   | stats dc(duser) AS destinatarios count BY src               # spray detection
```


---

## 7. Extracción de dominios
```spl
index="siem-eu-mta" | rex field=suser "@(?<sender_domain>[^> ]+)$" | stats count BY sender_domain
index="siem-eu-mta" | rex field=duser "@(?<recipient_domain>[^> ]+)$" | stats count BY recipient_domain
index="siem-eu-mta" | rex field=suser "@(?<domain>[^> ]+)$" | stats count BY domain | sort - count | head 10
```

---

## 8. Manejo de fechas y tiempos
```spl
| eval start_ts=strptime(start,"%a %b %e %H:%M:%S %Y")
| eval Fecha=strftime(start_ts,"%Y-%m-%d"), Mes=strftime(start_ts,"%Y-%m"), Hora=strftime(start_ts,"%H:%M:%S"), DiaSemana=strftime(start_ts,"%A")
```
Agrupar por mes:
```spl
| stats count BY Mes | sort Mes
```
Franja horaria:
```spl
| eval Hora=strftime(start_ts,"%H") | stats count BY Hora | sort Hora
```

---

## 9. Consultas avanzadas

### 9.1 Normalización y extracción
Extraer IPs de `_raw` si no vienen mapeadas:
```spl
| rex field=_raw "src=(?<src>(?:\d{1,3}\.){3}\d{1,3})"
| rex field=_raw "dst=(?<dest>(?:\d{1,3}\.){3}\d{1,3})"
| eval src_subnet=replace(src,"(\d+\.\d+\.\d+)\.\d+","\1.0/24")
| eval is_private=if(match(src,"^10\.|^192\.168\.|^172\.(1[6-9]|2[0-9]|3[0-1])\."),"yes","no")
```

### 9.2 Correlación por MID (transaction)
Agrupar eventos del mismo mensaje:
```spl
index="siem-eu-mta"
| transaction internal_message_id startswith=signature="accepted" endswith=signature="delivered" keepevicted=t maxspan=2h
| eval dur_seg=round(duration,2)
| table internal_message_id suser duser host dur_seg eventcount
```
Alternativa sin `transaction` (más escalable):
```spl
index="siem-eu-mta"
| stats earliest(_time) AS first latest(_time) AS last values(signature) AS signatures values(host) AS hosts count AS events BY internal_message_id suser duser
| eval dur_seg=round(last-first,2)
```

### 9.3 Ventanas móviles y rachas (streamstats)
Tasa por minuto y media móvil:
```spl
index="siem-eu-mta"
| bin _time span=1m
| stats count AS c BY _time
| streamstats window=30 avg(c) AS avg30 stdev(c) AS sd30
| eval z=if(sd30>0,(c-avg30)/sd30,null())
| table _time c avg30 sd30 z
```
Rachas de errores por IP:
```spl
index="siem-eu-mta" signature="rejected"
| bin _time span=5m
| stats count AS rej BY _time src
| streamstats current=f window=3 sum(rej) AS rej_prev BY src
| eval spike=rej>2*coalesce(rej_prev,0)
```

### 9.4 Detección de picos y outliers
Usando desvíos estándar:
```spl
index="siem-eu-mta"
| timechart span=5m count
| eventstats avg(count) AS media stdev(count) AS sigma
| eval outlier=if(count>media+3*sigma,1,0)
| where outlier=1
```
O percentiles (robusto):
```spl
index="siem-eu-mta"
| timechart span=5m count
| eventstats perc95(count) AS p95
| where count>p95
```

### 9.5 Distintos y cardinalidad
Correos por remitente con nº de destinatarios únicos:
```spl
index="siem-eu-mta"
| stats count dc(duser) AS destinatarios_unicos BY suser
| sort - destinatarios_unicos
```

### 9.6 Enriquecimiento (GeoIP/ASN/IOC)
> Requiere lookups cargados: `geoip`, `asn`, `ti_blocklist` (ajusta nombres).
```spl
| lookup geoip ip AS src OUTPUTNEW country AS src_country city AS src_city
| lookup asn  ip AS src OUTPUTNEW asn AS src_asn asn_org
| lookup ti_blocklist ip AS src OUTPUTNEW tag AS ti_tag severity AS ti_sev
| table _time src src_country src_city src_asn asn_org ti_tag ti_sev suser duser
```

### 9.7 Uniones/Lookups y tablas maestras
Cruce remitentes con lista blanca:
```spl
| lookup whitelist_senders suser OUTPUTNEW tag AS wl_tag
| where isnull(wl_tag)
```
Join con eventos de otra sourcetype por `internal_message_id` (no recomendado a gran escala, usar `stats`/`appendpipe` cuando sea posible):
```spl
index="siem-eu-mta" | fields internal_message_id suser duser host
| join type=inner internal_message_id [
  search index="siem-eu-mta-audit" | fields internal_message_id action user
]
```

---

## 10. Estadísticas avanzadas y KPIs

### 10.1 Ratios y tasas
Tasa de rechazo por dominio del remitente:
```spl
index="siem-eu-mta"
| rex field=suser "@(?<domain>[^> ]+)$"
| stats sum(eval(signature="rejected")) AS rechazados count AS total BY domain
| eval ratio_rechazo=round(rechazados/total*100,2)
| where total>=100
| sort - ratio_rechazo
```
Mensajes/minuto (RPM):
```spl
index="siem-eu-mta"
| bin _time span=1m
| stats count AS rpm BY _time
```

### 10.2 Percentiles y tamaños
Si tienes tamaño de mensaje `msg_size` (bytes):
```spl
index="siem-eu-mta"
| stats avg(msg_size) AS avg p50(msg_size) AS p50 p90(msg_size) AS p90 p95(msg_size) AS p95 max(msg_size) AS max
| eval avg=round(avg/1024,2), p50=round(p50/1024,2), p90=round(p90/1024,2), p95=round(p95/1024,2), max=round(max/1024,2)
```

### 10.3 Series temporales multi-split
Top 5 dominios por hora (aplanado a 5 series):
```spl
index="siem-eu-mta"
| rex field=suser "@(?<domain>[^> ]+)$"
| timechart span=1h count BY domain limit=5 useother=t otherSeries="otros"
```

### 10.4 Heatmaps y matrices
IP origen vs host (matriz):
```spl
index="siem-eu-mta"
| stats count BY src host
| xyseries src host count
```

### 10.5 Top N con “otros”
Top remitentes con bucket “otros”:
```spl
index="siem-eu-mta"
| stats count BY suser
| sort - count
| head 9
| appendpipe [ stats sum(count) AS count | eval suser="otros" ]
```

---

## 11. Guardar búsquedas / permisos
1. Ejecuta la búsqueda → **Save As → Saved Search** o **Report**.  
2. Define permisos (privado / compartido por app / roles).  
3. Para alertas: **Save As → Alert** y configura condición + acción (email/webhook).

---

## 12. Anexos: macros y buenas prácticas

### Macros útiles (ejemplos)
- `` `idx_mta()` `` → `index="siem-eu-mta"`  
- `` `solo_publicas(field)` `` → `NOT $field$="10.*" NOT $field$="192.168.*" NOT $field$="172.1[6-9].*" NOT $field$="172.2[0-9].*" NOT $field$="172.3[0-1].*"`  
- `` `extraer_dominio(field,out)` `` → `rex field=$field$ "@(?<$out$>[^> ]+)$"`

### Buenas prácticas
- Prefiere `stats`/`eventstats`/`streamstats` antes que `transaction` en volúmenes altos.
- Usa `timechart` con `limit` y `useother=t` para limitar series.
- Evita `join` en datasets grandes; utiliza `lookup` o `stats` para correlacionar.
- Normaliza fechas a ISO (`%Y-%m-%d`) para ordenación y tabulación.
- Guarda búsquedas frecuentes como Report; condiciones → Alert.

---

> **Nota**: Ajusta los nombres de campos (`internal_message_id` vs `mid`, `signature`, `ESA*`) a tu esquema real de ingesta.
