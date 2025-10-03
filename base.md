
## Busqueda base

```python
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

```perl
    | fields CES Nodo MID Dia Entrada Salida Size(MB) dest_ip Domain Sender
    | table CES Nodo MID Dia Entrada Salida Size(MB) dest_ip Domain Sender
```

---

## Tabla con datos para encolamientos

```sql
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

## Grafica para ver correos procesados y que han tenido un procesamiento superior a 60 segundos

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

## Cuenta correos por sender

```spl
    | stats count AS Correos by Sender
```

---

## Número de correos enviados y ordenados de mayor a menor

```spl
    | stats count AS Correos by Sender
    | sort - Correos
    | head 20
```

---

## Pone a los valores numéricos un separador de miles con "," en vez de "."

```spl
    | foreach * [ eval <<FIELD>> = if(isnum('<<FIELD>>'), replace(tostring('<<FIELD>>', "commas"), ".", ","), '<<FIELD>>') ]
```

---

## Cuenta correos por horas

```spl
    | bin _time span=1h
    | stats count AS Correos by _time
    | sort _time
```
---

## Cuenta correos por horas, totales y sender seleccionados

```spl
    | bin _time span=1h
    | stats count AS Correos
        count(eval(user="correo1@mail.com")) AS "correo1@mail.com"
        count(eval(user="correo2@mail.com")) AS "correo2@mail.com"
        count(eval(user="correo3@mail.com")) AS "correo3@mail.com"
        count(eval(user="correo4@mail.com")) AS "correo4@mail.com"
        count(eval(user="correo5@mail.com")) AS "correo5@mail.com"
        count(eval(user!="correo1@mail.com"" OR user!="correo2@mail.com"" OR user!="correo3@mail.com"" OR user!="correo4@mail.com"" OR user!="correo5@mail.com"")) AS Otros
    by _time
    | sort _time
    | addcoltotals
    | eval _time = if(isnull(_time), "Total", _time)
    | foreach * [ eval <<FIELD>> = if(isnum('<<FIELD>>'), replace(tostring('<<FIELD>>', "commas"), ".", ","), '<<FIELD>>') ]
```

---

## Correos encolamientos

```spl
    | eval QueueRange = case(
        QueueTime < 60, "1. Menos de 1 min",
        QueueTime >= 60 AND QueueTime < 180, "2. Hasta 3 min",
        QueueTime >= 180 AND QueueTime < 300, "3. Hasta 5 min",
        QueueTime >= 300 AND QueueTime < 600, "4. Hasta 10 min",
        QueueTime >= 600, "5. Mas de 10 min"
    )
    | stats count by QueueRange
    | eval count = tostring(count, "commas")
    | sort QueueRage
```
---

## Numero correos por senders indicado

```spl
    | bin _time span=1h
    | stats count AS Correos
        count(eval(user="correo1@mail.com")) AS "correo1@mail.com"
        count(eval(user="correo2@mail.com")) AS "correo2@mail.com"
        count(eval(user="correo3@mail.com")) AS "correo3@mail.com"
        count(eval(user="correo4@mail.com")) AS "correo4@mail.com"
        count(eval(user="correo5@mail.com")) AS "correo5@mail.com"
    by _time
    | sort _time
    | addcoltotals
    | eval _time = if(isnull(_time), "Total", _time)
    | fields _time Correos "correo1@mail.com" "correo2@mail.com" "correo3@mail.com" "correo4@mail.com" "correo5@mail.com"
    | foreach * [ eval <<FIELD>> = if(isnum('<<FIELD>>'), replace(tostring('<<FIELD>>', "commas"), ".", ","), '<<FIELD>>') ]
```

---

## Cuenta correos por entry log

```spl
    | eval OPC1 = if(like(signature,"%valor1%"), mid, null())
    | eval OPC2 = if(like(signature,"%valor2%"), mid, null())
    | eval OPC3 = if(like(signature,"%valor3"), mid, null())
    | stats dc(mid) AS Total_Correos 
        dc(OPC1) AS "valor1" 
        dc(OPC2) AS "valor2" 
        dc(OPC3) AS "valor3" 
    by CES
    | foreach * [ eval <<FIELD>> = if(isnum('<<FIELD>>'), replace(tostring('<<FIELD>>',"commas"),".",","), '<<FIELD>>') ]
```

---

## Busca correos en base al Sender y la act

