# Uphill AI 🏔️ — Science-Backed Trail, Mountain & Ultra Coaching Platform

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-16.2-black.svg?style=flat&logo=next.js&logoColor=white)](https://nextjs.org)
[![Capacitor](https://img.shields.io/badge/Capacitor-8.5-119EFF.svg?style=flat&logo=capacitor&logoColor=white)](https://capacitorjs.com)
[![Google Gemini](https://img.shields.io/badge/Gemini_2.5_Flash-8E75B2.svg?style=flat&logo=google&logoColor=white)](https://ai.google.dev/)
[![Qdrant](https://img.shields.io/badge/Qdrant-Vector_DB-DC2626.svg?style=flat&logo=qdrant&logoColor=white)](https://qdrant.tech/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791.svg?style=flat&logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![Apache Airflow](https://img.shields.io/badge/Apache_Airflow-2.9-017CEE.svg?style=flat&logo=apacheairflow&logoColor=white)](https://airflow.apache.org)
[![Apache Spark](https://img.shields.io/badge/Apache_Spark-3.5-E25A1C.svg?style=flat&logo=apachespark&logoColor=white)](https://spark.apache.org)
[![DuckDB](https://img.shields.io/badge/DuckDB-dbt_Core-FFF000.svg?style=flat&logo=duckdb&logoColor=black)](https://duckdb.org)
[![Prometheus & Grafana](https://img.shields.io/badge/Observability-Prometheus_%26_Grafana-F46800.svg?style=flat&logo=grafana&logoColor=white)](https://grafana.com)
[![Bilingual](https://img.shields.io/badge/i18n-English_%7C_Ti%E1%BA%BFng_Vi%E1%BB%87t-blue.svg?style=flat)](#-bilingual--localization)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **"Train Smarter. Climb Stronger. Peak with Confidence."**  
> Uphill AI is an end-to-end, science-grounded adaptive training and race-readiness platform purpose-built for **trail, mountain, skyrunning, and ultramarathon athletes**.

---

## 📖 Table of Contents

- [Introduction](#-introduction)
  - [The Problem with Mountain Athletics](#the-problem-with-mountain-athletics)
  - [The Scientific Core & Philosophy](#the-scientific-core--philosophy)
- [Core Features](#-core-features)
  - [1. Plan Scheduler & Periodization Engine](#1-plan-scheduler--periodization-engine)
  - [2. Coach Uphill (Grounded AI Assistant)](#2-coach-uphill-grounded-ai-assistant)
  - [3. Goal Determiner & Rank Transfer](#3-goal-determiner--rank-transfer)
  - [4. Pace Strategy (Minetti Grade & Weather Engine)](#4-pace-strategy-minetti-grade--weather-engine)
  - [5. Gear Finder (Catalog-Grounded Vault)](#5-gear-finder-catalog-grounded-vault)
  - [6. Nutrition Lab (Hour-by-Hour Fueling)](#6-nutrition-lab-hour-by-hour-fueling)
  - [7. Knowledge Hub & Multimodal RAG Ingestion](#7-knowledge-hub--multimodal-rag-ingestion)
  - [8. Data Platform, Warehousing & Analytics](#8-data-platform-warehousing--analytics)
- [Uphill AI vs. The Landscape](#-uphill-ai-vs-the-landscape)
  - [Feature & Science Comparison Matrix](#feature--science-comparison-matrix)
  - [Why Traditional Running Apps (e.g., Runna) Fall Short in the Mountains](#why-traditional-running-apps-eg-runna-fall-short-in-the-mountains)
  - [Why Generic AI Chatbots (ChatGPT, Claude, Gemini) Are Dangerous for Ultra Training](#why-generic-ai-chatbots-chatgpt-claude-gemini-are-dangerous-for-ultra-training)
  - [The Uphill AI Solution: Deterministic Physics + Grounded Intelligence](#the-uphill-ai-solution-deterministic-physics--grounded-intelligence)
- [Architecture & Tech Stack](#-architecture--tech-stack)
  - [System Architecture Diagram](#system-architecture-diagram)
  - [Technology Breakdown](#technology-breakdown)
- [References & Scientific Resources](#-references--scientific-resources)
- [Quickstart & Deployment](#-quickstart--deployment)
  - [Docker Compose (Complete Stack)](#docker-compose-complete-stack)
  - [Manual Development Setup](#manual-development-setup)
  - [Mobile App Setup (Capacitor)](#mobile-app-setup-capacitor)
  - [Testing & Quality Assurance](#testing--quality-assurance)

---

## 🏔️ Introduction

### The Problem with Mountain Athletics

Mountain running and ultramarathons are fundamentally different from road racing:
1. **Vertical Ascent Metabolic Load**: Climbing requires exponential metabolic work modeled by non-linear biomechanics, not flat pace splits.
2. **Eccentric Downhill Damage**: Steep descents inflict severe structural damage on quadriceps and connective tissues. Without targeted **Muscular Endurance (ME)**, legs fail hours before the cardiovascular engine does.
3. **Severe Hypoxia & Environmental Extremes**: High altitude ($>1,500\text{m}$), temperature swings ($>15^\circ\text{C}$ heat penalties), and humidity drastically impair glycogen absorption and heart rate drift.
4. **Nutrition & Hydration Failure**: The #1 cause of DNF (*Did Not Finish*) in ultra-endurance is gastrointestinal distress. Fueling requires personalized sodium ($500\text{--}1,000\text{mg/hr}$) and carb ($60\text{--}90\text{g/hr}$) strategies matched to sweat rate and gut training.

Mainstream running platforms treat running as a 2D flat sport. Generic AI chatbots hallucinate unsafe mileage ramps and make up nutritional claims. **Uphill AI bridges this divide.**

```
                           UPHILL AI SYSTEM
 ┌──────────────────────────────────────────────────────────────────────────┐
 │                                                                          │
 │   🏃 INDIVIDUAL PHYSIOLOGY       ⛰️ RACE TOPOGRAPHY & METEOROLOGY        │
 │   • Aerobic Threshold (AeT)      • GPX / Course Elevation Profiles       │
 │   • Anaerobic Threshold (AnT)    • Minetti Metabolic Energy Model        │
 │   • HR Drift & Aerobic Base      • Live Weather & Altitude Degradation   │
 │                                                                          │
 └──────────────────────────────────┬───────────────────────────────────────┘
                                    │
                                    ▼
 ┌──────────────────────────────────────────────────────────────────────────┐
 │   🧠 GROUNDED AI & DETERMINISTIC ENGINES                                 │
 │   • 80/20 Intensity Polarizer     • Muscular Endurance (ME) Protocols    │
 │   • Gemini 2.5 Flash + Qdrant RAG • DUV Ultramarathon Rank Transfer      │
 │   • 100% Curated Gear Catalog     • Dynamic Nutrition & Sodium Synthesis │
 └──────────────────────────────────┬───────────────────────────────────────┘
                                    │
                                    ▼
 ┌──────────────────────────────────────────────────────────────────────────┐
 │   📱 SEAMLESS MULTI-PLATFORM EXPERIENCE                                  │
 │   • Next.js 16 Web App           • iOS & Android (Capacitor)             │
 │   • Offline-First Execution      • English & Tiếng Việt (Bilingual)      │
 └──────────────────────────────────────────────────────────────────────────┘
```

### The Scientific Core & Philosophy

Uphill AI codifies the training methodologies of elite coaches and world-record endurance athletes:

- **Aerobic Base Building (Zone 1–2 / Below AeT)**: Based on **Scott Johnston, Steve House, and Kilian Jornet** (*Training for the Uphill Athlete*). Up to 80–90% of training stays strictly below the Aerobic Threshold (AeT) to maximize mitochondrial density, capillary vascularization, and lipid oxidation capacity while preventing *Aerobic Deficiency Syndrome (ADS)*.
- **Strict 80/20 Intensity Polarization**: Implements **Dr. Stephen Seiler's** polarization model to eliminate wasteful Zone 3 "black hole" training.
- **Muscular Endurance (ME) Conditioning**: Tailored sport-specific strength protocols (weighted step-ups, steep uphill bounds, eccentric load prep) that condition fast-twitch fibers to resist fatigue during thousands of meters of vertical gain and loss.
- **Minetti Grade-Adjusted Energetics**: Calculates energy expenditure using the landmark **Minetti et al. (2002)** metabolic cost equations, with downhill energy dissipation damping and steep gradient hiking-economy thresholds.
- **Precision Fueling & Gut Training**: Grounded in **Dr. Asker Jeukendrup's** sports nutrition frameworks, scaling exogenous carbohydrate oxidation ($60\text{--}90\text{g/hr}$) and sweat sodium replacement ($500\text{--}1,000\text{mg/hr}$) under real race conditions.

---

## 🚀 Core Features

### 1. Plan Scheduler & Periodization Engine
*Your training plan, built on the manual written by the sport's greatest.*

- **5-Zone Physiological Threshold Model**: Zones anchored directly to your **Aerobic Threshold (AeT)** and **Anaerobic Threshold (AnT)**—never inaccurate generic $220 - \text{age}$ formulas.
- **Automated 80/20 Volume Audit**: Weekly schedules are algorithmically audited to guarantee $\ge 80\%$ easy volume (Zone 1–2) and flag high-intensity overreach.
- **Dedicated Muscular Endurance (ME) Blocks**: Progresses from base aerobic volume into uphill sprints, weighted box step-ups, and downhill durability blocks.
- **Deterministic Treadmill Speed & Incline Derivation**: Converts any outdoor trail workout into an exact, mathematically equivalent treadmill speed/grade pair using grade-adjusted metabolic equations.
- **Adaptive Injury & Fatigue Swapping**: Seamlessly swaps strained muscle groups for low-impact cross-training or active recovery sessions.

### 2. Coach Uphill (Grounded AI Assistant)
*Ask anything. Receive advice grounded in peer-reviewed sports science.*

- **Gemini 2.5 Flash + Qdrant Vector Retrieval**: Chat assistant operating under strict retrieval-augmented generation (RAG) constraints.
- **Zero-Hallucination Refusal Policy**: If an inquiry falls outside verified physiological literature or curated catalogs, Coach Uphill explicitly declares its bounds rather than fabricating dangerous advice.
- **Live Athlete Context Awareness**: Seamlessly inspects your active training calendar, recent workload, target race profile, and threshold history.
- **Native Bilingual Fluency**: Instant switching between **English** and **Vietnamese (Tiếng Việt)** across all coaching advice and knowledge cards.

### 3. Goal Determiner & Rank Transfer
*Turn current baseline fitness or past races into realistic race-day targets.*

- **Terrain-Inverted Flat Pace Extraction**: Takes your past race finish time on any mountainous course and inverts the course physics (ITRA-style) to calculate your true flat-ground base fitness.
- **Asymmetric A/B/C Race Goals**:
  - **A (Ambitious)**: $+5\%$ stretch target assuming optimal weather, nutrition, and pacing execution.
  - **B (Realistic)**: Base target aligned with projected physiological adaptation.
  - **C (Safe / Contingency)**: $-8\%$ conservative safety margin accounting for mountain hazards, GI issues, or harsh weather.
- **Time-to-Race Adaptation Progression**: Models realistic fitness gains ($+0.25\%/\text{week}$, capped at $5\%$) over structured multi-week training blocks.
- **DUV & UltraSignup Rank Transfer**: Validates targets against historical finisher percentiles from global ultramarathon databases.

### 4. Pace Strategy (Minetti Grade & Weather Engine)
*Checkpoint-by-checkpoint race execution modeling.*

- **Minetti (2002) Grade Cost Multiplier**: Evaluates the metabolic cost of ascent and descent, applying downhill damping (energy absorption) and steep climbing caps.
- **Altitude Hypoxia Degradation**: Applies progressive pace penalties above $1,500\text{m}$ elevation ($\approx 1.5\%$ per $100\text{m}$ ascent).
- **Durability & Neuromuscular Decay**: Models non-linear pace degradation after $15\text{km}$ of cumulative flat-equivalent fatigue.
- **Live Meteorology Synchronization**: Fetches live race-day temperature, humidity, and precipitation data to penalize heat loads above $15^\circ\text{C}$.
- **Split Bias Optimization**: Balances even effort vs. negative split distribution while strictly preserving total target time.

### 5. Gear Finder (Catalog-Grounded Vault)
*Shoe recommendations from a verified, curated database—never AI hallucinations.*

- **100% Full-Catalog Grounding**: Injects verified specifications (stack height, drop, carbon plate, lug depth, weight, outsole compound) across top brands (*Hoka, Salomon, Nike, adidas, Asics, Altra, Norda, Saucony, Brooks, On, etc.*).
- **Terrain & Profile Matching**: Recommends footwear matched to rockiness, mud depth, race distance, runner weight, and foot strike.
- **Hallucination Validator**: Automatically rejects models or specifications not present in the verified master catalog.

### 6. Nutrition Lab (Hour-by-Hour Fueling)
*Precision sports dietitian strategies mapped to real nutrition products.*

- **Target-Driven Dynamic Math**: Formulates hourly carbohydrate ($60\text{--}90\text{g/hr}$) and sodium ($500\text{--}1,000\text{mg/hr}$) requirements based on race duration, heat index, and sweat rate.
- **Verified Product Composition**: Maps targets to real products (Maurten, Precision Fuel & Hydration, Tailwind, GU, SIS, whole foods) with exact macro/electrolyte counts.
- **Gut-Training Protocol**: Structures training-phase nutrition loading to build gut tolerance before race day.

### 7. Knowledge Hub & Multimodal RAG Ingestion
*Continuously evolving coaching wisdom curated from primary sources.*

- **Dual-Source Ingestion Engine**:
  1. **NotebookLM Deep Sweeps**: Structured extraction across 8 core endurance topics.
  2. **Autonomous Podcast Pipeline**: Crawls new *Evoke Endurance ("Evokecast")* episodes, downloads YouTube transcripts, and synthesizes bilingual knowledge cards.
- **Curated Race Course Database**: Ingests route profiles, key climbs, terrain nuances, climate warnings, and DUV result statistics.

### 8. Data Platform, Warehousing & Analytics
*Production-grade data engineering and observability built for scale.*

- **Event Streaming**: Apache Kafka capturing workout logs and telemetry streams.
- **Batch Processing**: Apache Spark 3.5 & Delta Lake pipelines for user dimension and training load aggregations.
- **Modern Data Warehouse**: DuckDB + dbt Core modeling dimensional layers (`dim_user`, `fct_workouts`, `fct_plan_generation`).
- **Workflow Orchestration**: Apache Airflow DAGs orchestrating weekly KB distillation, race results enrichment, and ELT schedules.
- **Analytics & Observability**: Metabase BI dashboards for business metrics alongside Prometheus and Grafana for backend latency and telemetry monitoring.

---

## ⚡ Uphill AI vs. The Landscape

### Feature & Science Comparison Matrix

| Feature / Dimension | Uphill AI 🏔️ | Traditional Apps (Runna, Nike, Garmin Coach) | General LLMs (ChatGPT-4o, Claude 3.7, Gemini) |
| :--- | :--- | :--- | :--- |
| **Primary Domain Focus** | **Trail, Mountain, Skyrunning, Ultras** | Road 5K to Marathon | General text generation |
| **Scientific Training Foundation** | **House, Johnston & Jornet (*Uphill Athlete*) + Seiler 80/20** | Generic road templates & linear progression | Mixed internet training blogs (unverified) |
| **Heart Rate Threshold Model** | **Individualized AeT & AnT (HR Drift Test)** | Generic $220 - \text{age}$ formulas or static pace bands | Vague generic heart rate percentages |
| **Elevation & Terrain Physics** | **Minetti (2002) Curve + GPX Segment Splits** | ❌ None (assumes flat road running) | ❌ Cannot parse physics or GPX splits |
| **Downhill & Muscular Endurance (ME)**| **✅ Dedicated ME circuits (weighted step-ups, hill bounds)**| ❌ Generic core/gym templates | ⚠️ Generic bodyweight suggestions |
| **Race Checkpoint Pacing** | **Altitude + Grade + Fatigue Decay + Live Weather** | Flat splits / Simple pace targets | Basic arithmetic division (often buggy) |
| **Goal Prediction Engine** | **ITRA Terrain Inversion + DUV Rank Transfer** | VDOT / Riegel formula (flat road only) | Hallucinated finish times |
| **Gear Recommendation Accuracy** | **100% Grounded in Curated Shoe Catalog** | Static affiliate articles / Non-adaptive | ⚠️ High hallucination (invents fake models/specs) |
| **Nutrition & Fueling Blueprint** | **Grounded in Real Products (Carb/Na+ hourly plan)** | Basic tips (e.g., "drink water, take a gel") | ⚠️ Rough generic estimates (no catalog check) |
| **Hallucination Safeguards** | **Dual RAG + Hardcoded Scientific Guardrails** | N/A (Rules-based) | ❌ Frequent hallucinations & unsafe mileage jumps |
| **Data Platform & Observability** | **Airflow + Spark + DuckDB/dbt + Kafka + Grafana** | Proprietary closed stack | Closed proprietary API |
| **Privacy & Self-Hosting** | **BYOK (Gemini API Key) + Dockerized Self-Host** | Closed subscription garden | Cloud-only subscription |
| **Bilingual Localization** | **Native English & Tiếng Việt (Bilingual RAG & UI)** | English-only (or generic machine translation) | Multilingual text (no contextual grounding) |

---

### Why Traditional Running Apps (e.g., Runna) Fall Short in the Mountains

```
 Traditional Road Apps (e.g. Runna)              Uphill AI Mountain Physics
 ┌─────────────────────────────────┐            ┌─────────────────────────────────┐
 │ • Linear weekly mileage ramp    │            │ • Vertical Gain + Distance load │
 │ • Flat-ground pacing formulas   │    VS.     │ • Minetti Grade Metabolic Curve │
 │ • Ignorant of eccentric fatigue │            │ • Muscular Endurance (ME) blocks│
 │ • No high-altitude adjustment   │            │ • Altitude + Weather degradation│
 └─────────────────────────────────┘            └─────────────────────────────────┘
```

1. **Failure of Flat-Pace Calculations**: Traditional running apps structure workouts by target pace per kilometer (e.g., "Run $5\text{km}$ at 4:30/km"). In mountain terrain with $15\text{--}30\%$ grades, pace is meaningless—metabolic cost, heart rate, and hiking transition thresholds dictate output.
2. **The Zone 3 "Black Hole" Trap**: Without individualized Aerobic Threshold (AeT) calibration, apps push runners into moderate-intensity Zone 3. Over weeks, this triggers *Aerobic Deficiency Syndrome (ADS)*, chronic sympathetic fatigue, and plateaued fat-burning efficiency.
3. **No Eccentric Load Preparation**: Road training relies almost entirely on concentric muscle action. When road-trained runners encounter a $-1,500\text{m}$ mountain descent, eccentric muscle contraction destroys unconditioned muscle fibers, resulting in severe quadriceps lockup and DNFs. Uphill AI’s Muscular Endurance routines directly eliminate this vulnerability.

---

### Why Generic AI Chatbots (ChatGPT, Claude, Gemini) Are Dangerous for Ultra Training

```
 Generic Unconstrained LLM                        Uphill AI Grounded Agent
 ┌─────────────────────────────────┐            ┌─────────────────────────────────┐
 │ Prompt: "Plan a 100k ultra"     │            │ Prompt: "Plan a 100k ultra"     │
 │ ⚠️ Hallucinates 25% weekly jumps│    VS.     │ ✅ Audits AeT/AnT & weekly vol  │
 │ ⚠️ Invents non-existent shoes   │            │ ✅ Enforces 80/20 volume bounds │
 │ ⚠️ Guesses nutrition math       │            │ ✅ Verifies products in catalog │
 │ ⚠️ Ignores course topography    │            │ ✅ Runs Minetti physics on GPX  │
 └─────────────────────────────────┘            └─────────────────────────────────┘
```

1. **Hallucinated Progression Curves**: Unconstrained LLMs lack deterministic validation. They routinely recommend $20\text{--}30\%$ weekly volume jumps, violating the safe ceiling ($10\%$ max) and inviting patellofemoral syndrome, IT band friction, or bone stress injuries.
2. **Mathematical Incompetence in Split Calculations**: LLMs struggle with multi-variable physics. Prompting a generic LLM for split times on a course with $4,000\text{m}$ elevation gain produces mathematically impossible splits that ignore metabolic cost decay and heat degradation.
3. **Fake Gear and Nutritional Invented Specs**: General LLMs frequently hallucinate shoe models, misstate heel-to-toe drop numbers, or recommend dangerous sodium intake values ($>2,500\text{mg/hr}$).
4. **Lack of State & Telemetry Awareness**: Generic chatbots do not connect to your actual training calendar, cannot parse Garmin `.fit` files or `.gpx` routes, and cannot adapt in real time to missed workouts.

---

### The Uphill AI Solution: Deterministic Physics + Grounded Intelligence

Uphill AI uses a **hybrid architecture**:
- **Deterministic Python Physics & Mathematical Engines**: Plan volume audits, Minetti metabolic curves, treadmill incline conversions, and A/B/C goal bounds run through rigorously tested, deterministic algorithms.
- **RAG-Grounded Generative AI**: Gemini 2.5 Flash acts as an empathetic, multilingual synthesizer that communicates exclusively through verified knowledge chunks and structured product catalogs.

---

## 🛠️ Architecture & Tech Stack

### System Architecture Diagram

![Uphill AI System Architecture](assets/architecture/uphill_ai_architecture.png)

*Interactive Excalidraw source file available at [`assets/architecture/uphill_ai_architecture.excalidraw`](assets/architecture/uphill_ai_architecture.excalidraw).*

<details>
<summary><b>Click to view textual Mermaid source</b></summary>

```mermaid
flowchart TB
    subgraph CLIENT["Client Layer (Web & Mobile)"]
        WEB["Next.js 16 (React 19, TS5)\nTailwind CSS + HSL Tokens"]
        MOB["Capacitor 8.5\n(iOS & Android Native Shell)"]
    end

    subgraph API_GATEWAY["API & Orchestration Layer"]
        FASTAPI["FastAPI Backend (Python 3.11+)\nSQLAlchemy Core (Async Raw SQL)"]
        AUTH["JWT Session Store / OAuth2\n(Google & Facebook Auth)"]
    end

    subgraph ENGINES["Deterministic & Physiological Engines"]
        MINETTI["Minetti Metabolic Physics Engine\n(Grade, Altitude, Heat, Decay)"]
        PLAN_GEN["Plan Generator & 80/20 Auditor"]
        GOAL_ENG["Goal Determiner & Rank Transfer\n(ITRA Inversion, DUV Stats)"]
        PARSERS["Telemetry Parsers\n(fitparse, gpxpy)"]
    end

    subgraph AI_RAG["AI & Vector Knowledge Layer"]
        GEMINI["Google Gemini 2.5 Flash\n(Structured LLM Engine)"]
        QDRANT["Qdrant Vector DB\n(uphill_kb_scheduler)"]
        NOTEBOOKLM["NotebookLM API\n(Offline Topic Distiller)"]
        TAVILY["Tavily Web Search\n(Live Gear/Nutrition Crawler)"]
    end

    subgraph DATA_PLATFORM["Enterprise Data Platform"]
        KAFKA["Apache Kafka 3.7\n(Event Stream)"]
        SPARK["Apache Spark 3.5\n(Delta Lake Aggregations)"]
        AIRFLOW["Apache Airflow 2.9\n(DAG Orchestration)"]
        DUCKDB["DuckDB + dbt Core\n(Data Warehouse)"]
    end

    subgraph STORAGE["Storage & Observability"]
        PG["PostgreSQL 16\n(Primary OLTP Database)"]
        PROM["Prometheus + Node Exporter\n(Metrics Collection)"]
        GRAFANA["Grafana OSS\n(System Dashboards)"]
        METABASE["Metabase BI\n(Analytics & Reporting)"]
    end

    CLIENT --> FASTAPI
    FASTAPI --> AUTH
    FASTAPI --> ENGINES
    FASTAPI --> AI_RAG
    FASTAPI --> PG
    FASTAPI --> KAFKA
    
    ENGINES --> PARSERS
    AI_RAG --> QDRANT
    AI_RAG --> GEMINI

    KAFKA --> SPARK
    SPARK --> DUCKDB
    AIRFLOW --> DUCKDB
    AIRFLOW --> QDRANT
    AIRFLOW --> FASTAPI

    PG --> METABASE
    DUCKDB --> METABASE
    FASTAPI --> PROM
    PROM --> GRAFANA
```
</details>

### Technology Breakdown

#### Frontend & Mobile Client
- **Web Framework**: Next.js 16 (App Router) with static HTML export (`output: "export"`).
- **Core Library**: React 19, TypeScript 5.
- **Mobile Runtime**: Capacitor 8.5 (`@capacitor/ios`, `@capacitor/android`, `@capacitor/haptics`, `@capacitor/local-notifications`).
- **Styling**: Tailwind CSS v4 + custom HSL design tokens for rich light/dark themes.
- **State Management**: Centralized React `AppContext` with offline persistence.

#### Backend & Core Engines
- **Web Framework**: FastAPI, Uvicorn (ASGI).
- **Database Access**: SQLAlchemy Core with parameterized SQL queries (high performance, SQL-injection safe, zero heavy ORM overhead).
- **Database Migrations**: Alembic + idempotent `init_db()` startup self-migration.
- **Telemetry Parsers**: `gpxpy` for GPX elevation splits, `fitparse` for Garmin `.fit` activity streams.
- **Physics Models**: Minetti metabolic cost equations, altitude exponential degradation curve, durability decay multiplier, weather heat index penalty.

#### AI, Vector Search & RAG
- **LLM**: Google Gemini 2.5 Flash (`gemini-2.5-flash`).
- **Vector Database**: Qdrant (`gemini-embedding-2` embeddings, collection `uphill_kb_scheduler`).
- **Web Discovery & Crawling**: Tavily Search API for continuous shoe catalog and nutrition catalog updates.
- **Podcast Processing**: `youtube-transcript-api` + Tavily crawler for *Evoke Endurance* podcast transcript synthesis.

#### Data Platform & Observability
- **Event Streaming**: Apache Kafka 3.7 (Docker Kraft cluster).
- **Batch Processing**: Apache Spark 3.5 with Delta Lake.
- **Data Warehousing**: DuckDB + dbt Core for ELT transformations.
- **Workflow Orchestration**: Apache Airflow 2.9 (LocalExecutor, automated weekly distillation DAGs).
- **Metrics & Telemetry**: Prometheus auto-instrumented via `prometheus-fastapi-instrumentator`, Node Exporter, Grafana OSS.
- **Business Intelligence**: Metabase BI running on custom glibc Debian image with DuckDB native driver.

---

## 📚 References & Scientific Resources

The algorithms and coaching guardrails in Uphill AI are directly sourced from the following literature:

1. **House, S., Johnston, S., & Jornet, K. (2019)**. *Training for the Uphill Athlete: A Manual for Mountain Runners and Ski Mountaineers*. Patagonia Books.  
   *(Core methodology for aerobic base building, AeT/AnT threshold modeling, and Muscular Endurance protocols).*
2. **Minetti, A. E., Moia, C., Roi, G. S., Susta, D., & Ferretti, G. (2002)**. *Energy cost of walking and running at extreme uphill and downhill gradients*. Journal of Applied Physiology, 93(3), 1039-1046.  
   *(Metabolic cost polynomial curve used in Pace Strategy).*
3. **Seiler, S. (2010)**. *What is best practice for training characteristics and physiological progressions in endurance athletes?* International Journal of Sports Physiology and Performance.  
   *(The 80/20 polarized intensity distribution framework).*
4. **Jeukendrup, A. (2014)**. *A step towards personalized sports nutrition: carbohydrate intake during exercise*. Sports Medicine, 44(Suppl 1), 25-33.  
   *(Exogenous carbohydrate oxidation limits and gut-training protocols).*
5. **San-Millán, I., & Brooks, G. A. (2018)**. *Assessment of Metabolic Flexibility and Skeletal Muscle Mitochondrial Capacity in Endurance Athletes*. Sports Medicine, 48(2), 467-479.  
   *(Physiological rationale for Zone 2 aerobic base conditioning).*
6. **DUV Ultramarathon Statistics** & **ITRA (International Trail Running Association)**.  
   *(Historical finisher statistics, percentile benchmarking, and course difficulty index normalization).*

---

## 🐳 Quickstart & Deployment

### Docker Compose (Complete Stack)

Start the entire platform (PostgreSQL, FastAPI Backend, Next.js Frontend, Qdrant, Kafka, Spark, Airflow, Prometheus, Grafana, Metabase) with one command:

```bash
# Clone the repository
git clone https://github.com/kylianvo/uphill-ai.git
cd uphill-ai

# Launch all services
docker compose up -d --build
```

#### Service URLs

| Service | URL | Default Credentials |
| :--- | :--- | :--- |
| **Frontend Web App** | [http://localhost:8080](http://localhost:8080) | — |
| **Backend API Docs** | [http://localhost:8000/docs](http://localhost:8000/docs) | — |
| **Grafana Dashboards**| [http://localhost:3000](http://localhost:3000) | `admin` / `changeme` |
| **Metabase BI** | [http://localhost:3001](http://localhost:3001) | Setup on first launch |
| **Airflow Webserver** | [http://localhost:8081](http://localhost:8081) | `admin` / `admin` |
| **Spark Master UI** | [http://localhost:8090](http://localhost:8090) | — |
| **Qdrant Vector DB** | [http://localhost:6333/dashboard](http://localhost:6333/dashboard) | — |

---

### Manual Development Setup

#### 1. Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env

# Run database migrations & seed knowledge base
alembic upgrade head
python scripts/load_kb.py

# Start backend server
uvicorn main:app --reload --port 8000
```

#### 2. Frontend Setup

```bash
cd frontend
npm install

# Start local Next.js dev server
npm run dev
# App available at http://localhost:3000
```

---

### Mobile App Setup (Capacitor)

Uphill AI runs natively on iOS and Android via Capacitor:

```bash
cd frontend

# Build static bundle and sync to native projects
npm run cap:sync

# Open in Xcode (iOS)
npm run cap:open:ios

# Open in Android Studio (Android)
npm run cap:open:android
```

---

### Testing & Quality Assurance

```bash
# Run backend test suite (470+ unit & integration tests)
cd backend
pytest tests/ -v -m "not kafka"

# Run frontend unit tests
cd frontend
npm run test

# Run Playwright End-to-End & Visual Regression tests
npm run test:e2e
```

---

## 🌐 Bilingual & Localization

Uphill AI features first-class internationalization for English and Vietnamese:
- **UI & Navigation**: Instant toggle across all views.
- **RAG Knowledge Hub**: Structured grounding cards distilled bilingually.
- **AI Coach & Plan Output**: Workouts, coach notes, and pace descriptions generated natively in the athlete's chosen language.

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
