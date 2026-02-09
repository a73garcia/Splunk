📧 PLAN COMPLETO DE CONTINGENCIA

Caída de Pasarela de Seguridad de Correo Proofpoint

------------------------------------------------------------------------

📑 Índice

1.  Introducción
2.  Objetivo
3.  Alcance
4.  Arquitectura del Servicio
5.  Dependencias Técnicas
6.  Análisis de Riesgos
7.  Escenarios de Contingencia
8.  Procedimiento Operativo de Activación
9.  Procedimiento Técnico Detallado
10. Hardening de Seguridad Durante Contingencia
11. Monitorización SOC
12. Procedimiento de Rollback
13. Plan de Comunicación
14. Pruebas y Validaciones
15. Mantenimiento del Plan
16. Roles y Responsabilidades
17. KPIs y Métricas
18. Anexos Técnicos
19. Versionado

------------------------------------------------------------------------

1. Introducción

Este documento define el plan de contingencia para garantizar la
continuidad del servicio de correo electrónico corporativo en caso de
indisponibilidad parcial o total de la pasarela de seguridad Proofpoint.

La organización dispone de una arquitectura basada en:

-   Proofpoint como pasarela principal
-   Microsoft Exchange Online (O365)
-   Microsoft Defender for Office 365

------------------------------------------------------------------------

2. Objetivo

Garantizar:

-   Continuidad del servicio de correo
-   Mantenimiento de niveles mínimos de seguridad
-   Reducción del impacto operativo
-   Procedimientos claros de activación y rollback

------------------------------------------------------------------------

3. Alcance

Este plan cubre:

-   Correo entrante
-   Correo saliente
-   Filtrado antimalware
-   Protección antiphishing
-   Protección antispam
-   Monitorización SOC

------------------------------------------------------------------------

4. Arquitectura del Servicio

Arquitectura Normal

Internet → Proofpoint → Exchange Online → Defender → Usuarios

Arquitectura en Contingencia

Internet → Exchange Online → Defender → Usuarios

------------------------------------------------------------------------

5. Dependencias Técnicas

Infraestructura

-   DNS público
-   Registros MX
-   Conectores Exchange Online
-   Políticas Defender
-   Monitorización SIEM
-   Proofpoint Gateway

------------------------------------------------------------------------

6. Análisis de Riesgos

Interrupción correo — Crítico
Pérdida de correos — Alto
Entrada de malware — Crítico
Spam masivo — Alto

------------------------------------------------------------------------

7. Escenarios de Contingencia

Escenario 1 — Caída Total Proofpoint

Indicadores: - No entrega correo - Alertas monitorización - Colas SMTP
elevadas

Escenario 2 — Proofpoint sin Filtrado

Indicadores: - Incremento spam - Incremento malware downstream

Escenario 3 — Caída solo salida SMTP

Indicadores: - NDR masivos - Bloqueo envío externo

------------------------------------------------------------------------

8. Procedimiento Operativo de Activación

Paso 1 – Confirmación Incidente
Paso 2 – Clasificación Incidente
Paso 3 – Escalado

------------------------------------------------------------------------

9. Procedimiento Técnico Detallado

Cambio MX hacia: .mail.protection.outlook.com

Comprobación DNS: nslookup -type=mx dominio.com

PowerShell:

Connect-ExchangeOnline
Set-InboundConnector -Identity “Proofpoint Connector” -Enabled $false

Set-OutboundConnector -Identity “Proofpoint SmartHost” -Enabled $false

------------------------------------------------------------------------

10. Hardening Durante Contingencia

-   Anti-Spam Strict
-   Safe Attachments Block
-   Safe Links Enabled
-   Protección Impersonation

------------------------------------------------------------------------

11. Monitorización SOC

Vigilar: - Ratio spam - Ratio malware - Latencias SMTP - Volumen correo

------------------------------------------------------------------------

12. Procedimiento Rollback

-   Confirmar recuperación Proofpoint
-   Restaurar MX
-   Reactivar conectores
-   Validar SPF, DKIM, DMARC

------------------------------------------------------------------------

13. Plan de Comunicación

Usuarios: - Posible incremento spam

Dirección IT: - Estado servicio - Impacto negocio

------------------------------------------------------------------------

14. Pruebas y Validaciones

-   Simulación failover MX
-   Pruebas phishing controladas
-   Validación políticas Defender

------------------------------------------------------------------------

15. Mantenimiento del Plan

-   Revisión anual
-   Revisión tras incidentes
-   Actualización rangos IP

------------------------------------------------------------------------

16. Roles y Responsabilidades

SOC — Monitorización
Infraestructura — Cambios DNS
Seguridad — Hardening
Service Manager — Coordinación

------------------------------------------------------------------------

17. KPIs

-   Tiempo activación contingencia
-   Tiempo recuperación servicio
-   Ratio amenazas detectadas

------------------------------------------------------------------------

18. Anexos Técnicos

Validación SPF: nslookup -type=txt dominio.com

Validación DKIM: selector._domainkey.dominio.com

Validación TLS: openssl s_client -starttls smtp -connect dominio.com:25

------------------------------------------------------------------------

19. Versionado

Versión 1.0 — Documento inicial

------------------------------------------------------------------------