---
name: Marco legal y compliance por mercado
description: Regulación outbound (España/UK/US), estructura legal red comercial, riesgos de agencia, WhatsApp API, y compliance publicitario.
type: project
---

## Red comercial España
- **Recomendado:** Contrato de Agencia (Ley 12/1992, BOE-A-1992-12347)
- Agente como autónomo, facturando con IVA (21%) y retención IRPF (15%, o 7% primeros 3 años)
- **Riesgo:** reclasificación laboral si falta autonomía real
- **Riesgo financiero:** Indemnización por clientela (Art. 28) al terminar

## Red comercial otros mercados
- **México (⚠️ ALTO):** presunción relación laboral para comisionistas permanentes. Solución: contratos B2B con persona moral
- **Colombia:** agencia comercial obliga a cesantía comercial al terminar (~1 año comisiones)
- **Argentina (⚠️ MUY ALTO):** Art. 23 LCT presunción fortísima laboral. Solo viable B2B (SAS/SRL)
- **EE.UU.:** 1099 independent contractors. Precaución en California (AB5)
- **UK:** self-employed agents fuera de IR35

## Compliance outbound

### España
- AEPD: cambio de régimen en llamadas comerciales. No pueden realizarse llamadas a números generados aleatoriamente sin consentimiento previo
- Sistemas de exclusión publicitaria (Lista Robinson)
- Práctica: listas B2B verificadas, pruebas de interés legítimo, canales menos intrusivos

### Reino Unido
- No llamar a números en TPS/CTPS salvo consentimiento
- Obligación de "screen" listas contra registros TPS

### Estados Unidos
- FTC Telemarketing Sales Rule + Do Not Call Registry
- TCPA para robocalls/robotexts: mantener "human-in-the-loop"

## WhatsApp Business API
- Permite flujos conversacionales con CTAs, rich media y listas de productos
- **⚠️ RIESGO (desde 15 enero 2026):** cambios de términos limitan "general purpose AI assistants" en WhatsApp. Marco de "AI Providers" con restricciones
- CE ha comunicado fricción por posible exclusión de asistentes de terceros
- **Implicación:** vender "automatización de atención del negocio" (customer support/triage), NO "ponte un ChatGPT en WhatsApp"
- Diseñar arquitectura multi-canal (web chat, email, voz) para no depender de una sola plataforma

## Riesgos publicitarios
- "Web gratis" = posible publicidad engañosa (Directiva EU 2005/29/EC, FTC "Operation AI Comply")
- **Mitigación:** usar "demo gratuita", revelar siempre que el servicio completo requiere suscripción
