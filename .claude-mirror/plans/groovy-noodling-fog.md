# Plan: Aplicación de Generación de Listas de Clientes por Vertical y Región

## Context

El negocio "Webs PYMEs IA" necesita una herramienta interna que, dado un **vertical de negocio** (ej: "clínicas dentales", "reformas") y una **región** (ej: "Madrid", "Barcelona provincia"), genere automáticamente listas de posibles clientes — negocios que probablemente NO tienen web profesional y son candidatos para outbound sales.

Actualmente el repositorio `c:/VenderWEB` está vacío (solo git init). Se necesita crear la aplicación desde cero.

---

## Arquitectura: Modular Monolith

```
┌─────────────────────────────────────────────┐
│            FRONTEND (Next.js)               │
│  Dashboard / Campañas / Leads / Exportar    │
└─────────────────────┬───────────────────────┘
                      │ REST API
┌─────────────────────▼───────────────────────┐
│            API (FastAPI)                     │
│  Auth │ Campaigns │ Leads │ Exports         │
└──┬──────────┬──────────┬──────────┬─────────┘
   │          │          │          │
   ▼          ▼          ▼          ▼
 AUTH    DISCOVERY    ENRICHMENT   SCORING
         ENGINE       PIPELINE    & EXPORT
            │              │
            ▼              ▼
      DATA SOURCES     WEB CHECKER
      (Google Places,  (HTTP, SSL,
       Directorios)     CMS detect)
            │              │
            └──────┬───────┘
                   ▼
          PostgreSQL + Redis
```

---

## Tech Stack

| Capa | Tecnología | Justificación |
|------|-----------|---------------|
| Backend | **Python 3.12 + FastAPI** | Mejor ecosistema para scraping, APIs, y procesamiento de datos |
| Tasks | **Celery + Redis** | Jobs largos de discovery/enrichment asíncronos |
| DB | **PostgreSQL 16 + PostGIS** | JSONB, búsqueda geoespacial, full-text search |
| Frontend | **Next.js 14 + shadcn/ui + Tailwind** | Server components, i18n (es/en), dashboards rápidos |
| Containers | **Docker Compose** | Dev local inmediato |

---

## Estrategia de Datos: Modelo Híbrido de 3 Capas (coste ~€0)

El enfoque NO depende de una sola fuente de pago. Se combinan 3 capas para máxima cobertura con coste mínimo:

```
CAPA 1: Scraping gratuito (cobertura masiva)
├── Playwright/Puppeteer scrapeando Google Maps directamente
├── Scraping Páginas Amarillas / directorios locales
└── ~100.000+ negocios/mes, coste = €0

CAPA 2: Perplexity API (enriquecimiento inteligente)
├── Ya disponible (el equipo tiene API)
├── Para cada lead: buscar email, redes sociales, datos extra
├── Consultas tipo "¿tiene [negocio] presencia online?"
└── Enriquecer contexto que el scraping no captura

CAPA 3: Google Places API (validación quirúrgica)
├── Solo para leads "calientes" (sin web, score alto)
├── Validar teléfono, dirección, rating actualizado
├── Free tier: $200/mes gratis = ~66.000 requests (Basic+Contact)
└── $300 créditos de regalo al crear cuenta Google Cloud (90 días)
```

### Capa 1 — Scraping Google Maps con Navegador Automatizado

Un agente con Playwright/Puppeteer abre Google Maps, busca el vertical en cada zona y extrae resultados directamente del HTML.

**Datos que devuelve cada resultado de Google Maps:**
- Nombre del negocio
- Dirección completa (calle, ciudad, CP, provincia)
- Coordenadas GPS
- Teléfono (cuando el negocio lo tiene en ficha)
- Website URL (si tiene — **dato clave para nosotros**)
- Google Maps URL
- Rating medio (1-5 estrellas)
- Número total de reseñas
- Horario de apertura
- Categorías del negocio
- Fotos del negocio
- Nivel de precio ($, $$, $$$)

**Lo que NO da Google Maps:** email, nombre del propietario, facturación, empleados, redes sociales → para eso usamos Capa 2 (Perplexity).

