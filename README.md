# Deliverables

## Final MVP Scope

Core flow of the AI automation:

```text
Customer Enquiry
       ↓
FastAPI
       ↓
HMAC Verification
       ↓
Store Enquiry
       ↓
Background AI Processing
       ↓
AI Classification / Extraction
       ↓
Create Lead
       ↓
Schedule Follow-Up
       ↓
Next.js Dashboard
```

## Core Features

- **Public enquiry submission** — Gives customers a form where they can submit their name, email, company, and message. That enquiry enters LeadFlow.

- **Webhook ingestion** — Allows another system to send enquiry data directly to LeadFlow through an API endpoint such as `POST /api/webhooks/enquiries`.

- **HMAC verification** — Checks that a webhook request genuinely came from a trusted sender and was not modified or forged.

- **PostgreSQL persistence** — Permanently stores enquiries, leads, AI results, users, webhook events, and follow-up jobs in the database.

- **AI processing** — Analyzes the enquiry and determines things like category, priority, intent, summary, and a suggested response.

- **Lead creation** — Converts a processed enquiry into a lead that the sales/admin team can manage.

- **Follow-up jobs** — Schedules work that should happen later, such as reminding the team to follow up with a high-priority lead.

- **Admin authentication** — Requires admins to log in before they can access lead information or dashboard functionality.

- **Lead dashboard** — Gives admins a UI where they can view leads, priorities, statuses, AI summaries, suggested replies, and follow-up information.

---

# Technology Stack

## Frontend

* Next.js
* TypeScript
* Tailwind CSS

## Backend

* FastAPI
* Python

## Database

* PostgreSQL

## ORM

* SQLAlchemy 2.x

## Migrations

* Alembic

## Validation

* Pydantic

## AI

* OpenAI API

## Background Jobs

* ARQ + Redis

## Authentication

* JWT

## Testing

* pytest
* pytest-asyncio
* httpx

## Infrastructure

* Docker
* Docker Compose

---

# System Architecture

## Database Schema Design

```text
users
enquiries
leads
ai_processing_results
webhook_events
follow_up_jobs
```

## High-Level Relationships + Entity Relationships

```text
enquiries
    │
    ├──── ai_processing_results
    │
    └──── leads
             │
             └──── follow_up_jobs

webhook_events
    │
    └──── enquiry

users
    │
    └──── manage dashboard/leads
```

---

# API Endpoint Plan

```text
/api/enquiries
/api/webhooks
/api/auth
/api/leads
/api/dashboard
/api/users
```

Important endpoints later include:

```http
POST /api/enquiries
POST /api/webhooks/enquiries
POST /api/auth/login
GET /api/auth/me
GET /api/leads
GET /api/leads/{id}
PATCH /api/leads/{id}
GET /api/dashboard/metrics
```

---

# Enquiry Lifecycle

An enquiry will move through:

```text
received
   ↓
pending_processing
   ↓
processing
   ↓
processed
```

## Failure Path

```text
processing
   ↓
failed
```

Once processing succeeds:

```text
Enquiry
   ↓
AI Result
   ↓
Lead
   ↓
Follow-Up Job
```

## Lead Lifecycle

```text
new
 ↓
contacted
 ↓
qualified
 ↓
closed
```

---

# `.env.example` Specification

```env
APP_ENV=
DATABASE_URL=
REDIS_URL=
JWT_SECRET_KEY=
WEBHOOK_SECRET=
OPENAI_API_KEY=
FRONTEND_URL=
```

---

# Folder Structure

## Frontend Architecture

```text
frontend/
├── app/
├── components/
├── features/
├── lib/
├── services/
├── types/
├── hooks/
└── public/
```

## Backend Architecture

```text
backend/
├── app/
│   ├── api/
│   ├── core/
│   ├── db/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   ├── repositories/
│   ├── workers/
│   └── main.py
│
├── migrations/
├── tests/
├── alembic.ini
├── requirements.txt
└── Dockerfile
```
