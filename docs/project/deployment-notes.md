# Deployment Notes — Railway

Practical notes on deploying the Feedback Triage App to Railway cheaply.

---

## Filesystem Persistence Warning

Container filesystems are ephemeral. If your app used:

- `app.db`
- `uploads/`
- `generated_reports/`

inside the app container, those could disappear on redeploy.

For this app:

- **Bad:** SQLite file stored inside the app container
- **Bad:** user uploads stored inside the app container
- **Good:** managed Postgres database
- **Good:** external object storage for files, if uploads are added later

Use Postgres for persistent feedback data. Do not use local SQLite for the
deployed version.

---

## Railway Cost Model

Railway charges for resource usage (CPU, memory, storage, egress), not just
traffic. On Hobby, the $5 subscription counts toward usage; if you exceed $5
in resources, you pay the difference.

When a service is running, it consumes CPU and RAM regardless of whether
traffic is hitting it.

**Cost-saving goal:** keep the app small, idle, and sleeping when not used.

---

## Cheap Configuration Recommendations

### 1. One backend service

Avoid splitting into separate API, frontend, worker, and scheduler services.
Use one FastAPI app that serves both API endpoints and the simple HTML/CSS/JS
frontend.

```text
1 Railway project
├── FastAPI web service
└── Railway Postgres
```

### 2. Use Railway Postgres, not SQLite in the container

Use environment variables like:

```env
DATABASE_URL=...
```

Do not use `sqlite:///./app.db` in production.

### 3. Enable Serverless / App Sleeping

Railway's Serverless feature sleeps inactive services. Tradeoff: first
request after sleep has a cold-start delay. Fine for portfolio/demo apps.

**Caution:** outbound traffic can prevent sleep (database connections,
telemetry, NTP). Avoid background loops, scheduled polling, or constant
outbound calls.

### 4. Set a hard usage limit immediately

For a learning/portfolio app:

- alert at ~$3–$4
- hard limit at ~$5–$7

A mistake should not become an expensive bill.

### 5. Set low resource limits

For a tiny FastAPI CRUD app:

- 1 replica only
- low memory limit
- low CPU limit

Do not horizontally scale.

### 6. Use one Uvicorn worker

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

More workers usually means more memory.

### 7. Avoid expensive background logic

Skip scrapers, scheduled jobs, AI summarization, polling, analytics,
long-running workers, browser automation, file processing.

### 8. Keep the database small

- paginate `GET /feedback`
- add indexes only if useful
- do not store huge text blobs
- do not store files in Postgres
- seed only a small amount of demo data

Default: `GET /feedback?skip=0&limit=20`

### 9. Serve static assets simply

Let FastAPI serve CSS/JS for now. If the app grows, move static assets to
Cloudflare Pages later.

---

## Cheapest Sane Setup

```text
Railway Hobby
├── FastAPI app
│   ├── serves frontend pages
│   ├── serves API routes
│   └── serverless/app sleeping enabled
└── Railway Postgres
```

Configure:

- hard usage limit
- one replica
- low CPU/memory limits
- no extra workers
- no cron jobs
- no AI/background tasks
- Postgres for persistence
- no local file storage

---

## Should You Worry About "Running Logic" Costs?

For this app, not much. A CRUD triage app is computationally cheap:

```text
receive form → validate → insert row → show updated list
```

The bigger cost risk is not the logic. It is:

- app sitting awake 24/7
- database sitting awake 24/7
- too much memory usage
- multiple services
- background processes
- no hard spending limit

---

## Best Recommendation

- build locally first
- use Postgres locally through Docker
- deploy to Railway only when you want a public demo
- enable Serverless / App Sleeping
- set a hard usage limit
- keep everything in one FastAPI service plus Postgres
