# ContentForge AI — Frontend Dashboard (Part 3)

The Next.js 14 (App Router) + React + TypeScript + Tailwind CSS frontend dashboard for **ContentForge AI**, connecting to the Part 1 & Part 2 backend services.

---

## Features & Screens Built

1. **Login / Signup (`/login`)**:
   - Authenticates against `POST /auth/login` and `POST /auth/register`.
   - Stores JWT token in `localStorage`, attaches Bearer token to all requests, and handles auto-redirect on session expiry.
2. **Dashboard (`/dashboard`)**:
   - Welcome banner, quick metric cards, and prominent "New Transformation" CTA.
   - Recent generation jobs list with status badges and direct navigation to results.
3. **Source Input (`/new-transformation/upload`)**:
   - Drag-and-drop file uploader for PDF/DOCX (up to 20MB) and raw text paste area.
   - Calls `POST /documents/upload` and polls `GET /documents/{id}` until `processed_status = "processed"`.
4. **Content Preview (`/new-transformation/preview`)**:
   - Fetches `GET /documents/{id}/facts` and displays summary, detected entities (people, orgs, locations, systems), taxonomy topics, and the immutable Fact Registry.
   - Source snippet inspection before proceeding to output generation.
5. **Output Selection & Generation Settings (`/new-transformation/output-selection`)**:
   - Interactive selection cards for all 7 output formats (LinkedIn, Twitter, Advisory, Executive Summary, Presentation, Infographic, Video Package).
   - Form controls for Audience, Tone, Detail Level, and Objective.
   - "Generate" button calling `POST /generate` with automatic validation guard.
6. **Generation Progress (`/new-transformation/generating`)**:
   - Real-time polling of `GET /generation/{job_id}` every 2 seconds.
   - Per-channel pipeline status and auto-redirect to Results upon completion.
7. **Results & Output Preview (`/results/[jobId]`)**:
   - Tabbed interface rendering all 7 format-specific components:
     - `LinkedInCard`: Hook, narrative body, hashtags, and CTA with feed styling.
     - `TweetThreadCard`: Connected numbered tweet bubbles with character counts.
     - `AdvisoryCard`: Formatted severity badge, impacted scope, technical details, and numbered remediation steps.
     - `ExecutiveSummaryCard`: C-suite briefing layout with core synthesis and strategic takeaways.
     - `InfographicCard`: Campaign headline, layout/colour theme suggestions, and modular statistics.
     - `SlideDeckCard`: 16:9 presentation viewer with slide navigation, presenter speaker notes, and visual cues.
     - `VideoScriptCard`: Scene-by-scene storyboard with narration, visual directions, subtitles, and runtime estimates.
   - Confidence score badge (`e.g. 94% source-grounded`) on every card.
   - Automatic visual highlighting of unverified claims (orange wavy underline and explanation tooltip).
8. **Interactive Traceability (`TraceabilityPanel`)**:
   - Clicking any sentence or claim opens the drawer displaying exact linked Fact Registry statements and original source document snippets.
9. **Inline Editing**:
   - Direct field editing on every card, saved via `PUT /outputs/{id}` (with graceful local storage cache fallback).
10. **Export & Actions**:
    - "Copy to Clipboard" with one-click full formatting.
    - PDF/DOCX export button with "Coming in Part 4" status.
    - Visible disabled "Send for Review" button (Part 4 Reviewer Workflow placeholder).
11. **Transformation History (`/history`)**:
    - Searchable by document title/job ID, filterable by output format, and sortable by date.
12. **Operator Settings (`/settings`)**:
    - Profile details, active JWT session status, backend API target indicator, and logout.

---

## Local Development & Setup

### 1. Prerequisites
- Node.js 18+ (tested on Node v20/v26)
- npm 9+

### 2. Installation
```bash
cd frontend
npm install
```

### 3. Environment Variables
Create a `.env.local` file in the `frontend/` directory (or set the environment variable in your shell):

```bash
# Target Backend API URL (FastAPI)
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 4. Running the Dev Server
```bash
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser.

### 5. Running the Automated Test Suite
The frontend includes a Jest + React Testing Library test suite:

```bash
npm test
```
All 5 test suites (13 unit and integration tests) verify login validation, output selection button state, all 7 output cards, claim traceability, and unverified claim styling.

---

## Modular Architecture: Adding an 8th Output Format
The results viewer is built with a pluggable registry pattern (`components/output-cards/index.ts`):
1. Create a new card component in `components/output-cards/NewFormatCard.tsx`.
2. Register it in `OUTPUT_TYPE_REGISTRY` in `components/output-cards/index.ts`.
3. The Results screen, Output Selection screen, History filter, and clipboard copy will automatically support the new format without restructuring existing screens.
