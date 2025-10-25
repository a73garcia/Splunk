

```spl
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




