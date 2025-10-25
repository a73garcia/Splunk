# CrowdStrike Falcon LogScale 

## Busqueda tipo en SPLUNK

```spl
index=siem-sp-cisco host="*.maquina.grupo.com" cef_6_header="Consolidated Log Event"
	| eval HoraE = coalesce(strptime(start, "%a %b %d %H:%M:%S %Y"), _time)
      	, HoraS = strptime(end,   "%a %b %d %H:%M:%S %Y")
      	, "Size(MB)" = round(ESAMsgSize/1048576, 2)
     		, HostRaw = mvindex(split(host, "."), 0)
      	, SPF = mvindex(split(SPF_verdict, ","), 5)
      	, Adjunto = mvindex(split(ESAAttachmentDetails, ","), 1)
	| eval DKIM = case(DKIM_verdict=="pass","pass", DKIM_verdict=="permfail","permfail", DKIM_verdict=="tempfail","tempfail", true(),"Other")
	| rename ESAMID AS MID
        user AS Sender
        duser AS Recipient
        act AS Accion
        cs2 AS IP_Pais
        cs1 AS Politica
        cs3 AS Categoria
        cs6 AS Reputacion
        antivirus_verdict AS AV_Verdict
        src_user_domain AS Domain
        recipient_status AS Status
        DMARC_verdict AS DMARC
	| eval ESA_Num = tonumber(replace(HostRaw,"c3s2",""))
      	, Nodo = printf("ESA%02d", ESA_Num)
	| eval CES = case(
      	like(host,"%.maquina.grupo1.com"), "Grupo1",
      	like(host,"%.maquina.grupo2.com"), "Grupo2",
      	like(host,"%.maquina.grupo3.com"), "Grupo3",
      	like(host,"%.maquina.grupo4.com"), "Grupo4",
      	like(host,"%.maquina.grupo5.com"), "Grupo5",
      	true(), "Otro"
  		)
	| eval Recipient = split(Recipient,";")
	| eval Dia = strftime(HoraE, "%d/%m/%Y")
      	, Entrada = strftime(HoraE, "%H:%M")
      	, Salida  = if(isnum(HoraS), strftime(HoraS, "%H:%M"), null())
      	, QueueTime_s = if(isnum(HoraS) AND isnum(HoraE), HoraS-HoraE, null())
      	, QueueTime_m = if(isnum(QueueTime_s), round(QueueTime_s/60,2), null())
	| fields CES Nodo MID Dia Entrada Salida Size(MB) IP_Pais QueueTime Politica Categoria Reputacion Status Domain Sender Recipient
    	| table CES Nodo MID Dia Entrada Salida Size(MB) IP_Pais QueueTime Politica Categoria Reputacion Status Domain Sender Recipient
```



# Busqueda en equivalencia a SPLUNK

```cql
# Repositorio (index) y filtros iniciales
repository = "siem-sp-cisco"
host =~ "*.maquina.grupo.com"
cef_6_header == "Consolidated Log Event"

# ---- EQUIVALENTE A eval ----
| parseDate(field=start, format="%a %b %d %H:%M:%S %Y") as HoraE_tmp
| parseDate(field=end, format="%a %b %d %H:%M:%S %Y")   as HoraS_tmp
| coalesce([HoraE_tmp, @timestamp])                     as HoraE
| HoraS_tmp                                              as HoraS

| eval("Size(MB)" = round(ESAMsgSize / 1048576, 2))
| eval(HostRaw = split(host, ".")[0])
| eval(SPF = split(SPF_verdict, ",")[5])
| eval(Adjunto = split(ESAAttachmentDetails, ",")[1])

# DKIM normalizado
| eval(DKIM = case(
      DKIM_verdict == "pass",      "pass",
      DKIM_verdict == "permfail",  "permfail",
      DKIM_verdict == "tempfail",  "tempfail",
      true(),                      "Other"
  ))

# ---- Renombrar campos ----
| rename({
    "ESAMID": "MID",
    "user": "Sender",
    "duser": "Recipient",
    "act": "Accion",
    "cs2": "IP_Pais",
    "cs1": "Politica",
    "cs3": "Categoria",
    "cs6": "Reputacion",
    "antivirus_verdict": "AV_Verdict",
    "src_user_domain": "Domain",
    "recipient_status": "Status",
    "DMARC_verdict": "DMARC"
})

# ---- Cálculos adicionales ----
| eval(ESA_Num = to_number(replace(HostRaw, "c3s2", "")))
| eval(Nodo = format("ESA%02d", ESA_Num))

# Clasificación CES según host
| eval(CES = case(
      like(host, "%.maquina.grupo1.com"), "Grupo1",
      like(host, "%.maquina.grupo2.com"), "Grupo2",
      like(host, "%.maquina.grupo3.com"), "Grupo3",
      like(host, "%.maquina.grupo4.com"), "Grupo4",
      like(host, "%.maquina.grupo5.com"), "Grupo5",
      true(), "Otro"
  ))

# Separar múltiples destinatarios
| eval(Recipient = split(Recipient, ";"))

# ---- Tiempos y duraciones ----
| eval(Dia = formatTime(HoraE, "%d/%m/%Y"))
| eval(Entrada = formatTime(HoraE, "%H:%M"))
| eval(Salida = if(is_number(HoraS), formatTime(HoraS, "%H:%M"), null()))
| eval(QueueTime_s = if(is_number(HoraS) && is_number(HoraE), HoraS - HoraE, null()))
| eval(QueueTime_m = if(is_number(QueueTime_s), round(QueueTime_s / 60, 2), null()))

# ---- Selección final de campos ----
| fields CES, Nodo, MID, Dia, Entrada, Salida, "Size(MB)", IP_Pais, QueueTime_m, Politica, Categoria, Reputacion, Status, Domain, Sender, Recipient

# (Opcional, para presentación tipo tabla)
| table CES, Nodo, MID, Dia, Entrada, Salida, "Size(MB)", IP_Pais, QueueTime_m, Politica, Categoria, Reputacion, Status, Domain, Sender, Recipient
```

Consejos de uso en LogScale
	• 🔍 Si start y end no existen o están vacíos en algunos registros, el coalesce([HoraE_tmp, @timestamp]) usa el timestamp de ingesta automáticamente.
	• 🧾 Los nombres de campo (ESAMID, user, etc.) deben coincidir exactamente con los del parser de tu feed Cisco ESA; puedes verificarlo con:

```cql
repository = "siem-sp-cisco" | fields _all | head(1)
```

• 📈 Si quieres hacer cálculos o agregaciones (por ejemplo, tamaño promedio o tiempo de cola por dominio), puedes añadir al final:

```cql
| groupBy(CES)
    (avg("Size(MB)") as AvgSize_MB, avg(QueueTime_m) as AvgQueue_m, count() as Total)
| sort(desc: Total)
```

• 🕒 Todos los campos HoraE, HoraS y derivados quedan como tipo datetime, por lo que puedes graficar o usar en dashboards sin formatearlos nuevamente.