**Mitigación de riesgos del scraping:**

| Riesgo | Mitigación |
|--------|-----------|
| CAPTCHAs | Rotar IPs con proxies residenciales (~$5-15/mes) |
| Ban de IP | Rate limiting: 1 búsqueda cada 10-15 seg |
| ToS Google | Zona gris; datos públicos pero Google lo prohíbe en ToS |
| HTML cambia | Usar MCP Browser + agente IA que interpreta visualmente |
| Datos inconsistentes | Validar con Capa 3 (API oficial) para leads calientes |

**Alternativa limpia:** Servicios como Outscraper o SerpAPI hacen el scraping de Google Maps por ti (~$2-3/1000 resultados vs $32 de la API oficial).

### Estrategia de Cobertura Nacional (España completa)

Para cubrir toda España con un vertical se usan 3 niveles de densidad:

**Provincias rurales (40 provincias):** 1 búsqueda con radio amplio → ~60 negocios cada una
**Provincias medias (8: Valencia, Sevilla, Málaga...):** subdividir en 5-10 zonas → ~300-500 cada una
**Madrid y Barcelona:** grid fino de 3x3km → ~500-1.000 cada una

| Vertical completo España | Búsquedas | Coste scraping | Negocios estimados |
|-------------------------|-----------|---------------|-------------------|
| Dentistas | ~500 | €0 (scraping) | ~15.000-25.000 |
| Reformas | ~500 | €0 | ~30.000-50.000 |
| **5 verticales completos** | **~2.500** | **€0** | **~100.000+** |

### Capa 2 — Perplexity API (ya disponible)

Usar la API de Perplexity que el equipo ya tiene para:
- Buscar email y redes sociales de leads específicos
- Consultas de validación: "¿tiene [ClínicaX en Sevilla] página web?"
- Investigar directorios locales por país/vertical
- Enriquecer datos que el scraping no captura (ej: años de actividad, especialidades)

### Capa 3 — Google Places API (validación selectiva)

Solo para leads que pasan el filtro (sin web, score alto). Valida datos con fuente oficial.

**Pricing de Google Places API:**

| Nivel de datos | Coste/1000 req | Qué incluye |
|---------------|---------------|-------------|
| Basic | **$0 (gratis)** | Nombre, dirección, coordenadas, place_id |
| Contact | **$3/1000** | + teléfono, website, horario |
| Atmosphere | $5/1000 | + rating, reseñas, fotos |
| Todos los campos | $32/1000 | Todo junto |

**Se cobra por request (petición), no por resultado.** 1 request = hasta 20 resultados.

**Créditos gratuitos disponibles:**
- **$300 de regalo** al crear cuenta Google Cloud Platform (90 días)
- **$200/mes gratis permanentes** en Google Maps Platform
- Con Basic+Contact ($3/1000): ~66.000 requests gratis/mes = ~1,3M negocios
- Con todos los campos ($32/1000): ~6.000 requests gratis/mes = ~120.000 negocios

### Capa 2b — Directorios por país (scraping complementario)
- **España:** Páginas Amarillas, QDQ
- **UK:** Yell.com, FreeIndex
- **México:** Sección Amarilla
- **Colombia/Chile:** Páginas Amarillas locales
- **USA:** Yelp API, YellowPages

### Capa 4 — Registros públicos
- **España:** CNAE (BORME), Infoempresa
- **UK:** Companies House API (gratuita)

### Verificación de presencia web
- HTTP GET + SSL check + viewport meta tag + detección CMS
- PageSpeed Insights API (gratuita, 25K/día) para calidad

---

## Esquema de Base de Datos (tablas principales)

1. **`verticals`** — Verticales con search terms multilingües, códigos CNAE/SIC/NAICS
2. **`regions`** — Regiones con geocoding (centro, bounding box, país, zona horaria)
3. **`campaigns`** — Cada ejecución: vertical + región, status, totales
4. **`businesses`** — Registro maestro deduplicado: datos del negocio, presencia web, scoring, compliance
5. **`campaign_businesses`** — Junction table con raw data de cada fuente
6. **`outreach_log`** — Tracking de llamadas/emails/WhatsApp
7. **`users`** — Auth con roles (admin, manager, sales_rep)
8. **`robinson_list`** — Cache de Lista Robinson (España)
9. **`api_usage`** — Tracking de costes de APIs

