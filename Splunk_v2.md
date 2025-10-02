
# 📖 Guía Unificada de Búsquedas en Splunk (Cisco ESA / Correo + Red) — con ejemplos de salida

Esta guía recopila ejemplos prácticos de **búsquedas, filtrados, estadísticas y visualizaciones en Splunk**, aplicados a **logs de correo (Cisco ESA)** y **tráfico de red**.  
Cada consulta incluye un **ejemplo de salida** (datos simulados) para que veas el formato esperado en Splunk.

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
```

**Salida (ejemplo):**
```
_time                host          suser                     duser                        signature    internal_message_id
2025-09-30 08:01:12  ESA01         alice@acme.com            bob@contoso.com              accepted     1.2.3.4-AAA
2025-09-30 08:01:45  ESA02         spammer@bad.biz           team@acme.com                rejected     1.2.3.4-BBB
```

```spl
index="siem-eu-mta" suser="usuario@dominio.com"  /* por remitente */
```
**Salida (ejemplo):**
```
_time                host   suser                  duser                  signature    internal_message_id
2025-09-30 09:15:22  ESA01  usuario@dominio.com    cliente@otro.com       accepted     1.2.3.4-CCC
```

```spl
index="siem-eu-mta" duser="destino@dominio.com"  /* por destinatario */
```
**Salida (ejemplo):**
```
_time                host   suser               duser                     signature    internal_message_id
2025-09-30 10:02:04  ESA02  facturas@acme.com   destino@dominio.com       accepted     1.2.3.4-DDD
```

```spl
index="siem-eu-mta" earliest=-24h latest=now     /* últimas 24h */
```
**Salida (ejemplo):**
```
_time                host   suser             duser                  signature    internal_message_id
2025-09-30 12:12:55  ESA01  alerts@acme.com   ops@acme.com           accepted     1.2.3.4-EEE
```

---

## 2. Campos útiles
*(sin consulta específica; referencia de campos y significado)*

---

## 3. Tablas personalizadas

```spl
index="siem-eu-mta"
| rename suser AS Sender, duser AS Recipient, internal_message_id AS MID
| table MID Sender Recipient host
```
**Salida (ejemplo):**
```
MID        Sender            Recipient           host
1.2.3.4-AAA alice@acme.com   bob@contoso.com     ESA01
1.2.3.4-BBB spammer@bad.biz  team@acme.com       ESA02
```

Separar fecha en día y hora:
```spl
index="siem-eu-mta"
| eval start_ts=strptime(start,"%a %b %e %H:%M:%S %Y")
| eval Dia=strftime(start_ts,"%Y-%m-%d"), Hora=strftime(start_ts,"%H:%M:%S")
| table Dia Hora internal_message_id suser duser host
```
**Salida (ejemplo):**
```
Dia         Hora      internal_message_id  suser             duser              host
2025-09-30  08:01:12  1.2.3.4-AAA         alice@acme.com    bob@contoso.com    ESA01
```

---

## 4. Estadísticas y conteos

Correos por remitente:
```spl
index="siem-eu-mta" | stats count BY suser | sort - count
```
**Salida (ejemplo):**
```
suser               count
alerts@acme.com     1520
alice@acme.com       230
spammer@bad.biz      120
```

Correos por dominio:
```spl
index="siem-eu-mta"
| rex field=suser "@(?<domain>[^> ]+)$"
| stats count BY domain | sort - count
```
**Salida (ejemplo):**
```
domain         count
acme.com       1850
contoso.com     620
bad.biz         120
```

Mensajes por hora:
```spl
index="siem-eu-mta" | timechart span=1h count
```
**Salida (ejemplo):**
```
_time                count
2025-09-30 00:00:00  80
2025-09-30 01:00:00  95
...
2025-09-30 23:00:00  140
```

---

## 5. Filtrados avanzados

```spl
index="siem-eu-mta" signature="rejected"
```
**Salida (ejemplo):**
```
_time                suser               duser                signature  reason
2025-09-30 08:01:45  spammer@bad.biz     team@acme.com        rejected   policy:BLOCKLIST
```

```spl
index="siem-eu-mta" signature="accepted"
```
**Salida (ejemplo):**
```
_time                suser              duser                 signature
2025-09-30 09:03:10  alice@acme.com     bob@contoso.com       accepted
```

```spl
index="siem-eu-mta" ESAOFVerdict="NEGATIVE"
```
**Salida (ejemplo):**
```
_time                suser            duser              ESAOFVerdict signature
2025-09-30 10:22:40  spam@phish.io    user@acme.com     NEGATIVE     rejected
```

```spl
index="siem-eu-mta" host="CIOBI301926B"
```
**Salida (ejemplo):**
```
_time                host           suser            duser             signature
2025-09-30 12:50:05  CIOBI301926B   alerts@acme.com  ops@acme.com     accepted
```

---

## 6. Opciones de red

### 6.1 Filtrados de red
```spl
index="siem-eu-mta" src="180.205.32.105"
```
**Salida (ejemplo):**
```
_time                src            suser             duser             signature
2025-09-30 07:31:02  180.205.32.105 spam@bad.biz      ceo@acme.com     rejected
```

```spl
index="siem-eu-mta" src="192.168.1.0/24"
```
**Salida (ejemplo):**
```
_time                src            suser           duser           signature
2025-09-30 11:05:19  192.168.1.25   svc@mailgw      noc@acme.com    accepted
```

```spl
index="siem-eu-mta" (src="1.1.1.1" OR src="2.2.2.2")
```
**Salida (ejemplo):**
```
_time                src        suser             duser            signature
2025-09-30 13:11:42  1.1.1.1    alerts@acme.com   ops@acme.com    accepted
```

```spl
index="siem-eu-mta" NOT src="10.*" NOT src="192.168.*"
```
**Salida (ejemplo):**
```
_time                src           suser            duser             signature
2025-09-30 14:01:05  52.23.10.2    mail@vendor.io   buyer@acme.com   accepted
```

### 6.2 Estadísticas
```spl
index="siem-eu-mta" | stats count BY src | sort - count | head 20
```
**Salida (ejemplo):**
```
src             count
52.23.10.2      980
1.1.1.1         320
180.205.32.105  120
```

```spl
index="siem-eu-mta" | stats count BY dest | sort - count | head 20
```
**Salida (ejemplo):**
```
dest           count
10.0.0.15      1450
10.0.0.21       980
```

```spl
index="siem-eu-mta" | stats count BY host | sort - count
```
**Salida (ejemplo):**
```
host    count
ESA01   2100
ESA02   1950
```

### 6.3 Visualización
```spl
index="siem-eu-mta" | timechart span=15m count BY src limit=10
```
**Salida (ejemplo simplificado):**
```
_time                52.23.10.2  1.1.1.1  180.205.32.105  otros
2025-09-30 10:00:00  10          2        1               7
2025-09-30 10:15:00  12          3        0               9
```

```spl
index="siem-eu-mta" | table _time src dest suser duser host
```
**Salida (ejemplo):**
```
_time                src          dest        suser           duser           host
2025-09-30 10:22:15  52.23.10.2   10.0.0.15  alerts@acme.com ops@acme.com    ESA02
```

### 6.4 Reputación y anomalías
```spl
index="siem-eu-mta"
| stats dc(duser) AS destinatarios count BY src
| where destinatarios>50
| sort - destinatarios
```
**Salida (ejemplo):**
```
src          destinatarios  count
52.23.10.2   320            980
```

```spl
index="siem-eu-mta"
| stats sum(eval(signature="rejected")) AS rechazados count AS total BY src
| eval ratio_rechazo=round(rechazados/total*100,2)
| where total>=50 AND ratio_rechazo>=20
| sort - ratio_rechazo
```
**Salida (ejemplo):**
```
src             rechazados  total  ratio_rechazo
180.205.32.105  40          120    33.33
```

---

## 7. Extracción de dominios

```spl
index="siem-eu-mta" | rex field=suser "@(?<sender_domain>[^> ]+)$" | stats count BY sender_domain
```
**Salida (ejemplo):**
```
sender_domain  count
acme.com       1850
contoso.com     620
```

```spl
index="siem-eu-mta" | rex field=duser "@(?<recipient_domain>[^> ]+)$" | stats count BY recipient_domain
```
**Salida (ejemplo):**
```
recipient_domain  count
acme.com          2100
contoso.com        420
```

```spl
index="siem-eu-mta" | rex field=suser "@(?<domain>[^> ]+)$" | stats count BY domain | sort - count | head 10
```
**Salida (ejemplo):**
```
domain       count
acme.com     1850
contoso.com   620
bad.biz       120
```

---

## 8. Manejo de fechas y tiempos

```spl
index="siem-eu-mta"
| eval start_ts=strptime(start,"%a %b %e %H:%M:%S %Y")
| eval Fecha=strftime(start_ts,"%Y-%m-%d"), Mes=strftime(start_ts,"%Y-%m"), Hora=strftime(start_ts,"%H:%M:%S"), DiaSemana=strftime(start_ts,"%A")
| table Fecha Mes Hora DiaSemana suser duser
```
**Salida (ejemplo):**
```
Fecha       Mes       Hora      DiaSemana  suser            duser
2025-09-30  2025-09   08:01:12  Tuesday    alice@acme.com   bob@contoso.com
```

Agrupar por mes:
```spl
index="siem-eu-mta" | eval start_ts=strptime(start,"%a %b %e %H:%M:%S %Y") | eval Mes=strftime(start_ts,"%Y-%m") | stats count BY Mes | sort Mes
```
**Salida (ejemplo):**
```
Mes       count
2025-08   51000
2025-09   57500
```

Franja horaria:
```spl
index="siem-eu-mta" | eval start_ts=strptime(start,"%a %b %e %H:%M:%S %Y") | eval Hora=strftime(start_ts,"%H") | stats count BY Hora | sort Hora
```
**Salida (ejemplo):**
```
Hora count
00   80
01   95
...
23   140
```

---

## 9. Consultas avanzadas

### 9.1 Normalización y extracción
```spl
index="siem-eu-mta"
| rex field=_raw "src=(?<src>(?:\d{1,3}\.){3}\d{1,3})"
| rex field=_raw "dst=(?<dest>(?:\d{1,3}\.){3}\d{1,3})"
| eval src_subnet=replace(src,"(\d+\.\d+\.\d+)\.\d+","\1.0/24")
| eval is_private=if(match(src,"^10\.|^192\.168\.|^172\.(1[6-9]|2[0-9]|3[0-1])\."),"yes","no")
| table _time src dest src_subnet is_private
```
**Salida (ejemplo):**
```
_time                src           dest        src_subnet      is_private
2025-09-30 10:05:55  192.168.1.25  10.0.0.15  192.168.1.0/24  yes
```

### 9.2 Correlación por MID (transaction y alternativa)
```spl
index="siem-eu-mta"
| transaction internal_message_id startswith=signature="accepted" endswith=signature="delivered" keepevicted=t maxspan=2h
| eval dur_seg=round(duration,2)
| table internal_message_id suser duser host dur_seg eventcount
```
**Salida (ejemplo):**
```
internal_message_id  suser           duser            host   dur_seg  eventcount
1.2.3.4-AAA          alice@acme.com  bob@contoso.com  ESA01  12.35    4
```

Alternativa escalable (sin `transaction`):
```spl
index="siem-eu-mta"
| stats earliest(_time) AS first latest(_time) AS last values(signature) AS signatures values(host) AS hosts count AS events BY internal_message_id suser duser
| eval dur_seg=round(last-first,2)
| table internal_message_id suser duser hosts signatures dur_seg events
```
**Salida (ejemplo):**
```
internal_message_id  suser           duser            hosts        signatures              dur_seg  events
1.2.3.4-AAA          alice@acme.com  bob@contoso.com  ESA01,ESA02  accepted,delivered      12.35    4
```

### 9.3 Ventanas móviles y rachas (streamstats)
```spl
index="siem-eu-mta"
| bin _time span=1m
| stats count AS c BY _time
| streamstats window=30 avg(c) AS avg30 stdev(c) AS sd30
| eval z=if(sd30>0,(c-avg30)/sd30,null())
| table _time c avg30 sd30 z
```
**Salida (ejemplo):**
```
_time                c   avg30  sd30  z
2025-09-30 10:00:00  95  82.1   12.3  1.04
```

Rachas de errores por IP:
```spl
index="siem-eu-mta" signature="rejected"
| bin _time span=5m
| stats count AS rej BY _time src
| streamstats current=f window=3 sum(rej) AS rej_prev BY src
| eval spike=rej>2*coalesce(rej_prev,0)
| where spike=1
```
**Salida (ejemplo):**
```
_time                src            rej  rej_prev  spike
2025-09-30 11:15:00  180.205.32.105 40   15        1
```

### 9.4 Detección de picos y outliers
```spl
index="siem-eu-mta"
| timechart span=5m count
| eventstats avg(count) AS media stdev(count) AS sigma
| eval outlier=if(count>media+3*sigma,1,0)
| where outlier=1
```
**Salida (ejemplo):**
```
_time                count  media  sigma  outlier
2025-09-30 12:35:00  520    310    60     1
```

Percentiles (robusto):
```spl
index="siem-eu-mta"
| timechart span=5m count
| eventstats perc95(count) AS p95
| where count>p95
```
**Salida (ejemplo):**
```
_time                count  p95
2025-09-30 13:10:00  480    455
```

### 9.5 Distintos y cardinalidad
```spl
index="siem-eu-mta"
| stats count dc(duser) AS destinatarios_unicos BY suser
| sort - destinatarios_unicos
```
**Salida (ejemplo):**
```
suser             count  destinatarios_unicos
marketing@acme.com 850    410
```

### 9.6 Enriquecimiento (GeoIP/ASN/IOC)
```spl
index="siem-eu-mta"
| lookup geoip ip AS src OUTPUTNEW country AS src_country city AS src_city
| lookup asn  ip AS src OUTPUTNEW asn AS src_asn asn_org
| table _time src src_country src_city src_asn asn_org suser duser
```
**Salida (ejemplo):**
```
_time                src          src_country  src_city  src_asn  asn_org           suser            duser
2025-09-30 14:12:11  52.23.10.2   US           Ashburn   AS14618  AMAZON-AES        alerts@acme.com  ops@acme.com
```

### 9.7 Uniones/Lookups y tablas maestras
Lista blanca de remitentes (excluir permitidos):
```spl
index="siem-eu-mta"
| lookup whitelist_senders suser OUTPUTNEW tag AS wl_tag
| where isnull(wl_tag)
| stats count BY suser
```
**Salida (ejemplo):**
```
suser               count
unknown@vendor.io   92
```

Join por `internal_message_id` (ejemplo controlado):
```spl
index="siem-eu-mta" | fields internal_message_id suser duser host
| join type=inner internal_message_id [
  search index="siem-eu-mta-audit" | fields internal_message_id action user
]
| table internal_message_id suser duser host action user
```
**Salida (ejemplo):**
```
internal_message_id  suser           duser           host  action   user
1.2.3.4-AAA          alice@acme.com  bob@contoso.com ESA01 quarantine admin
```

---

## 10. Estadísticas avanzadas y KPIs

### 10.1 Ratios y tasas
```spl
index="siem-eu-mta"
| rex field=suser "@(?<domain>[^> ]+)$"
| stats sum(eval(signature="rejected")) AS rechazados count AS total BY domain
| eval ratio_rechazo=round(rechazados/total*100,2)
| where total>=100
| sort - ratio_rechazo
```
**Salida (ejemplo):**
```
domain     rechazados  total  ratio_rechazo
bad.biz    90          120    75.00
contoso.com 120        620    19.35
```

Mensajes/minuto (RPM):
```spl
index="siem-eu-mta"
| bin _time span=1m
| stats count AS rpm BY _time
```
**Salida (ejemplo):**
```
_time                rpm
2025-09-30 10:00:00  95
2025-09-30 10:01:00  101
```

### 10.2 Percentiles y tamaños
```spl
index="siem-eu-mta"
| stats avg(msg_size) AS avg p50(msg_size) AS p50 p90(msg_size) AS p90 p95(msg_size) AS p95 max(msg_size) AS max
| eval avg=round(avg/1024,2), p50=round(p50/1024,2), p90=round(p90/1024,2), p95=round(p95/1024,2), max=round(max/1024,2)
```
**Salida (ejemplo):**
```
avg   p50   p90    p95    max
42.1  15.2  98.3   120.5  358.8
```

### 10.3 Series temporales multi-split
```spl
index="siem-eu-mta"
| rex field=suser "@(?<domain>[^> ]+)$"
| timechart span=1h count BY domain limit=5 useother=t otherSeries="otros"
```
**Salida (ejemplo):**
```
_time                acme.com  contoso.com  bad.biz  otros
2025-09-30 08:00:00  60        22           4        14
```

### 10.4 Heatmaps y matrices
```spl
index="siem-eu-mta"
| stats count BY src host
| xyseries src host count
```
**Salida (ejemplo):**
```
src           ESA01  ESA02
52.23.10.2    120    860
1.1.1.1       50     270
```

### 10.5 Top N con “otros”
```spl
index="siem-eu-mta"
| stats count BY suser
| sort - count
| head 9
| appendpipe [ stats sum(count) AS count | eval suser="otros" ]
```
**Salida (ejemplo):**
```
suser               count
alerts@acme.com     1520
marketing@acme.com   850
...
otros                430
```

---

## 11. Casos especiales: correos sin adjuntos >2 MB

Usando campo de tamaño en bytes:
```spl
index="siem-eu-mta"
| eval size_bytes = coalesce(msg_size, message_size, bytes, msgbytes)
| where size_bytes > 2097152
| where (attachment_count=0 OR isnull(attachment_count) OR has_attachment=0)
| eval size_MB = round(size_bytes/1024/1024,2)
| rename internal_message_id AS MID, suser AS Sender, duser AS Recipient
| table _time MID Sender Recipient host size_MB attachment_count
```
**Salida (ejemplo):**
```
_time                MID        Sender            Recipient          host  size_MB  attachment_count
2025-09-30 09:41:20  1.2.3.4-ZZ big@acme.com      ops@acme.com       ESA02  3.25     0
```

Si existe `has_attachment`:
```spl
index="siem-eu-mta"
| eval size_bytes = coalesce(msg_size, message_size, bytes, msgbytes)
| where size_bytes > 2097152
| where isnull(has_attachment) OR has_attachment=0
| eval size_MB = round(size_bytes/1024/1024,2)
| table _time internal_message_id suser duser host size_MB has_attachment
```
**Salida (ejemplo):**
```
_time                internal_message_id  suser          duser           host  size_MB  has_attachment
2025-09-30 10:12:01  1.2.3.4-QQ           big@acme.com   ops@acme.com    ESA01  2.50     0
```

Detección por regex en `_raw`:
```spl
index="siem-eu-mta"
| eval size_bytes = coalesce(msg_size, message_size, bytes, msgbytes)
| where size_bytes > 2097152
| rex field=_raw max_match=0 "(?i)(Content-Disposition:\s*attachment|filename=|Content-Type:\s*multipart/mixed)"
| eval attachment_count = mvcount(match)
| where attachment_count=0 OR isnull(attachment_count)
| eval size_MB = round(size_bytes/1024/1024,2)
| table _time internal_message_id suser duser host size_MB attachment_count
```
**Salida (ejemplo):**
```
_time                internal_message_id  suser        duser         host  size_MB  attachment_count
2025-09-30 10:44:30  1.2.3.4-PP           big@acme.com ops@acme.com  ESA02  2.10     0
```

Tamaño en KB/MB:
```spl
index="siem-eu-mta"
| eval size_bytes = case(
    isnum(msg_size_kb), msg_size_kb*1024,
    isnum(msg_size_mb), msg_size_mb*1024*1024,
    true(), null()
)
| where size_bytes > 2097152
| where attachment_count=0 OR isnull(attachment_count)
| eval size_MB = round(size_bytes/1024/1024,2)
| table _time internal_message_id suser duser host size_MB
```
**Salida (ejemplo):**
```
_time                internal_message_id  suser        duser         host  size_MB
2025-09-30 11:02:11  1.2.3.4-OO           big@acme.com ops@acme.com  ESA01  2.60
```

Excluir imágenes inline (opcional):
```spl
index="siem-eu-mta"
| eval size_bytes = coalesce(msg_size, message_size, bytes)
| where size_bytes > 2097152
| rex field=_raw "(?i)Content-ID:\s*<" 
| eval inline_images = if(isnull(match),0,1)
| where inline_images=0
| rex field=_raw max_match=0 "(?i)(Content-Disposition:\s*attachment|filename=|Content-Type:\s*multipart/mixed)"
| eval attachment_count = mvcount(match)
| where attachment_count=0 OR isnull(attachment_count)
| eval size_MB = round(size_bytes/1024/1024,2)
| table _time internal_message_id suser duser host size_MB inline_images attachment_count
```
**Salida (ejemplo):**
```
_time                internal_message_id  suser        duser         host  size_MB  inline_images  attachment_count
2025-09-30 11:20:05  1.2.3.4-NN           big@acme.com ops@acme.com  ESA02  3.00     0             0
```

---

## 12. Guardar búsquedas y alertas

Pasos para guardar:
1. Ejecutar la búsqueda → **Save As → Saved Search** o **Report**.  
2. Definir permisos (privado / app / roles).  
3. Para alertas: **Save As → Alert** y configurar condición + acción (email/webhook).

**Salida esperada (meta-ejemplo):** se crea un entry en *Searches, Reports, and Alerts* accesible por nombre.

---

## 13. Buenas prácticas y macros

- Prefiere `stats`/`eventstats`/`streamstats` antes que `transaction` en volúmenes altos.  
- Usa `timechart` con `limit` y `useother=t` para limitar series.  
- Normaliza fechas a ISO (`%Y-%m-%d`) para ordenación y tabulación.  
- Evita `join` salvo datasets pequeños; usa `lookup` o `stats` para correlación.

**Macros útiles (ejemplos):**
- `` `idx_mta()` `` → `index="siem-eu-mta"`  
- `` `solo_publicas(field)` `` → `NOT $field$="10.*" NOT $field$="192.168.*" NOT $field$="172.1[6-9].*" NOT $field$="172.2[0-9].*" NOT $field$="172.3[0-1].*"`  
- `` `extraer_dominio(field,out)` `` → `rex field=$field$ "@(?<$out$>[^> ]+)$"`  

**Salida (ejemplo) de macro aplicada:**
```
domain       count
acme.com     1850
contoso.com   620
```

---

> **Nota**: Todos los datos mostrados son simulados y sirven únicamente para ilustrar el formato de salida de Splunk.
