# API Overview

Base URL: `http://localhost:8000/api`
Interactive docs: `http://localhost:8000/api/docs`

## Health

| Method | Path | Description |
|---|---|---|
| GET | /health | Liveness check |

## Visitors

| Method | Path | Description |
|---|---|---|
| POST | /visitors | Create / update visitor memory |
| GET | /visitors/{visitor_id} | Get visitor memory |
| PATCH | /visitors/{visitor_id}/preferences | Partial update preferences |
| DELETE | /visitors/{visitor_id}/memory | Clear all stored memory |

## Visit Planning

| Method | Path | Description |
|---|---|---|
| POST | /visits/plan | Run full 5-agent planning workflow |
| GET | /visits/{visit_id} | Get a visit guide |
| GET | /visits/{visit_id}/trace | Get agent workflow trace |
| POST | /visits/{visit_id}/complete-stop | Mark a stop visited |
| POST | /visits/{visit_id}/feedback | Submit liked/disliked feedback |
| POST | /visits/{visit_id}/replan | Crowd-aware replan |
| GET | /visits/{visit_id}/sources | Get RAG evidence sources |

## Galleries & Crowd

| Method | Path | Description |
|---|---|---|
| GET | /galleries | List galleries with current crowd state |
| GET | /galleries/crowd | Crowd state for all galleries |
| PATCH | /galleries/{gallery_id}/crowd | Update crowd state |

## Exhibits

| Method | Path | Description |
|---|---|---|
| GET | /exhibits | Paginated exhibit list |
| GET | /exhibits/{exhibit_id} | Single exhibit |

## Evaluation

| Method | Path | Description |
|---|---|---|
| POST | /evaluation/run | Run evaluation for all 8 profiles |
| GET | /evaluation/latest | Most recent evaluation report |
| GET | /evaluation/profiles | List seeded visitor profiles |

## Admin

| Method | Path | Description |
|---|---|---|
| POST | /admin/reindex | Re-ingest catalogue into ChromaDB |

## Response Format

All responses use standard HTTP status codes.
Errors return `{"detail": "message"}`.
Successful planning returns a full `VisitGuide` JSON object.
