# 📖 Guía de Búsquedas en Splunk (Cisco ESA / Correo + Red)

Esta guía recopila ejemplos prácticos de búsquedas, filtrados, visualizaciones y **estadísticas avanzadas** en Splunk para logs de Cisco ESA (correo) y señales de red.

---

## 0. Cómo usar esta guía
- Sustituye `index="siem-eu-mta"` por tu índice real si aplica.
- Si `start` viene como texto (`Wed Oct 1 14:45:43 2025`), conviértelo primero con `strptime` y formatea con `strftime`.
- Campos habituales: `suser` (remitente), `duser` (destinatario), `internal_message_id` o `mid` (ID), `host` (ESA), `signature` (accepted/rejected), `ESA*` (veredictos/políticas), `src`/`dest` (red).

---

## 1. Búsquedas básicas
```spl
index="siem-eu-mta"                              /* todo en el índice */
index="siem-eu-mta" suser="usuario@dominio.com"  /* remitente */
index="siem-eu-mta" duser="destino@dominio.com"  /* destinatario */
index="siem-eu-mta" earliest=-24h latest=now     /* últimas 24h */
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
index="siem-eu-mta"
| rename suser AS Sender, duser AS Recipient, internal_message_id AS MID
| table MID Sender Recipient host
```

Separar fecha en día y hora (ISO ordenable):
```spl
... | eval start_ts=strptime(start,"%a %b %e %H:%M:%S %Y")
| eval Dia=strftime(start_ts,"%Y-%m-%d"), Hora=strftime(start_ts,"%H:%M:%S")
| table Dia Hora MID suser duser host
```

---
