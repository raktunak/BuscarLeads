# VenderWEB - Lead Generation Platform

Plataforma de generacion de listas de clientes potenciales por vertical y region.
Busca negocios sin web profesional para outbound sales.

## Arquitectura

```
Frontend (Next.js) --> API (FastAPI) --> Discovery Engine
                                            |
                              Capa 1: Playwright (Google Maps scraping, gratis)
                              Capa 2: Perplexity API (enriquecimiento)
                              Capa 3: Google Places API (validacion, $200/mes gratis)
                                            |
                                    PostgreSQL + Redis + Celery
```

## Requisitos

- Docker + Docker Compose
- Node.js 18+ (para frontend)
- API key de Perplexity (opcional, para enriquecimiento)
- API key de Google Places (opcional, $200/mes gratis)

## Arranque rapido

### 1. Configurar variables de entorno

```bash
cp .env.example .env
```

Editar `.env` con tus claves:
```
PERPLEXITY_API_KEY=tu_clave_aqui
GOOGLE_PLACES_API_KEY=tu_clave_aqui
JWT_SECRET_KEY=genera_un_secreto_aleatorio
```

### 2. Levantar servicios (PostgreSQL, Redis, API, Celery)

```bash
docker compose up --build -d
```

Esto arranca:
- PostgreSQL 16 con PostGIS en puerto 5432
- Redis 7 en puerto 6379
- FastAPI en puerto 8000
- Celery worker (procesa campanas en background)
- Celery beat (tareas programadas)

### 3. Ejecutar migraciones y seed

```bash
docker compose exec api alembic upgrade head
docker compose exec api python -m app.seed
```

El seed carga:
- 10 verticales (dental, reformas, abogados, estetica, fisio, restaurantes, fontaneria, electricistas, veterinarios, talleres)
- 22 regiones (10 ciudades ES, Espana completa, 3 UK, 3 MX, 2 CO, 1 CL)

### 4. Arrancar frontend

```bash
cd frontend
npm install
npm run dev
```

Abre http://localhost:3000

### 5. Crear cuenta y primera campana

1. Abre http://localhost:3000
2. Crea una cuenta (el primer usuario es admin)
3. Ve a "Campanas" > selecciona vertical + region > "Lanzar"
4. La campana se ejecuta en background (Celery):
   - Scraping de Google Maps por zona
   - Verificacion de presencia web
   - Normalizacion de telefonos
   - Scoring de leads
5. Ve a "Leads" para ver resultados
6. Exporta a CSV o Excel

## API docs

Con el servidor corriendo: http://localhost:8000/docs (Swagger UI)

### Endpoints principales

| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| POST | /api/auth/register | Crear cuenta |
| POST | /api/auth/login | Login (devuelve JWT) |
| GET | /api/catalog/verticals | Listar verticales |
| GET | /api/catalog/regions | Listar regiones |
| POST | /api/campaigns/ | Crear campana (lanza discovery) |
| GET | /api/campaigns/ | Listar campanas |
| GET | /api/leads/ | Listar leads con filtros |
| GET | /api/exports/csv | Exportar a CSV |
| GET | /api/exports/excel | Exportar a Excel |
| GET | /api/dashboard/stats | Metricas agregadas |

## Estructura del proyecto

```
VenderWEB/
├── docker-compose.yml
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI routers + schemas
│   │   ├── discovery/        # Motor de busqueda
│   │   │   ├── engine.py     # Orquestador principal
│   │   │   ├── geo.py        # Grid por densidad (52 provincias ES)
│   │   │   ├── dedup.py      # Deduplicacion telefono + nombre + geo
│   │   │   └── adapters/     # Google Maps scraper, Places API, Perplexity
│   │   ├── enrichment/       # Web checker, phone normalizer, Robinson
│   │   ├── scoring/          # Lead scoring 0-100
│   │   ├── export/           # CSV + Excel con formato
│   │   ├── tasks/            # Celery workers
│   │   └── models/           # SQLAlchemy + PostGIS
│   └── data/                 # YAML seed (verticales, regiones)
└── frontend/                 # Next.js 14 + Tailwind
```

## Scoring de leads (0-100)

| Criterio | Puntos |
|----------|--------|
| Sin web | +40 |
| Web caida/aparcada | +30-35 |
| Sin SSL | +20 |
| Sin mobile responsive | +15 |
| Rating Google > 4.0 | +10 |
| Vertical prioritario | +10 |
| No en Lista Robinson | +10 |
| Tiene telefono | +5 |
| Muchas resenas (>20) | +5 |

## Costes estimados

| Componente | Coste |
|-----------|-------|
| Capa 1 (Playwright scraping) | Gratis |
| Capa 2 (Perplexity API) | Segun plan existente |
| Capa 3 (Google Places API) | $200/mes gratis + $300 creditos iniciales |
| Proxies residenciales (opcional) | $5-15/mes |
| Infraestructura (VPS) | $20-50/mes |

## Comandos utiles

```bash
# Ver logs
docker compose logs -f api celery-worker

# Reiniciar solo el worker
docker compose restart celery-worker

# Shell de Python
docker compose exec api python

# Tests
docker compose exec api pytest -v

# Lint
docker compose exec api ruff check app/
```

## Lista Robinson (Espana)

Para cumplir con RGPD, antes de llamar hay que verificar contra la Lista Robinson:

1. Solicitar la lista a ADIGITAL (https://www.listarobinson.es)
2. Subir el CSV al sistema:
```bash
docker compose exec api python -c "
import asyncio
from app.enrichment.robinson import import_robinson_csv
from app.database import async_session
async def run():
    async with async_session() as db:
        count = await import_robinson_csv('/path/to/robinson.csv', db)
        print(f'{count} numeros importados')
asyncio.run(run())
"
```

Los leads con numeros en Robinson se marcan automaticamente y se excluyen de las exportaciones por defecto.
