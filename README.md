# GeoFlight Scout (IN-first)

**A smart, search-only flight finder with transit safety ranking for Indian travelers.**

GeoFlight Scout is an MVP web application that helps Indian passport holders find the cheapest flight options while highlighting transit and visa risk factors. Instead of just sorting by price, it uses heuristic-based risk assessment to surface safer transit patterns.

## 🎯 Core Value Proposition

- **Cheap flights with safer transit patterns** for Indian travelers
- **Transparent risk scoring** with clear warnings and verification steps
- **No scraping** — uses only official Amadeus API
- **Honest disclaimers** — never claims authoritative visa guidance
- **Single deployment** — FastAPI serves both API and built frontend

## ⚠️ Important Disclaimers

**READ THIS BEFORE USING:**

1. **Transit/visa guidance is heuristic-based and NOT authoritative.** This app uses general patterns and best-effort data to flag potential issues. It does NOT replace official sources.

2. **Always verify with official sources** (embassy, consulate, airline, government travel advisories) before booking any flight.

3. **"Safe transit" is a product feature**, not a legal guarantee. The risk scoring is based on common patterns for Indian passport holders but individual circumstances vary widely.

4. **Preferred/caution transit countries** are editable heuristics in the code (see `backend/app/services/risk_engine.py`). You can customize these lists for your needs.

5. **No booking functionality** — this is a search and analysis tool only.

6. **Travel documents influence** — if you indicate holding a US visa, for example, the app will reduce policy penalties, but you must still verify actual transit requirements.

## 🏗️ Architecture

### Tech Stack

- **Backend:** Python 3.11+, FastAPI, SQLite, uv (package manager)
- **Frontend:** React 18, Vite, TypeScript, Tailwind CSS
- **Flight Data:** Amadeus Self-Service API (OAuth2)
- **Visa Baseline:** TravelBriefing API (best-effort, free)

### Key Features

#### 1. **Transit Safety & Visa Risk Engine (IN-first)**

Implements heuristic-based risk assessment with:

- **PREFERRED transit hubs** (for IN passport): SG, AE, QA, TR, MY, TH, HK, JP, KR
- **CAUTION transit hubs** (often require visas): US, CA, AU
- **VERIFY-HEAVY** regions: Schengen, UK (DATV rules)

**Hard HIGH-risk triggers:**
- Airport change (e.g., LHR → LGW)
- Overnight layover
- Layover > 8 hours
- Connection < 75 minutes

**Policy adjustments:**
- Transiting US without visa → HIGH risk
- Transiting US with US visa → reduced risk (but still verify)
- Transiting Schengen → MEDIUM risk + verify ATV requirements
- Preferred hubs (SG, AE, etc.) → can reduce risk by one level

#### 2. **Scoring & Ranking System**

Results are ranked by weighted score combining:
- Price (normalized)
- Duration (normalized)
- Stops penalty
- Risk penalty (LOW=0, MEDIUM=1, HIGH=3)
- Caution country penalty (+1.5 per caution transit)
- Preferred country bonus (-0.5 per preferred transit)
- Travel docs bonus (-0.3 if relevant)

**Three safety modes:**
- **price_first**: Prioritize cheapest flights (risk weight = 0.6x)
- **balanced** (default): Balance price and safety (risk weight = 1.0x)
- **safety_first**: Prioritize safer routes (risk weight = 1.4x)

#### 3. **Optional Travel Documents**

Users can optionally indicate visas/residencies they hold:
- **Visas**: US, UK, SCHENGEN, CA, AU, JP, KR, etc.
- **Residencies**: US_GC, CA_PR, UK_BRP, EU_PR, etc.

This influences risk scoring and ranking, but always with transparent reasons and verification steps.

## 📦 Installation & Setup

### Prerequisites

