# 📧 Splunk - Buscar correos sin adjunto y con tamaño > 2 MB

Este documento describe cómo construir búsquedas en **Splunk** para identificar correos electrónicos que **no tienen adjuntos** y cuyo **tamaño es mayor a 2 MB** (≈ 2 097 152 bytes).

---

## 🔹 A. Usando campo de tamaño en bytes (`msg_size`, `message_size`, `bytes`)

```spl
index="siem-eu-mta"
| eval size_bytes = coalesce(msg_size, message_size, bytes, msgbytes)
| where size_bytes > 2097152
| where (attachment_count=0 OR isnull(attachment_count) OR has_attachment=0)
| eval size_MB = round(size_bytes/1024/1024,2)
| rename internal_message_id AS MID, suser AS Sender, duser AS Recipient
| table _time MID Sender Recipient host size_MB attachment_count
```

---

## 🔹 B. Si existe un campo booleano de adjuntos (`has_attachment`)

```spl
index="siem-eu-mta"
| eval size_bytes = coalesce(msg_size, message_size, bytes, msgbytes)
| where size_bytes > 2097152
| where isnull(has_attachment) OR has_attachment=0
| eval size_MB = round(size_bytes/1024/1024,2)
| table _time internal_message_id suser duser host size_MB has_attachment
```

---

## 🔹 C. Detectar adjuntos con expresiones regulares en `_raw`

Útil cuando no existen campos de adjuntos.

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

---

## 🔹 D. Si el tamaño viene en KB o MB

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

---

## 🔹 E. Filtrar también imágenes inline (opcional)

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

---

## 📌 Campos recomendados en resultados

- `_time`  
- `internal_message_id` (`MID`)  
- `suser` (`Sender`)  
- `duser` (`Recipient`)  
- `host`  
- `size_MB`  
- `attachment_count` / `has_attachment`  

---

## ✅ Recomendaciones

- Confirma el **nombre exacto del campo de tamaño** (`msg_size`, `message_size`, `bytes`, `msgbytes`).  
- Verifica si existe `attachment_count` o `has_attachment`.  
- Para eficiencia, limita el rango de tiempo (`earliest=-24h latest=now`) antes de correr sobre todo el índice.  