```spl
    | stats values(host) as host 
        values(HoraEntrada) as HoraEntrada 
        values(Accion) as Accion 
        values(MID) as MID 
        values(Size(MB)) as Size(MB) 
        values(Sender) as Sender 
        values(Recipient) as Recipient
    by suser, act
```

## Ver numero de los por nodos y tipo de syslogs

```spl
    | chart count over host by source
    | addtotals
```

---

## Correos dropeado y cuarentena

```spl
    | stats
        count(MID) as Total
        count(eval(QueueTime > 180)) as Encolados
        count(eval(Status="DROPPED")) as Dropped
        count(eval(Status="QUARANTINED")) as Quarantined
        count(eval(Status="DELIVERED")) as Delivered
      by Nodo
```

---

## Cuenta correos entregados y estados por nodos

```spl
    | stats 
        count(MID) as Total
        count(eval(Status="DELIVERED")) as Delivered
        count(eval(QueueTime > 180)) as Encolados
        count(eval(Status="QUARANTINED")) as Quarantined
        count(eval(Status="DROPPED")) as Dropped
        count(eval(Status="DQ")) as DQ
        count(eval(Status="BOUNCED")) as Bounce
        count(eval(Status="ABORTED")) as Aborted
    by CES, Nodo
    | eval Delivered = tostring(Delivered, "commas") . " (" . round((Delivered / Total) * 100, 2) . "%)"
    | eval Encolados = tostring(Encolados, "commas") . " (" . round((Encolados / Total) * 100, 2) . "%)"
    | eval Quarantined = tostring(Quarantined, "commas") . " (" . round((Quarantined / Total) * 100, 2) . "%)"
    | eval Dropped = tostring(Dropped, "commas") . " (" . round((Dropped / Total) * 100, 2) . "%)"
    | eval DQ = tostring(DQ, "commas") . " (" . round((DQ / Total) * 100, 2) . "%)"
    | eval Bounce = tostring(Bounce, "commas") . " (" . round((Bounce / Total) * 100, 2) . "%)"
    | eval Aborted = tostring(Aborted, "commas") . " (" . round((Aborted / Total) * 100, 2) . "%)"
    | eval Total = tostring(Total, "commas")
```

## Cuenta correos por estado

```spl
    | stats values(act) AS Estado count by act, duser
    | addcoltotals
```

---

## Busqueda de correos enviado por CES APP por Dominio de Sender

```spl
    | eval HoraE = strptime(start, "%a %b %d %H:%M:%S %Y"), HoraS = strptime(end, "%a %b %d %H:%M:%S %Y"), 
        HostRaw = mvindex(split(host, "."), 0), SPF = mvindex(split(SPF_verdict, ","), 5), 
        ESA_Num = tonumber(replace(HostRaw, "esa-", "")), Nodo = printf("ESA%02d", ESA_Num), 
        Dia = strftime(HoraE, "%d/%m/%Y"), Entrada = strftime(HoraE, "%H:%M"), Salida = strftime(HoraS, "%H:%M"), 
        QueueTime = HoraS - HoraE
    | eval CES=case(
        like(host, "%.santandergroup.c3s2.iphmx.com"), "EU",
        like(host, "%.hc5532-55.iphmx.com"), "AM",
        like(host, "%.hc6154-33.iphmx.com"), "BR",
        like(host, "%.santandergroup-out.c3s2.iphmx.com"), "APP",
        like(host, "%.hc5533-96.iphmx.com"), "APP DR"
    )
    | stats values(src_user_domain) as Dominio count by cs1
    | foreach * [ eval <<FIELD>> = if(isnum('<<FIELD>>'), replace(tostring('<<FIELD>>', "commas"), ".", ","), '<<FIELD>>') ]
```

---

## TLS

```spl
index=siem-cisco sourcetype="cisco:esa:cef" (ESATLSInProtocol="TLSv1.1" OR ESATLSOutProtocol="TLSv1.1" OR ESATLSOutProtocol="TLSv1.2") suser="*" duser="*" act="*"
    | rex field=suser "@(?<Origen>[^>]+)"
    | rex field=duser "@(?<Destino>[^>]+)"
    | rename ESATLSInProtocol AS TLS_IN, ESATLSOutProtocol AS TLS_OUT, act AS Accion
    | stats count by Origen Destino TLS_IN TLS_OUT Accion
```

---

## Correos por política

