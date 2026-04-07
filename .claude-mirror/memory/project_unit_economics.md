---
name: Unit economics y pricing recomendado
description: Costes por web, LTV por escenario, escalabilidad, pricing por mercado, upsells y modelo de ingresos del proyecto VenderWEB.
type: project
---

## Coste real por web

| Componente | Conservador | Optimista |
|-----------|-------------|-----------|
| IA (API) | €2,00 | €0,30 |
| Hosting mensual | €5,00/mes | €1,50/mes |
| Dominio/SSL/CDN | €1,50/mes | €0,50/mes |
| QA humano (setup) | €15,00 | €5,00 |
| **Coste setup total** | **€17** | **€5,30** |
| **Coste operativo/mes** | **€6,50/mes** | **€2,00/mes** |

## Infraestructura low-cost
- Cloudflare for SaaS: 100 hostnames incluidos, $0.10/mes por hostname adicional
- Let's Encrypt: certificados TLS gratuitos
- La parte cara es humana: onboarding, iteraciones, soporte → productizar mantenimiento

## LTV por escenario

| Plan | Precio/mes | Churn | Vida media | LTV (GP 80%) |
|------|-----------|-------|-----------|-------------|
| Básico España | €49 | 5% | 20 meses | €784 |
| Básico España | €49 | 3% | 33 meses | €1.294 |
| Pro España | €79 | 4% | 25 meses | €1.580 |
| Premium US/UK | $149 | 4% | 25 meses | $2.980 |
| Básico LATAM | $29 | 5% | 20 meses | $464 |

## Escalabilidad

| Clientes | MRR | Costes var. | Costes fijos | Beneficio | Margen |
|----------|-----|------------|-------------|-----------|--------|
| 100 | €4.900 | €1.000 | €5.000 | -€1.100 | -22% |
| 200 | €9.800 | €2.000 | €7.000 | €800 | 8% |
| 500 | €24.500 | €5.000 | €10.000 | €9.500 | 39% |
| 500 (upsells) | €39.500 | €7.500 | €12.000 | €20.000 | 51% |
| 1.000 (upsells) | €79.000 | €15.000 | €15.000 | €49.000 | 62% |

## Pricing recomendado por mercado

| Plan | España | LATAM | US/UK |
|------|--------|-------|-------|
| Starter | €39-€49/mes | $25-$35/mes | $59-$79/mes |
| Professional | €79-€99/mes | $49-$69/mes | $99-$149/mes |
| Premium | €149-€199/mes | $89-$129/mes | $199-$299/mes |
| Descuento anual | 2 meses gratis | 2 meses gratis | 2 meses gratis |

## Upsells de mayor rentabilidad

| Servicio | Coste | Precio venta | Margen | Adopción |
|----------|-------|-------------|--------|----------|
| Dominio + email | €2-5/mes | €10-19/mes | 75% | 40-60% |
| SEO local | €100-300/mes | €200-500/mes | 55% | 15-25% |
| Email marketing | €30-80/mes | €79-149/mes | 65% | 15-25% |
| Páginas extra | €15-50/pág | €50-150/pág | 70% | 20-30% |
| Google Ads mgmt | €200-400/mes | €300-750/mes | 45% | 10-20% |

## Churn benchmark
Recurly: overall churn rate 3,27%. Micro-pymes suele ser más volátil.
- Saludable: 3-5% mensual
- Peligro: 7-10% mensual

## Break-even ejemplo
- Precio base: €79/mes, margen bruto 75-85%
- Comisión comercial: 1 mes MRR + clawback
- CAC efectivo: 300-700€ (si rep vende 5-10 cierres/mes)
- Payback ~7 meses con margen bruto ~60-70€/mes
- Palancas: (i) setup fee opcional, (ii) anualidad con descuento, (iii) upsells

## Pricing alternativo (segundo análisis, validación 90 días España)

### Plan "Publicada" (core)
- 69-89 €/mes, contrato mínimo 12 meses
- Incluye: hosting, SSL, 1 landing + páginas servicio, CTAs, formulario/WhatsApp/call, 2 cambios menores/mes, uptime monitoring, backups

### Setup opcional
- 0€ ("self-serve": cliente aporta textos)
- 199-499€ ("done-for-you": copy + estructura + tracking + dominio + integraciones)

### Upsells productizados adicionales
- "Pack reseñas + reputación" (solicitud automatizada, link directo, landing de reseñas)
- "SEO local básico" (páginas por servicio/área, schema, mejoras on-page)
- "Ads de captación" (solo si hay tracking y call tracking)
- "Contenido mensual" (1 post/mes, 1 caso, 1 antes/después)
- Principio: no vender nada que no puedas entregar con procesos y plantillas

## Referencia mercado mantenimiento web España
- Cronoshare/mercado: tarifas planas habituales 50-150€/mes según complejidad
- WordPress hosting gestionado desde pocos €/mes (ej. Webempresa)

## Comparables high-ticket angloparlantes
- Thryv: desde $646/mes
- Hibu: desde ~$449/mes en comparadores
- Yell: desde £249/mes (e-commerce powered by Wix)
→ Hueco claro para "entry plan" accesible con upsells

## SLA operativo recomendado (proteger margen)
- Soporte por ticket: respuesta 24-48h (plan base)
- Urgencias: solo caídas (no "cambia un texto ya")
- Teléfono: solo plan premium o horas consultoría prepagadas

## Qué NO ofrecer (fase 1)
- E-commerce complejo a medida
- Integraciones raras sin plantilla
- "SEO garantizado" (riesgo reputacional y legal)
- Soporte inmediato ilimitado

## Cuellos de botella operativos típicos
- Revisiones creativas infinitas
- Migraciones mal definidas
- "SEO" como promesa vaga
