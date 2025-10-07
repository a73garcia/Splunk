# 🧩 Análisis Forense de Cabeceras de Correo — No Entregado

## 📄 INFORME TÉCNICO COMPLETO — SOC

**Fecha del mensaje:** 10/02/2025 08:01 AM  
**Asunto:** Coordinación de Reunión – Lynch + BCP Miami  
**Remitente:** carlos.santacruz@lyntech.com  
**Destinatario principal:** bcpmiami@bcp.com.pe  
**Plataforma de envío:** Microsoft 365 (Outlook / Exchange Online)  
**Analizador usado:** Message Header Analyzer (mha.azurewebsites.net)

---

## 📬 Resumen de entrega

| Hop | Host Emisor | Host Receptor | Hora | Delay | Tipo |
|-----|--------------|----------------|--------|--------|------|
| 1 | DB9PR0MB9404.prod.outlook.com | DB9PR0MB9404.prod.outlook.com | 08:01:44 | mapi | Interno |
| 2 | DB9PR0MB9404.prod.outlook.com | AM9PR04MB8290.prod.outlook.com | 08:01:44 | 17 seg | ESMTP/TLS |
| 3 | mail-westeuropean01T010005.outbound.protection.outlook.com | AM8PR03CU005.outbound.protection.outlook.com | 08:02:01 | 5 seg | ESMTP/TLS |
| 4 | mail.santandergroup.c3z.jphxcm.com | SA2EPF00001508.prod.outlook.com | 08:02:02 | 2 seg | ESMTP/TLS |
| 5 | SA2EPF00001508.prod.outlook.com | SA0PR11CA0078.amprd01.prod.outlook.com | 08:02:04 | 2 seg | ESMTP/TLS |
| 6 | SA0PR11CA0078.amprd01.prod.outlook.com | --- | 08:02:05 | 1 seg | ESMTP/TLS |

**Conclusión de tránsito:**  
El correo viajó correctamente a través de la infraestructura de Microsoft 365, hasta el salto final donde fue **rechazado por políticas de autenticación DMARC** del dominio del remitente (`lyntech.com`).

---

## 🚫 Motivo del fallo de entrega

**Error SMTP reportado:**
```
550 5.7.509 Access denied, sending domain lyntech.com does not pass DMARC verification and has a DMARC policy of reject
```

**Interpretación:**  
El dominio remitente (`lyntech.com`) posee una política DMARC configurada como **`p=reject`**, lo que obliga a rechazar cualquier mensaje que falle en las validaciones SPF o DKIM.

---

## 🧾 Resultados de autenticación

| Protocolo | Resultado | Descripción |
|------------|------------|--------------|
| **SPF** | ❌ Fail | El servidor emisor `216.71.158.121` (santandergroup.c3z.jphxcm.com) no está autorizado en el registro SPF de `lyntech.com`. |
| **DKIM** | ❌ Fail | La firma DKIM incluida no coincide con la clave pública del dominio o no está configurada. |
| **DMARC** | ❌ Fail (p=reject) | Política estricta que fuerza el rechazo ante fallos SPF/DKIM. |
| **ARC** | ⚠️ None | No se aplicó un sello ARC compensatorio. |
| **Antispam** | ✅ Limpio | Sin detección de malware o spam. |
| **ThreatScanner Verdict** | Negativo | Correo legítimo, pero bloqueado por autenticación. |

---

## 🧠 Conclusión forense

El correo **no llega al destinatario** porque fue **rechazado por la política DMARC de su propio dominio**.  
El servidor de envío (`santandergroup.c3z.jphxcm.com`) **no está autorizado** para enviar mensajes en nombre de `lyntech.com`, y el sistema destinatario **aplicó correctamente la política de rechazo**.

---

## 🛠️ Recomendaciones técnicas

### 1. Corregir autenticación del dominio `lyntech.com`
- **Actualizar el registro SPF**:
  ```txt
  v=spf1 include:santandergroup.c3z.jphxcm.com include:spf.protection.outlook.com -all
  ```
- **Configurar DKIM** en la plataforma que envía los correos (`santandergroup.c3z.jphxcm.com` o M365).
- **Revisar la política DMARC**:
  - Temporalmente cambiar a `p=quarantine` mientras se ajusta SPF/DKIM:
    ```txt
    v=DMARC1; p=quarantine; rua=mailto:dmarc@lyntech.com; ruf=mailto:dmarc@lyntech.com
    ```

### 2. Ajuste alternativo
- Usar un **dominio autorizado** como remitente (por ejemplo `@santandergroup.com`) y añadir `Reply-To: usuario@lyntech.com`.

### 3. Validaciones posteriores
- Probar con herramientas como:
  - [https://mxtoolbox.com/spf.aspx](https://mxtoolbox.com/spf.aspx)
  - [https://dmarcian.com/dmarc-inspector/](https://dmarcian.com/dmarc-inspector/)
- Confirmar que el **SPF pasa** y que el **DKIM firma correctamente** antes de volver a enviar.

---

## 📈 Impacto potencial
- Correos legítimos bloqueados.  
- Fallo de reputación de dominio.  
- Posible pérdida de comunicación con clientes externos.

---

## 🧾 Autor del informe
**Analista:** AntG  
**Fecha:** 10/10/2025  
**Herramientas:** Microsoft Message Header Analyzer, M365, Forefront Antispam Report Header.

---

# ✉️ RESUMEN EJECUTIVO — Correo no entregado

**Motivo del incidente:**  
El correo fue **rechazado automáticamente** por el servidor del destinatario debido a **fallo en la autenticación DMARC** del dominio `lyntech.com`.

---

## 🧠 Causa raíz
- El servidor de envío (`216.71.158.121`) **no figura en el registro SPF** de `lyntech.com`.  
- La firma **DKIM no se validó** correctamente.  
- La política DMARC del dominio (`p=reject`) bloqueó el mensaje.

---

## 🧩 Efecto
El correo no se entregó al destinatario. El sistema receptor cumplió la política DMARC y rechazó el mensaje con el error:

```
550 5.7.509 Access denied, sending domain lyntech.com does not pass DMARC verification (p=reject)
```

---

## 🛠️ Recomendaciones
1. **Actualizar SPF** para incluir el servidor de envío:
   ```txt
   include:santandergroup.c3z.jphxcm.com
   ```
2. **Configurar DKIM** para `lyntech.com` en Microsoft 365 u otro sistema de envío.
3. **Revisar DMARC**, usar temporalmente `p=quarantine` hasta validar SPF/DKIM.
4. **Alternativa:** enviar desde `@santandergroup.com` con `Reply-To: @lyntech.com`.

---

## 📅 Próximos pasos
- Verificar registros con herramientas DMARC externas.  
- Reenviar el correo una vez actualizados los registros.  
- Supervisar reportes DMARC durante 48 horas posteriores.

---

**Analista:** AntG  
**Fecha del análisis:** 10/10/2025
