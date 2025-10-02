# 📖 Guía de Búsquedas en Splunk (Cisco ESA / Correo + Red)

Esta guía recopila ejemplos prácticos de búsquedas, filtrados y visualizaciones en Splunk, 
enfocadas al análisis de **correo electrónico** y **red** a partir de logs de Cisco ESA.

---

## 1. Búsquedas básicas

```spl
index="siem-eu-mta"                              # todo en el índice
index="siem-eu-mta" suser="usuario@dominio.com"  # filtrar remitente
index="siem-eu-mta" duser="destino@dominio.com"  # filtrar destinatario
index="siem-eu-mta" earliest=-24h latest=now     # últimas 24h
```

---

## 2. Campos útiles

- `suser` → Remitente  
- `duser` → Destinatario  
- `internal_message_id` → ID del mensaje (MID)  
- `host` → Gateway o ESA que procesó el correo  
- `start` → Fecha/hora del evento  
- `signature` → Estado de verificación  
- `ESAOFVerdict` → Veredicto (NEGATIVE, SKIPPED, …)  

---

## 3. Tablas personalizadas

```spl
| rename suser AS Sender, duser AS Recipient
| table internal_message_id Sender Recipient
```

Separar fecha en día y hora:
```spl
| eval start_ts = strptime(start,"%a %b %e %H:%M:%S %Y")
| eval Dia=strftime(start_ts,"%Y-%m-%d"), Hora=strftime(start_ts,"%H:%M:%S")
| table Dia Hora internal_message_id suser duser
```

---

## 4. Estadísticas y conteos

Correos por remitente:
```spl
| stats count BY suser | sort - count
```

Correos por dominio:
```spl
| rex field=suser "@(?<domain>.+)$"
| stats count BY domain | sort - count
```

Mensajes por hora:
```spl
| timechart span=1h count
```

---

## 5. Filtrados avanzados

```spl
signature="rejected"    # Correos rechazados
signature="accepted"    # Mensajes aceptados
ESAOFVerdict="NEGATIVE" # Correos con veredicto negativo
host="CIOBI301926B"     # Filtrar por host
```

---

## 6. Ejemplos prácticos

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

---

## 7. Opciones de red

### 7.1 Filtrados de red

```spl
src="180.205.32.105"            # IP exacta
src="192.168.1.0/24"            # rango CIDR
(src="x.x.x.x" OR src="y.y.y.y")# varias IPs
host="CIOBI301926B"             # host específico
```

### 7.2 Estadísticas

```spl
| stats count BY src | sort - count | head 20     # top IP origen
| stats count BY dest | sort - count | head 20    # top IP destino
| stats count BY host | sort - count              # carga por host
```

### 7.3 Visualización

```spl
| timechart span=1h count BY src limit=10
| table _time src dest suser duser host
```

### 7.4 Reputación de red

```spl
NOT src="10.*" NOT src="192.168.*"                # solo públicas
| stats dc(duser) AS destinatarios count BY src   # spray detection
```

IPs con ratio de rechazo:
```spl
| stats sum(eval(signature="rejected")) AS rechazados count AS total BY src
| eval ratio_rechazo=round(rechazados/total*100,2)
| where total>=50 AND ratio_rechazo>=20
```

---

## 8. Extracción de dominios

Dominio de remitente:
```spl
| rex field=suser "@(?<sender_domain>[^> ]+)$"
| stats count BY sender_domain
```

Dominio de destinatario:
```spl
| rex field=duser "@(?<recipient_domain>[^> ]+)$"
| stats count BY recipient_domain
```

Top 10 dominios:
```spl
| rex field=suser "@(?<domain>[^> ]+)$"
| stats count BY domain | sort - count | head 10
```

---

## 9. Manejo de fechas y tiempos

Convertir campo `start` en timestamp:
```spl
| eval start_ts = strptime(start,"%a %b %e %H:%M:%S %Y")
```

Separar fecha y hora:
```spl
| eval Dia=strftime(start_ts,"%Y-%m-%d"), Hora=strftime(start_ts,"%H:%M:%S")
```

Agrupar por mes:
```spl
| eval Mes=strftime(start_ts,"%Y-%m")
| stats count BY Mes | sort Mes
```

Conteo por día de la semana:
```spl
| eval DiaSemana=strftime(start_ts,"%A")
| stats count BY DiaSemana
```

Conteo por franja horaria:
```spl
| eval Hora=strftime(start_ts,"%H")
| stats count BY Hora | sort Hora
```

---

## 10. Guardar búsquedas

1. Ejecuta la búsqueda en Splunk.  
2. Haz clic en **Save As → Saved Search**.  
3. Pon un nombre y descripción.  
4. Disponible en *Searches, Reports and Alerts*.  

---

📌 **Recomendación**: Guardar las búsquedas más comunes como **Reports** y las que requieren monitoreo como **Alerts**.
