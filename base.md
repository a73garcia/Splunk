
##Busqueda base


index=siem-sp-cisco host="*.maquina.grupo.com" cef_6_header="Consolidated Log Event"
| eval HoraE = strptime(start, "%a %b %d %H:%M:%S %Y"), HoraS = strptime(end, "%a %b %d %H:%M:%S %Y"), Size(MB) = round(ESAMsgSize / 1048576, 2), HostRaw = mvindex(split(host, "."), 0), SPF = mvindex(split(SPF_verdict, ","), 5), Adjunto = mvindex(split(ESAAttachmentDetails, ","), 1)
| eval DKIM=case(DKIM_verdict=="pass","pass", DKIM_verdict=="permfail","permfail", DKIM_verdict=="tempfail","tempfail", true(), "Other")
| rename ESAMID AS MID, user AS Sender, duser AS Recipient, act AS Accion, cs2 AS IP_Pais, cs1 AS Politica, cs3 AS Categoria, cs6 AS Reputacion, antivirus_verdict AS AV_Verdict, src_user_domain AS Domain, recipient_status AS Status, DMARC_verdict AS DMARC
| eval ESA_Num = tonumber(replace(HostRaw,"c3s2","")), Nodo = printf("ESA%02d", ESA_Num)
| eval CES=case(
    like(host, "%.santandergroup.c3s2.iphmx.com"), "EU",
    like(host, "%.hc5532-55.iphmx.com"), "AM",
    like(host, "%.hc6154-33.iphmx.com"), "BR",
    like(host, "%.santandergroup.ap.c3s2.iphmx.com"), "AP",
    like(host, "%.hc5533-96.iphmx.com"), "APP DR"
)
| eval Recipient = split(Recipient, ";")
| eval Dia = strftime(HoraE, "%d/%m/%Y"), Entrada = strftime(HoraE, "%H:%M"), Salida = strftime(HoraS, "%H:%M"), QueueTime = round(HoraS - HoraE)