```spl
    | rename cs1 AS Politica
    | stats count by Politica
    | addcoltotals
    | sort Politica
    | eval Politica = if(isnull(Politica), "Total", Politica)
    | foreach * [ eval <<FIELD>> = if(isnum('<<FIELD>>'), replace(tostring('<<FIELD>>', "commas"), ".", ","), '<<FIELD>>') ]
```

---

## Cuenta por política en meses (filas)

```spl
    | rename cs1 AS Politica
    | bin _time span=1mon
    | eval Mes=strftime(_time,"%m/%Y")
    | stats count by Mes Politica
    | sort 0 Mes Politica
    | streamstats count AS fila_en_mes by Mes
    | eval Mes=if(fila_en_mes=1, Mes, "")
    | fields Mes Politica count
    | foreach * [ eval <<FIELD>> = if(isnum('<<FIELD>>'), replace(tostring('<<FIELD>>', "commas"), ".", ","), '<<FIELD>>') ]
```

---

## Cuenta por política en meses (columnas)

```spl
    | rename cs1 AS Politica
    | bin _time span=1mon
    | eval Mes=strftime(_time,"%Y-%m")
    | stats count by Mes Politica
    | sort 0 Mes
    | xyseries Politica Mes count
    | addcoltotals
    | eval Politica = if(isnull(Politica), "Total", Politica)
    | foreach * [ eval <<FIELD>> = if(isnum('<<FIELD>>'), replace(tostring('<<FIELD>>', "commas"), ".", ","), '<<FIELD>>') ]
    ```
---

## Busqueda MailX

```spl
index="siem-cisco" suser="*" duser="*" start="*" event_class_id="ESA_CONSOLIDATED_LOG_EVENT"
    | eval start_ts = strptime(start, "%a %b %e %H:%M:%S %Y")
    | eval Dia = strftime(start_ts, "%d/%m/%Y"), Hora = strftime(start_ts, "%H:%M")
    | rename duser AS Recipient, suser AS Sender, internal_message_id AS MID, ESAHeloDomain AS Origen, dest_host AS Destino
    | eval Nodo=case(
        like(host, "Maquina1%"), "host1",
        like(host, "Maquina2%"), "host2",
        like(host, "Maquina3%"), "host3",
        like(host, "Maquina4%"), "host4",
        like(host, "Maquina5%"), "host5",
        like(host, "Maquina6%"), "host6"
    )
    | fields Dia Hora Nodo MID Origen Destino Sender Recipient
    | table Dia Hora Nodo MID Origen Destino Sender Recipient
```
---

## Correos entrantes sin adjuntos y con mas de 2MB de peso

```spl
index=siem-cisco (host=*.maquina.grupo1.com OR host=*.maquina.grupo2.com OR host=*.maquina.grupo3.com) cef_6_header="Consolidated Log Event" user="*" suser!="bounce" cs1="*_IN"
    | where ESAMsgSize > 2097152
    | where (ESAAttachmentDetails=0 OR isnull(ESAAttachmentDetails)) OR ESAAttachmentDetails!=0
    | eval HoraE = strptime(start, "%a %b %d %H:%M:%S %Y"), 
           Size = round(ESAMsgSize / 1048576, 2), 
           HostRaw = mvindex(split(host, "."), 0)
    | rename ESAMID AS MID, user AS Sender, duser AS Recipient, cs1 AS Politica
    | eval ESA_Num = tonumber(replace(HostRaw,"esa-","")), Nodo = printf("ESA%02d", ESA_Num), 
           Adjunto = mvindex(split(ESAAttachmentDetails, ","), 1)
    | eval CES=case(
           like(host,"%.maquina.grupo1.com"), "Grupo1",
           like(host,"%.maquina.grupo2.com"), "Grupo2",
           like(host,"%.maquina.grupo3.com"), "Grupo3",
           like(host,"%.maquina.grupo4.com"), "Grupo4",
           like(host,"%.maquina.grupo5.com"), "Grupo5"
    )
    | eval Dia = strftime(HoraE,"%d/%m/%Y"), Entrada = strftime(HoraE,"%H:%M")
    | fields CES Nodo Politica MID Dia Entrada Size Sender Adjunto
    | table CES Nodo Politica MID Dia Entrada Size Sender Adjunto
```

---

## Cuenta por Políticas los correos entrantes sin adjuntos y con mas de 2MB de peso

