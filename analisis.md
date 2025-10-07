# 🧩 Análisis Forense de Cabeceras de Correo — No Entregado

---


## 🚫 Motivo del fallo de entrega

**Error SMTP reportado:**
```
550 5.7.509 Access denied, sending domain bbb.com does not pass DMARC verification and has a DMARC policy of reject
```

**Interpretación:**  
El dominio remitente (`bbb.com`) posee una política DMARC configurada como **`p=reject`**, lo que obliga a rechazar cualquier mensaje que falle en las validaciones SPF o DKIM.

---

## 🧾 Resultados de autenticación

| Protocolo | Resultado | Descripción |
|------------|------------|--------------|
| **SPF** | ❌ Fail | El servidor emisor `216.71.158.121` (r45645.com) no está autorizado en el registro SPF de `bbb.com`. |
| **DKIM** | ❌ Fail | La firma DKIM incluida no coincide con la clave pública del dominio o no está configurada. |
| **DMARC** | ❌ Fail (p=reject) | Política estricta que fuerza el rechazo ante fallos SPF/DKIM. |
| **ARC** | ⚠️ None | No se aplicó un sello ARC compensatorio. |
| **Antispam** | ✅ Limpio | Sin detección de malware o spam. |
| **ThreatScanner Verdict** | Negativo | Correo legítimo, pero bloqueado por autenticación. |

---

## 🧠 Conclusión forense

El correo **no llega al destinatario** porque fue **rechazado por la política DMARC de su propio dominio**.  
El servidor de envío (`drgdgd.com`) **no está autorizado** para enviar mensajes en nombre de `bbb.com`, y el sistema destinatario **aplicó correctamente la política de rechazo**.

---

## 🛠️ Recomendaciones técnicas

### 1. Corregir autenticación del dominio `bbb.com`
- **Actualizar el registro SPF**:
  ```txt
  v=spf1 include:werrsfs.com include:spf.protection.outlook.com -all
  ```
- **Configurar DKIM** en la plataforma que envía los correos (`xdgvdfg.com` o M365).
- **Revisar la política DMARC**:
  - Temporalmente cambiar a `p=quarantine` mientras se ajusta SPF/DKIM:
    ```txt
    v=DMARC1; p=quarantine; rua=mailto:dmarc@bbb.com; ruf=mailto:dmarc@bbb.com
    ```

### 2. Ajuste alternativo
- Usar un **dominio autorizado** como remitente (por ejemplo `@ccc.com`) y añadir `Reply-To: usuario@bbb.com`.

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


# ✉️ RESUMEN EJECUTIVO — Correo no entregado

**Motivo del incidente:**  
El correo fue **rechazado automáticamente** por el servidor del destinatario debido a **fallo en la autenticación DMARC** del dominio `lyntech.com`.

---

## 🧠 Causa raíz
- El servidor de envío (`216.71.158.121`) **no figura en el registro SPF** de `bbb.com`.  
- La firma **DKIM no se validó** correctamente.  
- La política DMARC del dominio (`p=reject`) bloqueó el mensaje.

---

## 🧩 Efecto
El correo no se entregó al destinatario. El sistema receptor cumplió la política DMARC y rechazó el mensaje con el error:

```
550 5.7.509 Access denied, sending domain bbb.com does not pass DMARC verification (p=reject)
```

---

## 🛠️ Recomendaciones
1. **Actualizar SPF** para incluir el servidor de envío:
   ```txt
   include:aadfasdszd.com
   ```
2. **Configurar DKIM** para `bbb.com` en Microsoft 365 u otro sistema de envío.
3. **Revisar DMARC**, usar temporalmente `p=quarantine` hasta validar SPF/DKIM.
4. **Alternativa:** enviar desde `@ewsrwerwe.com` con `Reply-To: @bbb.com`.

---

## 📅 Próximos pasos
- Verificar registros con herramientas DMARC externas.  
- Reenviar el correo una vez actualizados los registros.  
- Supervisar reportes DMARC durante 48 horas posteriores.

