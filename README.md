# Uphill AI 🏔️ — Science-Backed Trail & Mountain Coaching

Uphill AI is a premium, AI-powered adaptive training platform for trail, mountain, and ultra-runners. The system leverages generative artificial intelligence and grounded athletic literature to design personalized training blocks, analyze route profiles, calculate physiological thresholds, and deliver real-time feedback.

---

## 🚀 Core Features

*   **Adaptive Training Scheduler**: Generates periodized blocks based on race date, distance, elevation gain, and terrain. Supports manual route profile input or **GPX route parsing** to automatically extract elevation splits and calculate grade-adjusted pacing targets.
*   **Grounded AI Coach**: Chat interface with a running coach assistant. Responses are grounded in elite coaching manuals, sweat/hydration case studies, and user physiological data.
*   **Knowledge Hub (RAG)**: Ingest reference materials (PDFs, URLs, or YouTube transcripts) into the knowledge base. Features automatic **NotebookLM integration** that synchronizes structured grounding cards in both **English and Vietnamese**.
*   **Physiology Calculators**: Quy đổi treadmill speed/grade to flat-equivalent efforts, calculate Zone 2 heart rate floors, and predict Split Times for trail checkpoints.
*   **Athlete Physiology Profile**: Stores threshold heart rates (Aerobic Threshold - AeT, Anaerobic Threshold - AnT) and pace constraints, allowing for precise training zone customization.

---

## 🧠 Coaching Philosophy

The system's intelligence adheres to established scientific methodologies of elite endurance athletics:

1.  **Aerobic Base Building & Zone 2**: Following the principles of **Scott Johnston** (*Training for the Uphill Athlete*), we emphasize that 80-90% of annual training volume must remain easy (strictly below the Aerobic Threshold). This builds mitochondrial density, capillary networks, and a "lactate vacuum cleaner" in slow-twitch muscle fibers.
2.  **The 80/20 Intensity Rule**: For road and flat speedwork, we follow Stephen Seiler's intensity distribution (80% easy, 20% moderate-to-high intensity).
3.  **Muscular Endurance (ME)**: Mountain performance is determined by local muscle fatigue resistance. The scheduler structures specific ME routines (e.g. weighted step-ups, hill sprints, and carries) to adapt fast-twitch fibers for vertical load.
4.  **Precision Fueling**: Scaled nutrition planning based on sweat rate, target finish time, and elite case studies (targeting optimal carb/sodium/fluid ratios per hour).

---

## ⚡ Why Coach Uphill is Better

*   **Zero Hallucinations**: Traditional LLMs often suggest generic, dangerous, or unscientific running programs. Coach Uphill strictly grounds its advice in trusted, ingested coaching resources.
*   **Dynamic i18n Synchronization**: Toggle the entire UI (and the RAG knowledge cards) between English and Vietnamese seamlessly.
*   **Privacy & Bring Your Own Key (BYOK)**: Store your private Gemini API key locally on the server or in your profile to run advanced RAG extractions for free.
*   **Offline Fallback Mode**: Fully functional offline mock mode in case the API keys are not supplied.

---

## 🛠️ Tech Stack

### Frontend
*   **Framework**: Next.js 16 (App Router)
*   **Logic & Typing**: React 19, TypeScript 5
*   **Styling**: Custom HSL-tailored CSS, Tailwind CSS
*   **Deployment**: Static HTML Export (`output: "export"`) served via `serve` inside a lightweight Node.js Docker container.

### Backend
*   **API Framework**: FastAPI, Uvicorn
*   **Database Access**: SQLAlchemy Core (parameterized queries for SQL injection prevention)
*   **Database**: PostgreSQL / SQLite (for development)

### AI & Telemetry
*   **LLM Model**: Gemini 2.5 Flash (`gemini-2.5-flash`)
*   **RAG Engine**: NotebookLM API and local SQLite vector search
*   **Telemetry Parsing**: `gpxpy` (for GPX files) and `fitparse` (for Garmin FIT files)

---

## 📚 References & Resources

*   **Core Manual**: *[Training for the Uphill Athlete](https://www.uphillathlete.com/)* by Steve House, Scott Johnston, and Kílian Jornet.
*   **Aerobic Testing**: *[Heart Rate Drift Test Protocol](https://uphillathlete.com/aerobic-training/heart-rate-drift-test/)*.
*   **Intensity Guidelines**: *[80/20 Running]* by Matt Fitzgerald.
*   **Hydration Studies**: *[Precision Hydration Elite Case Studies](https://www.precisionhydration.com/)*.

---

## 🐳 Quickstart: Docker Compose

Bring up the complete local stack (Database, FastAPI Backend, Next.js Static Frontend) using Docker Compose:

```bash
docker compose up -d --build
```
*   **Frontend Access**: [http://localhost:3000](http://localhost:3000)
*   **Backend API**: [http://localhost:8000/docs](http://localhost:8000/docs)
