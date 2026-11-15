# Shared Visitor-Preference Memory

## Purpose

Every agent in the system can read visitor preferences from a central memory store. This allows, for example, the Route Planner Agent to know a visitor requires wheelchair access without being told explicitly by the orchestrator, and the Commentary Writer Agent to tailor language to the visitor's preferred commentary length.

## Storage

**Persistent mode:** MongoDB collection `visitor_memory`. Keyed by `visitor_id`.

**Guest mode / no-DB fallback:** Python dict `_GUEST_STORE` in `memory/visitor_memory.py`. Survives the current process only.

## Schema (VisitorMemory)

| Field | Type | Description |
|---|---|---|
| visitor_id | str | Unique identifier |
| display_name | str | Human-readable name |
| interests | list[InterestCategory] | Explicit interest categories |
| interest_weights | dict[str, float] | Relative importance per interest |
| preferred_language | Language | en/es/fr/de/hi |
| preferred_commentary_length | CommentaryLength | short/medium/long |
| accessibility_needs | list[AccessibilityNeed] | wheelchair, step_free, etc. |
| memory_mode | MemoryMode | persistent / guest |
| previously_visited_exhibits | list[str] | Exhibit IDs visited in past sessions |
| previously_skipped_exhibits | list[dict] | {exhibit_id, reason} pairs |
| explicit_feedback | dict[str, dict] | {exhibit_id: {liked: bool, comment: str}} |
| updated_at | datetime | Last modification timestamp |
| memory_version | int | Incremented on each update |

## Read / Write Rules

- **Visitor Profile Agent**: writes on every session (creates or updates)
- **Route Planner Agent**: reads accessibility_needs and interest_weights
- **Commentary Writer Agent**: reads preferred_language and preferred_commentary_length
- **Guide Manager Agent**: reads interests for coverage computation
- **All agents**: access via `VisitorMemoryService` dependency injection

Agents write **only** when they have a justified update. Explicit preferences are never silently overwritten by inferred preferences.

## How Memory Improves Personalisation

On a returning visit, the Visitor Profile Agent:
1. Reads existing memory
2. Boosts interest weights for topics the visitor has previously engaged with
3. Skips exhibits the visitor has already seen (from `previously_visited_exhibits`)
4. Avoids topics the visitor explicitly disliked (from `explicit_feedback`)

This means a returning visitor gets a meaningfully different, progressively personalised route without re-entering their preferences.

## Guest Mode

If `memory_mode=guest`, preferences are stored in the in-process dict only. The visitor is not identified across sessions. No personal data is written to MongoDB.