---

## Módulos Core

### 1. `discovery/` — Motor de Descubrimiento
- `engine.py` — Orquestador: vertical+región → fan-out a adapters → dedup → raw results
- `adapters/google_maps_scraper.py` — **Capa 1 (MVP)**: Playwright scrapeando Google Maps directamente. Grid subdivision por densidad (rural/media/densa). Rate limiting + proxy rotation
- `adapters/google_places_api.py` — **Capa 3**: API oficial para validación quirúrgica de leads calientes
- `adapters/perplexity.py` — **Capa 2**: Consultas de enriquecimiento via Perplexity API (email, redes, validación web)
- `adapters/paginas_amarillas.py` — Scrapy para España (Fase 2)
- `adapters/base.py` — Clase abstracta que todos los adapters implementan
- `dedup.py` — Deduplicación: teléfono E.164 → nombre normalizado + proximidad geo (PostGIS)
- `geo.py` — Geocoding, subdivisión de bounding box en celdas, estrategia por densidad provincial

### 2. `enrichment/` — Pipeline de Enriquecimiento
- `web_checker.py` — HTTP check, SSL, mobile viewport, tiempo de carga
- `cms_detector.py` — Detectar WordPress/Wix/Squarespace desde HTML
- `perplexity_enricher.py` — Usar Perplexity API para buscar email, redes sociales, datos extra de leads específicos
- `robinson.py` — Cross-check contra Lista Robinson
- `phone_normalizer.py` — Normalización E.164 con librería `phonenumbers`

### 3. `scoring/` — Puntuación de Leads (0-100)
- Sin web: +40 pts
- Sin SSL / sitio roto: +20 pts
- Rating alto (>4.0, >20 reseñas): +10 pts (negocio exitoso, puede pagar)
- Vertical prioritario: +10 pts
- Negocio 2-10 años: +5 pts
- No en Lista Robinson: +10 pts

### 4. `export/` — Exportación
- CSV y XLSX con filtros y formato condicional
- Futuro: push a HubSpot/Pipedrive via API

### 5. `api/` — FastAPI
- CRUD de campañas, consulta de leads, exportaciones, auth JWT

### 6. `frontend/` — Next.js Dashboard
- `/dashboard` — Estadísticas generales
- `/campaigns/new` — Crear campaña (seleccionar vertical + región)
- `/campaigns/[id]` — Progreso y resultados
- `/leads` — Explorador global con filtros (score, vertical, región, tiene web, contactado)
- `/exports` — Generar y descargar

---

## Alcance MVP (4-6 semanas)

### Incluido en MVP:
1. **Google Maps scraper con Playwright** (Capa 1) — cobertura masiva gratuita
2. **Perplexity API adapter** (Capa 2) — enriquecimiento inteligente con API ya disponible
3. **Google Places API adapter** (Capa 3) — validación selectiva con free tier ($200/mes gratis)
4. **Estrategia de cobertura nacional** — grid por densidad provincial (rural/media/densa)
5. 1 vertical como prueba (clínicas dentales en España), fácil agregar más via YAML
6. Web presence check básico (HTTP + SSL + viewport)
7. Lead scoring simplificado
8. Campaign CRUD via API
9. Dashboard Next.js: crear campaña, ver resultados, exportar CSV
10. PostgreSQL + PostGIS + Redis en Docker Compose
11. Auth JWT básico
12. Lista Robinson: upload manual de CSV
13. Proxy rotation básico para scraping (~$5-15/mes)

### Fuera del MVP:
- Scrapers de directorios (Páginas Amarillas, Yell)
- Detección de CMS y responsive
- Integraciones CRM
- Multi-usuario con roles
- Outreach logging
- MCP Browser + agente IA para scraping adaptativo
- Elasticsearch
- Deploy cloud (funciona local o VPS)

---

## Compliance Legal

