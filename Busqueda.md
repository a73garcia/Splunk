# Detección de acciones maliciosas y patrones en logs Cisco ESA (Splunk)

> **Contexto:** Logs CEF de Cisco ESA (`sourcetype=cisco:esa:cef`) con campos como `user`, `duser`, `ESADKIMVerdict`, `ESADLPVerdict`, `ESAGMVerdict`, `ESACFVerdict`, `ESASPVeredict`/`SPF_verdict`, `ESADMARCVerdict`, `ESAHeloDomain`, `src`, `dest_host`, `internal_message_id`, etc.  
> **Objetivo:** 1) detectar actividad maliciosa/indeseada, 2) identificar patrones (quién/desde dónde/cuándo), 3) ofrecer pivotes rápidos de investigación.  
> **Nota:** Cambia `index=TU_INDEX` y adapta nombres de campos si tu CIM/props los renombra.

---

## Índice

1. [Base para trabajar (normaliza dominios y clave de correlación)](#1-base-para-trabajar-normaliza-dominios-y-clave-de-correlación)  
2. [Spoofing / suplantación (DMARC/DKIM/SPF)](#2-spoofing--suplantación-dmarcdkimspf)  
3. [Mismatch llamativo (Friendly-From vs Envelope-From vs HELO)](#3-mismatch-llamativo-friendly-from-vs-envelope-from-vs-helo)  
4. [HELO sospechoso (IP en HELO, dominios dinámicos, AWS genérico)](#4-helo-sospechoso-ip-en-helo-dominios-dinámicos-aws-genérico)  
5. [Graymail/Spam/AV/AMP/Content: focos por veredictos](#5-graymailspamavampcontent-focos-por-veredictos)  
6. [Cambios de protocolo/cifrado TLS (downgrade o envío sin TLS)](#6-cambios-de-protocolocifrado-tls-downgrade-o-envío-sin-tls)  
7. [SBRS/Rep Score alto (riesgo remitente)](#7-sbrsrep-score-alto-riesgo-remitente)  
8. [Picos/anomalías de envío por IP/domino (detección estadística)](#8-picosanomalías-de-envío-por-ipdomino-detección-estadística)  
9. [“Campañas” (mismo asunto + remitente + muchas víctimas)](#9-campañas-mismo-asunto--remitente--muchas-víctimas)  
10. [Enlaces con `internal_message_id` (correlación del mismo mensaje)](#10-enlaces-con-internal_message_id-correlación-del-mismo-mensaje)  
11. [Reglas “listas de sospechosos” (dominios/IPs nuevos y con mala reputación)](#11-reglas-listas-de-sospechosos-dominiosips-nuevos-y-con-mala-reputación)  
12. [Tabla ejecutiva “lo raro hoy”](#12-tabla-ejecutiva-lo-raro-hoy)  
13. [Consejos de uso / paneles](#consejos-de-uso--paneles)

---

## 1) Base para trabajar (normaliza dominios y clave de correlación)

```spl
index=TU_INDEX sourcetype=cisco:esa:cef
| eval from_domain=lower(coalesce(replace(user,"^.*@",""),"")),
       env_from_domain=lower(replace(ESAFriendlyFrom,"^.*@","")),
       rcpt_domain=lower(replace(duser,"^.*@","")),
       helo_domain=lower(ESAHeloDomain),
       src_ip=coalesce(src,src_ip),
       msg_id=coalesce(internal_message_id, ESAMID, message_id)
```

---

## 2) Spoofing / suplantación (DMARC/DKIM/SPF)

```spl
index=TU_INDEX sourcetype=cisco:esa:cef
| eval spf_fail = if(like(SPF_verdict,"%Fail%") OR match(SPF_verdict,"(?i)\bfail\b"),1,0)
| where ESADKIMVerdict="fail" OR ESADMARCVerdict="fail" OR spf_fail=1
| stats count AS eventos,
        dc(rcpt_domain) AS rcpt_dom_dist,
        values(ESAFriendlyFrom) AS friendly_from,
        values(from_domain) AS from_dom,
        values(SPF_verdict) AS spf,
        values(ESADKIMVerdict) AS dkim,
        values(ESADMARCVerdict) AS dmarc
        by src_ip, helo_domain, env_from_domain, msg_id
| sort -eventos
```

**Idea:** Saca intentos de suplantación (DMARC/DKIM/SPF fallidos) y agrupa por IP origen/HELO.

---

## 3) Mismatch llamativo (Friendly-From vs Envelope-From vs HELO)

```spl
index=TU_INDEX sourcetype=cisco:esa:cef
| eval env_from_domain=lower(replace(ESAFriendlyFrom,"^.*@","")),
       mismatch_env_friendly = if(env_from_domain!=from_domain,1,0),
       mismatch_helo_from = if(helo_domain!=from_domain AND helo_domain!=env_from_domain,1,0)
| where mismatch_env_friendly=1 OR mismatch_helo_from=1
| stats count, values(ESAHeloIP) as helo_ip, values(helo_domain) as helo, values(from_domain) as from_dom, values(env_from_domain) as env_dom by src_ip
| sort -count
```

---

## 4) HELO sospechoso (IP en HELO, dominios dinámicos, AWS genérico)

```spl
index=TU_INDEX sourcetype=cisco:esa:cef
| eval helo_domain=lower(ESAHeloDomain)
| where match(helo_domain,"^(\d+\.){3}\d+$") 
   OR like(helo_domain,"%.amazonaws.com%")
   OR like(helo_domain,"%.ec2.internal%")
| stats count by helo_domain, src, from_domain
| sort -count
```

---

## 5) Graymail/Spam/AV/AMP/Content: focos por veredictos

```spl
index=TU_INDEX sourcetype=cisco:esa:cef
| stats count by ESAGMVerdict, ESAAVVerdict, ESAAMPVerdict, content_filter_verdict, outbreak_filter_verdict
| sort -count
```

**Solo lo peligroso:**

```spl
index=TU_INDEX sourcetype=cisco:esa:cef
| where ESAGMVerdict="NEGATIVE" OR ESAAVVerdict="POSITIVE" OR ESAAMPVerdict="POSITIVE" OR content_filter_verdict="MATCH"
| stats count by src, from_domain, ESAGMVerdict, ESAAVVerdict, ESAAMPVerdict, content_filter_verdict, msg_id
| sort -count
```

> *Ajusta valores reales de tus campos: p.ej. algunos ESA usan `virusVerdict=Positive/Detected`, etc.*

---

## 6) Cambios de protocolo/cifrado TLS (downgrade o envío sin TLS)

```spl
index=TU_INDEX sourcetype=cisco:esa:cef
| eval tls_in=coalesce(ESATLSInProtocol, ESATLSInProtocolV)  /* alias si cambia el nombre */
| eval tls_bad = if(isnull(tls_in) OR match(tls_in,"(?i)TLSv1(\.0)?|SSL"),1,0)
| timechart span=1h count AS total, sum(tls_bad) AS sin_tls_o_debil
| eval pct=round(100*sin_tls_o_debil/total,2)
```

**Top orígenes con TLS débil/sin TLS:**

```spl
index=TU_INDEX sourcetype=cisco:esa:cef
| eval tls_in=coalesce(ESATLSInProtocol, ESATLSInProtocolV)
| where isnull(tls_in) OR match(tls_in,"(?i)TLSv1(\.0)?|SSL")
| stats count by src, from_domain, helo_domain
| sort -count
```

---

## 7) SBRS/Rep Score alto (riesgo remitente)

```spl
index=TU_INDEX sourcetype=cisco:esa:cef
| eval sbrs=coalesce(cfp1, sbrs, SBRScore)  /* usa el que tengas; en tus capturas cfpLabel=SBRScore y cfp1=3.1 */
| where tonumber(sbrs) < 0 OR tonumber(sbrs) <= 1
| stats count by src, from_domain, sbrs, ESASenderGroup
| sort -count
```

---

## 8) Picos/anomalías de envío por IP/domino (detección estadística)

```spl
index=TU_INDEX sourcetype=cisco:esa:cef
| bin _time span=15m
| stats count by _time, src
| anomalydetection action=annotate pvalue_field=pval
| where isOutlier=1
| sort -_time
```

---

## 9) “Campañas” (mismo asunto + remitente + muchas víctimas)

```spl
index=TU_INDEX sourcetype=cisco:esa:cef
| stats dc(rcpt_domain) AS victimas, count AS eventos, values(duser) AS destinatarios
       by from_domain, user, subject
| where victimas>=5 OR eventos>=10
| sort -victimas -eventos
```

---

## 10) Enlaces con `internal_message_id` (correlación del mismo mensaje)

```spl
index=TU_INDEX sourcetype=cisco:esa:cef
| stats earliest(_time) AS first_seen latest(_time) AS last_seen
       values(*) AS *
       by internal_message_id
| eval duracion=round(last_seen-first_seen,0)
| table internal_message_id, first_seen, last_seen, duracion, src, from_domain, duser, ESADKIMVerdict, ESADMARCVerdict, SPF_verdict, ESAGMVerdict, ESAAVVerdict, content_filter_verdict, action
```

---

## 11) Reglas “listas de sospechosos” (dominios/IPs nuevos y con mala reputación)

```spl
index=TU_INDEX sourcetype=cisco:esa:cef earliest=-30d
| eval from_domain=lower(replace(user,"^.*@",""))
| stats earliest(_time) AS first_seen, latest(_time) AS last_seen,
        count AS total, values(ESASenderGroup) AS sender_group,
        values(SPF_verdict) AS spf, values(ESADKIMVerdict) AS dkim, values(ESADMARCVerdict) AS dmarc
        by from_domain, src
| where total<5 AND (like(spf,"%Fail%") OR dkim="fail" OR dmarc="fail")
| sort -last_seen
```

---

## 12) Tabla ejecutiva “lo raro hoy”

```spl
index=TU_INDEX sourcetype=cisco:esa:cef earliest=-24h
| eval from_domain=lower(replace(user,"^.*@",""))
| eval spf_fail=if(like(SPF_verdict,"%Fail%") OR match(SPF_verdict,"(?i)\bfail\b"),"fail","ok")
| eval verdict_riesgo=case(ESAAVVerdict="POSITIVE","malware",
                           ESAAMPVerdict="POSITIVE","amp",
                           content_filter_verdict="MATCH","content",
                           ESAGMVerdict="NEGATIVE","spam",
                           1==1,"normal")
| stats count AS eventos,
        sum(case(spf_fail="fail",1,0)) AS spf_fail,
        sum(case(ESADKIMVerdict="fail",1,0)) AS dkim_fail,
        sum(case(ESADMARCVerdict="fail",1,0)) AS dmarc_fail,
        values(verdict_riesgo) AS tipos
        by from_domain, src, helo_domain
| where spf_fail>0 OR dkim_fail>0 OR dmarc_fail>0 OR match(tostring(tipos),"(malware|amp|content|spam)")
| sort -eventos
```

---

## Consejos de uso / paneles

- **Pivota por `ESASenderGroup`** (en las capturas aparece `UNKNOWNLIST`). Si un dominio conocido cae de golpe en otra sender group → revisar.  
- **Guarda listas de permitidos** (dominios/IPs legítimos con fallo ocasional) y exclúyelos con:
  ```spl
  NOT [ | inputlookup allowlist_esa.csv | fields src ]
  ```
- **Normaliza campos**: algunos vienen anidados (p.ej. `SPF_verdict` con JSON tipo `{'result':'Pass','sender':'...'}`). Si lo tienes así, extrae `result`:
  ```spl
  | rex field=SPF_verdict "'result':\s*'(?<spf_result>[^']+)'"
  ```
  y usa `spf_result` en las búsquedas.
- **Alertas**: convierte 2, 6, 8, 9 y 12 en alertas programadas (con umbrales) y añade *throttling* para evitar ruido.
- **Correlación con entrega**: añade `action`/`act` (`DELIVERED`, `BLOCKED`, `BOUNCED`). Para los casos “fallo DMARC + DELIVERED”, revisa políticas.
- **Panel sugerido** (Simple XML) con: Visión general (timechart por veredicto), Spoofing/fallos de autenticación, TLS débil/sin TLS, Campañas activas (mismo asunto), Top IPs/HELO sospechosos y drilldown por `internal_message_id`.

---

**Licencia:** MIT.  
**Autor:** AntG & ChatGPT.
