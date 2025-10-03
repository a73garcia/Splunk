
## Busqueda base

```spl
index=siem-sp-cisco host="*.maquina.grupo.com" cef_6_header="Consolidated Log Event"
    | eval HoraE = strptime(start, "%a %b %d %H:%M:%S %Y"), HoraS = strptime(end, "%a %b %d %H:%M:%S %Y"), Size(MB) = round(ESAMsgSize / 1048576, 2), HostRaw = mvindex(split(host, "."), 0), SPF = mvindex(split(SPF_verdict, ","), 5), Adjunto = mvindex(split(ESAAttachmentDetails, ","), 1)
    | eval DKIM=case(DKIM_verdict=="pass","pass", DKIM_verdict=="permfail","permfail", DKIM_verdict=="tempfail","tempfail", true(), "Other")
    | rename ESAMID AS MID, user AS Sender, duser AS Recipient, act AS Accion, cs2 AS IP_Pais, cs1 AS Politica, cs3 AS Categoria, cs6 AS Reputacion, antivirus_verdict AS AV_Verdict, src_user_domain AS Domain, recipient_status AS Status, DMARC_verdict AS DMARC
    | eval ESA_Num = tonumber(replace(HostRaw,"c3s2","")), Nodo = printf("ESA%02d", ESA_Num)
    | eval CES=case(
        like(host, "%.maquina.grupo1.com"), "Grupo1",
        like(host, "%.maquina.grupo2.com"), "Grupo2",
        like(host, "%.maquina.grupo3.com"), "Grupo3",
        like(host, "%.maquina.grupo4.com"), "Grupo4",
        like(host, "%.maquina.grupo5.com"), "Grupo5"
    )
    | eval Recipient = split(Recipient, ";")
    | eval Dia = strftime(HoraE, "%d/%m/%Y"), Entrada = strftime(HoraE, "%H:%M"), Salida = strftime(HoraS, "%H:%M"), QueueTime = round(HoraS - HoraE)
```
---

## Tabla de correos

```spl
    | fields CES Nodo MID Dia Entrada Salida Size(MB) dest_ip Domain Sender
    | table CES Nodo MID Dia Entrada Salida Size(MB) dest_ip Domain Sender
```

---

## Tabla con datos para encolamientos

```spl
    | fields CES Nodo MID Dia Entrada Salida Size(MB) IP_Pais QueueTime Politica Categoria Reputacion Status Domain Sender Recipient
    | table CES Nodo MID Dia Entrada Salida Size(MB) IP_Pais QueueTime Politica Categoria Reputacion Status Domain Sender Recipient
```

---

## Tabla con datos para encolamientos con SPF, DKIM, DMARC, Adjuntos

```spl
    | fields CES Nodo MID Dia Entrada Salida Size(MB) IP_Pais QueueTime Politica Categoria Reputacion Status Domain Sender Adjunto SPF DMARC DKIM Recipient
    | table CES Nodo MID Dia Entrada Salida Size(MB) IP_Pais QueueTime Politica Categoria Reputacion Status Domain Sender Adjunto SPF DMARC DKIM Recipient
```

---

## Grafica para ver correos que han tenido un procesamiento a 90 segundos

```spl
    | eval esMayor90 = if(QueueTime > 90, 1, 0)
    | timechart span=1m sum(esMayor90) as EventosMayor90
```

---

## #Grafica para ver correos procesados y que han tenido un procesamiento superior a 60 segundos

```spl
    | eval esMayor60 = if(QueueTime > 60, 1, 0)
    | timechart span=1m dc(MID) as CorreosProcesados, sum(esMayor60) as EventosMayor60
```

---

## Cuenta correos por sender

```spl
    | stats count by Sender
```

---