- **Python 3.11+**
- **Node.js 18+** and npm
- **uv** (Python package manager) — install via `pip install uv` or see https://github.com/astral-sh/uv
- **Amadeus API credentials** (free test account at https://developers.amadeus.com/)

### Step 1: Clone and Navigate

```bash
cd cheap-flights
```

### Step 2: Backend Setup

```bash
cd backend

# Install dependencies using uv
uv sync

# Create .env file from example
cp .env.example .env

# Edit .env and add your Amadeus credentials
# nano .env
# Set:
#   AMADEUS_CLIENT_ID=your_actual_client_id
#   AMADEUS_CLIENT_SECRET=your_actual_client_secret
#   AMADEUS_ENV=test
```

#### Optional: Enable AI-Powered Visa Research

By default, the app uses TravelBriefing API for visa information. When that fails, it shows a generic fallback message. You can **optionally** enable AI-powered visa research as a smart fallback:

**How it works:**
1. When TravelBriefing fails, the app performs a web search for visa requirements
2. Claude AI (Haiku model) summarizes the findings into concise, helpful guidance
3. Results are marked with 🤖 icon and strong disclaimers

**To enable:**

1. Get an Anthropic API key from https://console.anthropic.com/
2. Add to your `.env` file:
   ```bash
   ENABLE_AI_VISA_RESEARCH=true
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   ```

**Important caveats:**
- ⚠️ AI-generated visa information is **NOT authoritative**
- Results must be verified with official embassy/consulate sources
- This uses Claude Haiku (fast, cheap model) so costs are minimal
- The app shows prominent disclaimers when displaying AI research
- If you don't enable this, the app still works fine with standard fallback messages

**When to use it:**
- You want more helpful context when TravelBriefing is down
- You understand the AI results need verification
- You're okay with small API costs (~$0.001 per search with AI fallback)

**When NOT to use it:**
- You don't want to rely on AI for any visa information
- You prefer only showing information from established APIs
- You want to avoid any Anthropic API costs

### Step 3: Frontend Setup

```bash
cd ../frontend

# Install dependencies
npm install

# Build the frontend
npm run build
```

This creates `frontend/dist/` with the production build.

### Step 4: Run the Application

```bash
cd ../backend

# Run FastAPI server (serves both API and frontend)
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Or using Python directly:**

```bash
uv run python -m app.main
```

The application will be available at **http://localhost:8000**

- **Frontend UI:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/api/health

## 🐳 Docker Deployment (Production-Ready)

For production deployment with PostgreSQL and Redis, use Docker:

### Prerequisites

- **Docker** and **Docker Compose** installed
- **Amadeus API credentials**

### Step 1: Create Environment File

```bash
# Copy the Docker environment template
cp .env.docker.example .env

# Edit .env and add your credentials
nano .env
```

**⚠️ SECURITY WARNING**: Never commit `.env` file to git! It contains sensitive credentials.

Required environment variables in `.env`:

```bash
# PostgreSQL Database (CHANGE THESE IN PRODUCTION!)
POSTGRES_DB=geoflight
POSTGRES_USER=geoflight
POSTGRES_PASSWORD=your_secure_password_here  # ← Change this!

# Redis
REDIS_URL=redis://redis:6379/0

# Amadeus API (required)
AMADEUS_CLIENT_ID=your_actual_client_id
AMADEUS_CLIENT_SECRET=your_actual_client_secret
AMADEUS_ENV=test  # or 'prod'

# Optional: AI Visa Research
ENABLE_AI_VISA_RESEARCH=false
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

The `.env` file is already in `.gitignore` to prevent accidental commits.

### Step 2: Build and Run

```bash
# Build and start all services (app + PostgreSQL + Redis)
docker-compose up --build

# Or run in detached mode
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop services
docker-compose down

# Stop and remove volumes (clears database)
docker-compose down -v
```

### What Gets Deployed

The Docker setup includes 4 separate containers:

- **Frontend**: React app served by nginx (port 80)
- **Backend**: FastAPI REST API (port 8000)
- **PostgreSQL 15**: Production database for search history
- **Redis 7**: Distributed cache for multi-worker deployments

### Architecture

```
                ┌──────────────────┐
                │   Frontend       │
                │   (nginx:80)     │
                │   React SPA      │
                └────────┬─────────┘
                         │
                         │ /api/* proxied
                         │
                ┌────────▼─────────┐
                │   Backend        │
                │   (FastAPI:8000) │
                │   Python API     │
                └────┬──────┬──────┘
                     │      │
         ┌───────────┘      └───────────┐
         │                               │
    ┌────▼──────┐              ┌────────▼─────┐
    │  Redis    │              │  PostgreSQL  │
    │  (6379)   │              │    (5432)    │
    │  Cache    │              │  Database    │
    └───────────┘              └──────────────┘
```

### Access Points

- **Application UI**: http://localhost (port 80)
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost/docs (proxied through nginx)
- **PostgreSQL**: localhost:5432 (user: `geoflight`, db: `geoflight`)
- **Redis**: localhost:6379

### Database Management

```bash
# Connect to PostgreSQL inside container
docker-compose exec postgres psql -U geoflight -d geoflight

# Check database size
SELECT pg_size_pretty(pg_database_size('geoflight'));

# List all searches
SELECT id, created_at FROM searches ORDER BY created_at DESC LIMIT 10;

# Connect to Redis
docker-compose exec redis redis-cli

# Check cache size
DBSIZE

# Clear cache
FLUSHDB
```

### Production Deployment Notes

**🔒 Security Checklist:**

1. **Change database credentials** in `.env`:
   ```bash
   POSTGRES_PASSWORD=use_a_strong_random_password_here
   ```
   Generate secure passwords: `openssl rand -base64 32`

2. **Never commit `.env` file** to version control (already in `.gitignore`)

3. **Set up SSL/TLS** with Caddy/Traefik or configure nginx with Let's Encrypt

4. **Use production Amadeus credentials**:
   ```bash
   AMADEUS_ENV=prod
   AMADEUS_CLIENT_ID=your_production_client_id
   AMADEUS_CLIENT_SECRET=your_production_client_secret
   ```

5. **Enable monitoring** (add Prometheus + Grafana containers)

6. **Configure backups** for PostgreSQL volumes:
   ```bash
   docker-compose exec postgres pg_dump -U geoflight geoflight > backup.sql
   ```

7. **Restrict network access**: Configure firewall rules, don't expose PostgreSQL/Redis ports publicly

8. **Load balancing**: For multiple backend replicas, add nginx/haproxy load balancer

### Scaling for High Traffic

Scale the backend horizontally (Redis ensures cache is shared across instances):

```bash
# Scale backend to 4 replicas
docker-compose up -d --scale backend=4

# Note: You'll need a load balancer in front (nginx-proxy, Traefik, etc.)
```

Or use Docker Swarm/Kubernetes for production orchestration:

```yaml
# docker-compose.yml with Swarm deploy config:
services:
  backend:
    deploy:
      replicas: 4
      update_config:
        parallelism: 2
        delay: 10s
      restart_policy:
        condition: on-failure
```

## 🧪 Running Tests

```bash
cd backend

# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=app --cov-report=html

# Run specific test file
uv run pytest tests/test_risk_engine.py -v
```

## 🔌 API Usage

### POST /api/search

**Search for flights with risk assessment and ranking.**

```bash
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "origin": "DEL",
    "destination": "SFO",
    "date": "2026-03-15",
    "adults": 1,
    "cabin": "ECONOMY",
    "max_stops": 2,
    "passport_nationality": "IN",
    "safety_mode": "balanced",
    "travel_docs": {
      "visas": ["US"],
      "residencies": [],
      "notes": "US B1/B2 valid until 2028"
    }
  }'
```

**Sample Response (truncated):**

```json
{
  "search_id": "a1b2c3d4e5f6g7h8",
  "query": {
    "origin": "DEL",
    "destination": "SFO",
    "date": "2026-03-15",
    "adults": 1,
    "cabin": "ECONOMY",
    "max_stops": 2,
    "passport_nationality": "IN",
    "safety_mode": "balanced",
    "travel_docs": {
      "visas": ["US"],
      "residencies": [],
      "notes": "US B1/B2 valid until 2028"
    }
  },
  "results": [
    {
      "id": "offer123",
      "provider": "amadeus",
      "price": {
        "total": 1234.56,
        "currency": "USD"
      },
      "total_duration_minutes": 1230,
      "stops": 1,
      "segments": [
        {
          "carrier": "AI",
          "flight_number": "AI173",
          "from": "DEL",
          "to": "SFO",
          "depart_at": "2026-03-15T10:05:00",
          "arrive_at": "2026-03-15T14:25:00",
          "duration_minutes": 1230
        }
      ],
      "layovers": [],
      "transit_countries": [],
      "risk": {
        "level": "LOW",
        "reasons": [
          "No major risk factors identified"
        ],
        "verify_steps": [
          "Confirm this is a single ticket (not self-transfer)",
          "Confirm baggage is checked through to final destination",
          "Verify you can remain airside during all connections"
        ],
        "transit_countries": [],
        "layover_airports": []
      },
      "visa_baseline": {
        "destination_entry_summary": "...",
        "source": "travelbriefing",
        "disclaimer": "Best-effort information from TravelBriefing..."
      },
      "score": 0.42
    }
  ],
  "meta": {
    "provider": "amadeus",
    "cached": false,
    "generated_at": "2026-01-01T12:34:56.789Z"
  }
}
```

### GET /api/search/{search_id}

Retrieve previously executed search.

```bash
curl http://localhost:8000/api/search/a1b2c3d4e5f6g7h8
```

### GET /api/health

Health check endpoint.

```bash
curl http://localhost:8000/api/health
```

## 🎨 Frontend Usage

Open http://localhost:8000 in your browser.

**Search Form Fields:**
- Origin & Destination (IATA codes, e.g., DEL, SFO)
- Date (one-way for MVP)
- Adults (1-9)
- Cabin (Economy, Premium Economy, Business, First)
- Max Stops (0, 1, or 2)
- Passport Nationality (default IN)
- **Safety Mode**: price_first | balanced | safety_first
- **Optional Travel Docs** (collapsible):
  - Visas (US, UK, SCHENGEN, etc.)
  - Residencies (US_GC, UK_BRP, EU_PR, etc.)
  - Notes (free text)

**Results Display:**
- Top 20 itineraries ranked by score (price + safety)
- Each card shows:
  - Price, duration, stops
  - Flight segments with times
  - Layovers with duration
  - Transit countries
  - **Risk badge** (LOW/MEDIUM/HIGH)
  - **Risk reasons** (specific)
  - **Verification steps** (actionable checklist)
  - Destination visa baseline (if available)
  - "Copy JSON" button

## 📂 Project Structure

```
cheap-flights/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app + static file serving
│   │   ├── settings.py             # Environment config
│   │   ├── models.py               # Pydantic models
│   │   ├── db.py                   # SQLite + caching
│   │   ├── api/
│   │   │   └── routes.py           # API endpoints
│   │   └── services/
│   │       ├── amadeus.py          # Amadeus API client
│   │       ├── travelbriefing.py   # TravelBriefing client
│   │       ├── normalizer.py       # Response normalization
│   │       ├── risk_engine.py      # Transit risk assessment (IN-first)
│   │       └── scoring.py          # Ranking & scoring
│   ├── tests/
│   │   ├── test_risk_engine.py
│   │   └── test_scoring.py
│   ├── pyproject.toml              # uv dependencies
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── api/
│   │   │   ├── client.ts           # API client
│   │   │   └── types.ts            # TypeScript types
│   │   └── components/
│   │       ├── SearchForm.tsx      # Search UI with travel docs
│   │       ├── ResultsList.tsx     # Results container
│   │       ├── ItineraryCard.tsx   # Individual itinerary card
│   │       └── RiskBadge.tsx       # Risk level badge
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── tsconfig.json
├── .gitignore
└── README.md
```

## 🛠️ Development Mode

For development with hot-reload:

### Terminal 1 (Backend):
```bash
cd backend
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Terminal 2 (Frontend):
```bash
cd frontend
npm run dev
```

Frontend dev server runs at http://localhost:5173 with API proxy to backend.

## 🧩 Customizing Transit Policy Lists

The transit safety heuristics are **easily editable** in:

**File:** `backend/app/services/risk_engine.py`

```python
# Edit these sets to match your preferences:

PREFERRED_TRANSIT_COUNTRIES = {
    "SG", "AE", "QA", "OM", "BH", "SA",
    "TR", "MY", "TH", "HK", "JP", "KR"
}

CAUTION_TRANSIT_COUNTRIES = {
    "US", "CA", "AU"
}

SCHENGEN_COUNTRIES = {
    "AT", "BE", "CZ", "DK", "EE", "FI", "FR", "DE", ...
}

# Adjust thresholds:
MIN_SAFE_CONNECTION_INTERNATIONAL = 75  # minutes
LONG_LAYOVER_THRESHOLD = 8 * 60  # hours
```

**After editing, restart the backend.**

## 📊 Caching

**Adaptive caching** (automatic selection based on configuration):
- Searches are cached by query hash (origin, destination, date, passport, safety mode, travel docs)
- Default TTL: 30 minutes (configurable via `APP_CACHE_TTL_SECONDS` in `.env`)
- Implementation in `app/cache.py`:
  - **With Redis** (`REDIS_URL` set): Uses RedisCache (distributed, multi-worker safe)
  - **Without Redis**: Uses SimpleCache (in-memory dict, single-worker only)

**Cache hit behavior:**
- Cache stores search_id → fetch full results from database
- Avoids duplicate Amadeus API calls within 30 minutes

**Redis usage:**
```bash
# Local development with Redis
REDIS_URL=redis://localhost:6379/0

# Docker (automatically configured in docker-compose.yml)
REDIS_URL=redis://redis:6379/0
```

## 🗄️ Database

**Supported databases:**
- **SQLite** (default for local development)
- **PostgreSQL** (recommended for production/Docker)

**Database tables:**
- `searches` — search requests and metadata
- `itineraries` — normalized itineraries with risk scores
- `provider_payloads` — raw API responses (optional for debugging)

**Configuration:**
```bash
# SQLite (local development)
DATABASE_URL=sqlite+aiosqlite:///./geoflight.db

# PostgreSQL (Docker/production)
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/dbname
```

**Location (SQLite):** `backend/geoflight.db` (auto-created on first run)

**Note:** Caching is separate from persistence. The database stores search history, while cache (Redis or in-memory) handles 30-min deduplication.

## 🔒 Security & Privacy

- **No user accounts** (search-only MVP)
- **No PII stored** beyond search queries (origin, destination, dates)
- **Travel docs are optional** and only used for risk scoring (not persisted long-term)
- **Secrets:** Keep `AMADEUS_CLIENT_SECRET` in `.env`, never commit to git

## 🚀 Deployment Notes

For production deployment:

1. Build frontend: `cd frontend && npm run build`
2. Set `AMADEUS_ENV=prod` in backend `.env` (and use production Amadeus credentials)
3. Run backend with production ASGI server: `uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4`
4. **IMPORTANT:** For multi-worker deployments, replace in-memory cache with Redis (see `app/cache.py`)
5. Optionally use a reverse proxy (nginx) in front
6. Use a production DB (PostgreSQL) instead of SQLite for scale (update `app/settings.py`)

## 🐛 Known Limitations & Assumptions

1. **Airport-to-country mapping** is a small hardcoded dict in `normalizer.py`. In production, use a proper airport database.

2. **Airport change detection** is a rough heuristic (first 2 letters of IATA code). Not always accurate.

3. **TravelBriefing API** may be rate-limited or unavailable. App degrades gracefully to "unknown" with disclaimers.

4. **No self-transfer detection** from Amadeus response (would need booking class analysis). App assumes single ticket unless heuristics detect issues.

5. **Schengen ATV rules** are complex and vary by nationality/itinerary. App flags for verification but doesn't claim certainty.

6. **Overnight airside rules** vary by airport. App flags overnight layovers but user must verify if airside stay is allowed.

7. **One-way flights only** for MVP. Round-trip stub exists but not implemented.

8. **No flexible dates implementation** (flex_days parameter exists but not used).

## 📚 References & Resources

- **Amadeus for Developers:** https://developers.amadeus.com/
- **TravelBriefing API:** https://travelbriefing.org/api/
- **Visa/transit verification sources (examples):**
  - IATA Timatic (paid): https://www.iata.org/timatic
  - Sherpa° (paid): https://apply.joinsherpa.com/
  - Official embassy/consulate websites
  - Government travel advisories (e.g., Indian MEA, US State Dept)

## 🤝 Contributing

This is an educational MVP. To contribute:

1. Fork the repo
2. Make changes
3. Add tests for new functionality
4. Run `uv run pytest` and `uv run black .`
5. Submit a pull request

## 📄 License

This project is for educational and research purposes. Use at your own risk. No warranty provided.

## ✨ Acknowledgments

- Built with ❤️ for Indian travelers
- Transit safety heuristics based on community knowledge
- Thanks to Amadeus for free test API access

---

**Remember:** GeoFlight Scout is a tool to help you find and analyze flights. It is NOT a substitute for official visa/entry requirement verification. Always verify with authoritative sources before booking international travel.

**Happy (and safe) travels! ✈️**