```spl
index=siem-cisco (host=*.maquina.grupo1.com OR host=*.maquina.grupo2.com OR host=*.maquina.grupo3.com) cef_6_header="Consolidated Log Event" user="*" suser!="bounce" cs1="*_IN"
    | where ESAMsgSize > 2097152
    | where (ESAAttachmentDetails=0 OR isnull(ESAAttachmentDetails)) OR ESAAttachmentDetails!=0
    | eval HoraE = strptime(start, "%a %b %d %H:%M:%S %Y"), 
           Size = round(ESAMsgSize / 1048576, 2), 
           HostRaw = mvindex(split(host, "."), 0)
    | rename ESAMID AS MID, user AS Sender, duser AS Recipient, cs1 AS Politica
    | eval ESA_Num = tonumber(replace(HostRaw,"esa-","")), Nodo = printf("ESA%02d", ESA_Num), 
           Adjunto = mvindex(split(ESAAttachmentDetails, ","), 1)
    | eval CES=case(
           like(host,"%.maquina.grupo1.com"), "Grupo1",
           like(host,"%.maquina.grupo2.com"), "Grupo2",
           like(host,"%.maquina.grupo3.com"), "Grupo3",
           like(host,"%.maquina.grupo4.com"), "Grupo4",
           like(host,"%.maquina.grupo5.com"), "Grupo5"
    )
    | eval Dia = strftime(HoraE,"%d/%m/%Y"), Entrada = strftime(HoraE,"%H:%M")
    | bin _time span=1mon
    | eval Mes=strftime(_time,"%Y-%m")
    | stats count by Mes Politica
    | sort 0 Mes Politica
    | addcoltotals
    | eval Politica = if(isnull(Politica), "Total", Politica)
    | foreach * [ eval <<FIELD>> = if(isnum('<<FIELD>>'), replace(tostring('<<FIELD>>', "commas"), ".", ","), '<<FIELD>>') ]
```
---

## Cuenta correos entrantes sin adjuntos y con mas de 2MB de peso dividido por rango de tamaño

```spl
index=siem-cisco (host=*.maquina.grupo1.com OR host=*.maquina.grupo2.com OR host=*.maquina.grupo3.com) cef_6_header="Consolidated Log Event" user="*" suser!="bounce" cs1="*_IN"
    | where ESAMsgSize > 2097152
    | where (ESAAttachmentDetails=0 OR isnull(ESAAttachmentDetails)) OR ESAAttachmentDetails!=0
    | eval HoraE = strptime(start, "%a %b %d %H:%M:%S %Y"), 
           Size = round(ESAMsgSize / 1048576, 2)
    | rename ESAMID AS MID, user AS Sender, duser AS Recipient
    | eval ESA_Num = tonumber(replace(HostRaw,"esa-","")), Nodo = printf("ESA%02d", ESA_Num), 
           Adjunto = mvindex(split(ESAAttachmentDetails, ","), 1)
    | eval CES=case(
           like(host,"%.maquina.grupo1.com"), "Grupo1",
           like(host,"%.maquina.grupo2.com"), "Grupo2",
           like(host,"%.maquina.grupo3.com"), "Grupo3",
           like(host,"%.maquina.grupo4.com"), "Grupo4",
           like(host,"%.maquina.grupo5.com"), "Grupo5"
    )
    | eval Dia = strftime(HoraE,"%d/%m/%Y"), Entrada = strftime(HoraE,"%H:%M")
    | eval Size = case(
           Size < 3, "1. Entre 2 y 3 MB",
           Size >= 3 AND Size < 5, "2. Entre 3 y 5 MB",
           Size >= 5 AND Size < 10, "3. Entre 5 y 10 MB",
           Size >= 10 AND Size < 20, "4. Entre 10 y 20 MB",
           Size >= 20 AND Size < 30, "5. Entre 20 y 30 MB",
           Size >= 30, "6. Mas de 30 MB"
    )
    | stats count by Size
    | eval count = tostring(count, "commas")
    | sort Size
```

## Comprobar tipos de index

```spl
    | tstats count where index=siem-cisco OR index=siem-*-mta by index, sourcetype, source
```

---

## Unir log por MID

```spl
index=siem-cisco
    | transaction internal_message_id startswith=signature="accepted" endswith=signature="delivered" keepevicted=t maxspan=2h
    | eval dur_seg=round(duration,300)
    | rename internal_message_id AS MID
    | table MID sender recipient subject
```

---