| País | Regulación | Registro opt-out | Acción requerida |
|------|-----------|-----------------|-----------------|
| España | RGPD Art. 6.1.f | Lista Robinson (ADIGITAL) | Check obligatorio antes de llamar |
| UK | PECR | TPS/CTPS | Screening contra registro |
| USA | FTC TSR + TCPA | Do Not Call Registry | Check antes de llamar |
| México | LFPDPPP | REUS (Profeco) | Check recomendado |

- Solo datos B2B públicos (interés legítimo)
- Respetar robots.txt en scraping
- Max 1 req/seg por dominio scrapeado
- No cachear datos de Google Places >30 días sin refresh

---

## Estructura de Directorio

```
VenderWEB/
├── docker-compose.yml
├── Makefile
├── .env.example
├── backend/
│   ├── pyproject.toml
│   ├── alembic/
│   ├── app/
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/
│   │   ├── api/
│   │   │   ├── main.py
│   │   │   ├── routers/ (campaigns, leads, exports, auth, dashboard)
│   │   │   └── schemas/
│   │   ├── discovery/
│   │   │   ├── engine.py
│   │   │   ├── dedup.py, geo.py
│   │   │   └── adapters/
│   │   │       ├── base.py
│   │   │       ├── google_maps_scraper.py  (Capa 1 - Playwright)
│   │   │       ├── google_places_api.py    (Capa 3 - API oficial)
│   │   │       ├── perplexity.py           (Capa 2 - enriquecimiento)
│   │   │       └── paginas_amarillas.py    (Fase 2)
│   │   ├── enrichment/
│   │   │   ├── pipeline.py, web_checker.py
│   │   │   ├── perplexity_enricher.py
│   │   │   ├── cms_detector.py, robinson.py
│   │   │   └── phone_normalizer.py
│   │   ├── scoring/ (scorer.py, rules.py)
│   │   ├── export/ (csv, excel)
│   │   └── tasks/ (celery workers)
│   ├── tests/
│   └── data/ (verticals.yaml, regions.yaml)
├── frontend/
│   ├── package.json
│   └── src/app/ (dashboard, campaigns, leads, exports)
└── docs/
```

---

## Secuencia de Implementación

### Semana 1-2: Infraestructura + Discovery (Capa 1)
- Docker Compose (PostgreSQL+PostGIS, Redis, FastAPI, Celery)
- Modelos SQLAlchemy + migraciones Alembic
- **Google Maps scraper con Playwright** (Capa 1): búsqueda por vertical+zona, extracción de datos, rate limiting
- **Estrategia de cobertura nacional**: geo.py con grid por densidad provincial
- API endpoint para crear campañas
- Web checker básico + phone normalizer

### Semana 3-4: Enriquecimiento + Scoring + Frontend
- **Perplexity API adapter** (Capa 2): enriquecer leads con email, redes, validación
- **Google Places API adapter** (Capa 3): validación selectiva de leads calientes
- Scoring module
- Deduplicación (teléfono E.164 + nombre normalizado + proximidad geo)
- Flow end-to-end: crear campaña → scrape → enrich → score
- CSV/Excel export
- Next.js: formulario de campaña, tabla de resultados, filtros, exportar

### Semana 5-6: Polish + Compliance + Escala
- Lista Robinson (upload CSV, cross-reference)
- Proxy rotation para scraping sostenible
- Dashboard con estadísticas
- i18n (es/en)
- Añadir 4+ verticales (construcción, belleza, abogados, fisio)
- **Test de cobertura nacional**: ejecutar 5 verticales x toda España
- Tests, error handling, retry logic
- Documentación

---

## Verificación

1. Crear campaña "Clínicas dentales en Madrid"
2. Verificar que descubre >100 negocios via Google Places
3. Verificar deduplicación (no hay duplicados por teléfono)
4. Verificar que el web checker clasifica correctamente (sin web vs con web)
5. Verificar scoring: negocios sin web aparecen primero
6. Exportar CSV y verificar que todos los campos están completos
7. Verificar que negocios en Lista Robinson están excluidos de exports
8. Repetir con otro vertical (reformas) y otra región (Barcelona)
