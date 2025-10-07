# 🌐 Registros DNS

Los registros **DNS (Domain Name System)** permiten traducir los nombres de dominio legibles (como `ejemplo.com`) en direcciones IP o servicios específicos dentro de Internet.  
Esta guía describe los principales tipos de registros DNS, sus funciones y ejemplos prácticos.

---

## 🧭 HOST (A + PTR)

### 🔹 Registro A
Asocia un **nombre de dominio** con una **dirección IPv4**.  
Es el registro más común para sitios web, servidores o servicios.

```bash
www.ejemplo.com → 203.0.113.45
```

> 💡 **Usa este registro si vas a cambiar la IP de un servidor web o de correo.**

---

### 🔹 Registro PTR
Es el **registro inverso** de un registro A.  
Convierte una IP en un nombre de dominio.

```bash
203.0.113.45 → mail.ejemplo.com
```

> ⚠️ Muy importante para servidores de correo: ayuda a evitar que tus mensajes se marquen como spam.

---

## 🌐 A
Define la dirección **IPv4** de un dominio o subdominio.  
Cada subdominio puede tener su propio registro A.

```bash
mail.ejemplo.com → 192.168.1.25
```

---

## 🧱 CNAME (Canonical Name)
Crea un **alias** que apunta a otro nombre de dominio.  
No puede coexistir con otros registros del mismo nombre.

```bash
blog.ejemplo.com → ghs.google.com
```

> 🪄 Útil para servicios como Google Sites, GitHub Pages o alias de subdominios.

---

## 📬 MX (Mail Exchange)
Indica los **servidores de correo electrónico** que gestionan el dominio.  
Permite definir **prioridades**: el número más bajo tiene mayor prioridad.

```bash
ejemplo.com
10 mail1.ejemplo.com
20 mail2.ejemplo.com
```

> 📧 Necesario para que tu dominio pueda **recibir correos**.

---

## 🧭 NS (Name Server)
Define los **servidores DNS autoritativos** del dominio.  
Estos servidores contienen la información oficial de tus registros.

```bash
ejemplo.com
ns1.proveedor.com
ns2.proveedor.com
```

> 🔐 Cambiar estos registros puede delegar tu dominio a otro proveedor DNS.

---

## 🔄 PTR (Pointer)
Realiza la **resolución inversa**: de IP a nombre.  
Usado para verificar la identidad de servidores, sobre todo en el envío de correo.

```bash
203.0.113.45 → mail.ejemplo.com
```

> ✅ Debe coincidir con el registro A correspondiente.

---

## ⚙️ SRV (Service Record)
Define **servicios específicos**, protocolos y puertos.

Formato:
```
_servicio._protocolo.dominio prioridad peso puerto destino
```

**Ejemplo:**
```bash
_sip._tcp.ejemplo.com → 10 60 5060 sipserver.ejemplo.com
```

> Usado por Microsoft 365, Teams, VoIP, LDAP, etc.

---

## 🧾 TXT (Text Record)
Permite añadir **texto libre** en el DNS.  
Se utiliza principalmente para **verificaciones** y **autenticaciones de correo** (SPF, DKIM, DMARC).

---

### 🔹 TXT (SPF)
Define los servidores **autorizados para enviar correos** en nombre de tu dominio.

```bash
v=spf1 include:_spf.google.com ~all
```

- `v=spf1`: versión del registro SPF.  
- `include:`: dominios autorizados.  
- `~all`: todo lo demás será “softfail”.

> 🛡️ Evita la suplantación de identidad (spoofing).

---

### 🔹 TXT (DKIM)
Publica la **clave pública** usada para firmar digitalmente los correos.

```bash
v=DKIM1; k=rsa; p=MIGfMA0GCSqGSIb3DQEBAQUAA4...
```

> 🔏 Garantiza que el mensaje no ha sido modificado y proviene de tu dominio.

---

### 🔹 TXT (DMARC)
Establece la **política de autenticación** y los **reportes** para SPF y DKIM.

```bash
v=DMARC1; p=quarantine; rua=mailto:report@ejemplo.com
```

- `p=none | quarantine | reject`: acción ante fallos.  
- `rua`: dirección para reportes automáticos.

> 📊 Ayuda a controlar la autenticidad y reputación del correo.

---

## 🧩 Resumen de Tipos de Registros

| Tipo | Nombre | Función principal | Ejemplo |
|------|---------|--------------------|----------|
| **A** | Address | Nombre → IP (IPv4) | `www → 192.168.1.10` |
| **PTR** | Pointer | IP → Nombre | `192.168.1.10 → www` |
| **CNAME** | Canonical Name | Alias de otro nombre | `blog → ghs.google.com` |
| **MX** | Mail Exchange | Servidor de correo | `@ → mail.ejemplo.com` |
| **NS** | Name Server | DNS autoritativo | `@ → ns1.proveedor.com` |
| **SRV** | Service | Define servicios y puertos | `_sip._tcp → servidor SIP` |
| **TXT (SPF)** | Sender Policy Framework | Control de envío de correo | `v=spf1 include:spf.google.com` |
| **TXT (DKIM)** | DomainKeys Identified Mail | Firma digital de correo | Clave pública DKIM |
| **TXT (DMARC)** | Domain-based Message Authentication | Política y reportes SPF/DKIM | `v=DMARC1; p=reject` |

---

## ✅ Buenas Prácticas

1. Verifica siempre la propagación DNS con herramientas como `dig`, `nslookup` o [MXToolbox](https://mxtoolbox.com).  
2. Asegúrate de que los registros **A y PTR coincidan** en los servidores de correo.  
3. Evita duplicar registros **CNAME** o **SPF**.  
4. Comprueba la **sintaxis** de DKIM y DMARC antes de publicarlos.  
5. Documenta y guarda un **historial de cambios DNS**.  
6. Si usas varios proveedores (Cloudflare, Microsoft, Google, etc.), revisa que los valores estén sincronizados.

---

## 🧠 Nota Final

Los registros DNS son la **columna vertebral de tu identidad digital**.  
Una mala configuración puede afectar la navegación web, la recepción de correos o la reputación de tu dominio.  
Mantén tus registros revisados y actualizados regularmente.

---

