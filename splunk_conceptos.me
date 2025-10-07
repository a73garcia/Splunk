# 🧭 Guía Completa de Búsquedas en Splunk

> **Autor:** AntG  
> **Versión:** 1.0  
> **Fecha:** 2025-10-07  
> **Propósito:** Dominar las opciones de búsqueda en Splunk para análisis, depuración y generación de dashboards.

---

## 📘 Introducción

Splunk permite buscar, filtrar y analizar grandes volúmenes de datos mediante su propio lenguaje: **SPL (Search Processing Language)**.  
Esta guía recopila las **opciones y comandos más utilizados** para realizar búsquedas efectivas, optimizar consultas y crear estadísticas visuales.

---

## 🔍 1. Tipos de Búsquedas en Splunk

| Tipo | Descripción | Ejemplo |
|------|--------------|---------|
| **Básica** | Busca texto literal en los eventos. | `error` |
| **Por campo** | Filtra valores específicos en campos. | `status=404` |
| **Combinada** | Usa operadores lógicos. | `host=mail* AND action=blocked` |
| **Con comandos** | Procesa resultados con SPL. | `index=mail | stats count by sender` |

---

## ⚙️ 2. Estructura General de una Búsqueda

```spl
index=<nombre> [sourcetype=<tipo>] [host=<host>] [source=<ruta>]
| comando1 [opciones]
| comando2 [opciones]
| ...
```

Ejemplo:
```spl
index=siem-mail sourcetype=cisco:esa | stats count by sender
```

---

## 🔧 3. Filtros y Operadores

### Operadores Lógicos
| Operador | Significado | Ejemplo |
|-----------|--------------|----------|
| `AND` | Coinciden ambas condiciones | `host="ces01" AND action="blocked"` |
| `OR` | Coincide cualquiera | `status=400 OR status=500` |
| `NOT` | Excluye coincidencias | `NOT src_ip="10.0.0.1"` |

### Operadores de Comparación
| Operador | Uso |
|-----------|-----|
| `=` | Igual |
| `!=` | Diferente |
| `<`, `>`, `<=`, `>=` | Comparaciones numéricas |
| `IN()` | Valores dentro de lista → `status IN (400,404,500)` |

---

## ⏱️ 4. Filtros de Tiempo

| Intervalo | Ejemplo | Descripción |
|------------|----------|-------------|
| Últimos 15 minutos | `earliest=-15m latest=now` | Últimos 15 minutos |
| Última hora | `earliest=-1h@h latest=now` | Redondea a hora |
| Día actual | `earliest=@d latest=now` | Desde medianoche |
| Día anterior | `earliest=-1d@d latest=@d` | Día completo anterior |

> 💡 Puedes aplicarlos en el panel superior o dentro del comando `search`.

---

## 📊 5. Comandos Principales de Búsqueda

### 🔹 `search`
Filtra resultados según condiciones.
```spl
index=siem-mail | search action="blocked" sender="*@gmail.com"
```

### 🔹 `stats`
Genera estadísticas agrupadas.
```spl
| stats count by sender
| stats avg(size) as Media_MB by host
```

### 🔹 `timechart`
Crea series temporales.
```spl
| timechart count by action
```

### 🔹 `table`
Muestra campos específicos.
```spl
| table _time, sender, recipient, action
```

### 🔹 `fields`
Incluye o excluye campos.
```spl
| fields + sender, recipient
| fields - raw
```

### 🔹 `eval`
Crea o modifica campos.
```spl
| eval Size_MB=round(size/1024/1024,2)
```

### 🔹 `rename`
Cambia nombres de campos.
```spl
| rename sender AS Remitente, recipient AS Destinatario
```

### 🔹 `sort`
Ordena los resultados.
```spl
| sort - count
```

### 🔹 `dedup`
Elimina duplicados según un campo.
```spl
| dedup sender
```

### 🔹 `top`
Muestra los valores más frecuentes.
```spl
| top sender limit=10
```

### 🔹 `where`
Aplica condiciones avanzadas.
```spl
| where Size_MB > 2 AND action="blocked"
```

---

## 🧮 6. Ejemplos Combinados

### 🧩 Ejemplo 1 — Correos bloqueados por tamaño
```spl
index=siem-mail action="blocked"
| eval Size_MB=round(size/1048576,2)
| where Size_MB > 5
| stats count by sender, recipient
| sort - count
```

### 🧩 Ejemplo 2 — Estadísticas por país y reputación
```spl
index=siem-mail
| stats count by IP_Pais, Reputacion
| sort - count
```

### 🧩 Ejemplo 3 — Gráfico temporal de correos por host
```spl
index=siem-mail
| timechart count by host
```

---

## 🧰 7. Comandos Avanzados

| Comando | Función | Ejemplo |
|----------|----------|----------|
| `rex` | Extrae datos mediante regex | `| rex field=_raw "From:\s(?<Remitente>[^ ]+)"` |
| `regex` | Filtra usando expresiones regulares | `| regex sender=".*@gmail\.com$"` |
| `lookup` | Consulta archivos externos | `| lookup dominios_malos domain OUTPUT risk` |
| `join` | Une resultados de dos búsquedas | `| join MID [ search index=spam ]` |
| `transaction` | Agrupa eventos relacionados | `| transaction MID maxspan=30s` |
| `fillnull` | Sustituye valores nulos | `| fillnull value="N/A"` |

---

## 🧠 8. Buenas Prácticas

✅ Usa filtros de tiempo siempre.  
✅ Limita los campos con `fields` o `table`.  
✅ Usa `where` para filtrar después de crear campos.  
✅ Aprovecha `stats` y `timechart` para reducir volumen.  
✅ Guarda las búsquedas útiles como **Saved Searches** o **Alerts**.  
✅ Añade `| head 20` al final mientras pruebas para evitar sobrecarga.

---

## 📈 9. Ejemplo Real de Optimización

```spl
index=siem-mail host="*.grupo.com"
| eval Size_MB=round(size/1048576,2)
| where Size_MB > 2 AND isnull(ESAAttachmentDetails)
| stats count by sender, policy
| sort - count
```

👉 Resultado: lista de remitentes con correos grandes sin adjunto, agrupados por política.

---

## 🏁 Conclusión

Dominar las opciones de búsqueda en Splunk permite **acelerar el análisis forense, detectar anomalías y construir dashboards inteligentes**.  
Combina los comandos según tus necesidades y guarda tus mejores consultas como base de conocimiento.

---

📂 **Repositorio recomendado:**  
> [GitHub: Splunk Queries and Best Practices](https://github.com/splunk)
