import json
import base64
import os
import sys
from pathlib import Path

# Load Official Brand Vector SVGs directly from assets/logos/official/
LOGOS_DIR = Path("/Users/vietvo/Documents/antigravity/uphill-ai/assets/logos/official")

def load_logos():
    logos = {}
    for f in LOGOS_DIR.glob("*.svg"):
        logos[f.stem] = f.read_text(encoding="utf-8")
    return logos

def create_excalidraw_diagram():
    logos_dict = load_logos()
    elements = []
    files_dict = {}
    seed_counter = 60000

    def next_seed():
        nonlocal seed_counter
        seed_counter += 1
        return seed_counter

    for logo_key, svg_str in logos_dict.items():
        b64 = base64.b64encode(svg_str.encode("utf-8")).decode("utf-8")
        file_id = f"file_{logo_key}"
        files_dict[file_id] = {
            "mimeType": "image/svg+xml",
            "id": file_id,
            "dataURL": f"data:image/svg+xml;base64,{b64}"
        }

    def add_logo(logo_key, x, y, size=24):
        file_id = f"file_{logo_key}"
        el = {
            "type": "image",
            "id": f"logo_{logo_key}_{next_seed()}",
            "fileId": file_id,
            "x": x,
            "y": y,
            "width": size,
            "height": size,
            "strokeColor": "transparent",
            "backgroundColor": "transparent",
            "fillStyle": "solid",
            "strokeWidth": 1,
            "strokeStyle": "solid",
            "roughness": 0,
            "opacity": 100,
            "angle": 0,
            "seed": next_seed(),
            "version": 1,
            "versionNonce": next_seed(),
            "isDeleted": False,
            "groupIds": [],
            "boundElements": None,
            "link": None,
            "locked": False,
            "status": "saved",
            "scale": [1, 1]
        }
        elements.append(el)
        return el

    def add_rect(id_name, x, y, w, h, bg, stroke, stroke_width=2, stroke_style="solid", opacity=100, roundness=3, fill_style="solid"):
        el = {
            "type": "rectangle",
            "id": id_name,
            "x": x,
            "y": y,
            "width": w,
            "height": h,
            "strokeColor": stroke,
            "backgroundColor": bg,
            "fillStyle": fill_style,
            "strokeWidth": stroke_width,
            "strokeStyle": stroke_style,
            "roughness": 0,
            "opacity": opacity,
            "angle": 0,
            "seed": next_seed(),
            "version": 1,
            "versionNonce": next_seed(),
            "isDeleted": False,
            "groupIds": [],
            "boundElements": [],
            "link": None,
            "locked": False,
            "roundness": {"type": roundness} if roundness else None
        }
        elements.append(el)
        return el

    def add_text(id_name, x, y, text, font_size=16, color="#0f172a", align="left", container_id=None, width=None, height=None, bold=False):
        lines = text.split("\n")
        line_count = len(lines)
        approx_height = int(line_count * font_size * 1.3)
        max_len = max(len(l) for l in lines) if lines else 1
        approx_width = width if width is not None else int(max_len * font_size * 0.6)

        el = {
            "type": "text",
            "id": id_name,
            "x": x,
            "y": y,
            "width": approx_width,
            "height": approx_height if height is None else height,
            "text": text,
            "originalText": text,
            "fontSize": font_size,
            "fontFamily": 3, # Monospace
            "textAlign": align,
            "verticalAlign": "middle" if container_id else "top",
            "strokeColor": color,
            "backgroundColor": "transparent",
            "fillStyle": "solid",
            "strokeWidth": 1,
            "strokeStyle": "solid",
            "roughness": 0,
            "opacity": 100,
            "angle": 0,
            "seed": next_seed(),
            "version": 1,
            "versionNonce": next_seed(),
            "isDeleted": False,
            "groupIds": [],
            "boundElements": None,
            "link": None,
            "locked": False,
            "containerId": container_id,
            "lineHeight": 1.25
        }
        elements.append(el)
        return el

    def add_arrow(id_name, start_id, end_id, points, stroke="#475569", stroke_width=2, stroke_style="solid", start_arrow=None, end_arrow="arrow"):
        start_el = next((e for e in elements if e["id"] == start_id), None)
        end_el = next((e for e in elements if e["id"] == end_id), None)

        el = {
            "type": "arrow",
            "id": id_name,
            "x": points[0][0],
            "y": points[0][1],
            "width": points[-1][0] - points[0][0],
            "height": points[-1][1] - points[0][1],
            "strokeColor": stroke,
            "backgroundColor": "transparent",
            "fillStyle": "solid",
            "strokeWidth": stroke_width,
            "strokeStyle": stroke_style,
            "roughness": 0,
            "opacity": 100,
            "angle": 0,
            "seed": next_seed(),
            "version": 1,
            "versionNonce": next_seed(),
            "isDeleted": False,
            "groupIds": [],
            "boundElements": None,
            "link": None,
            "locked": False,
            "points": [[p[0] - points[0][0], p[1] - points[0][1]] for p in points],
            "startBinding": {"elementId": start_id, "focus": 0, "gap": 4} if start_id else None,
            "endBinding": {"elementId": end_id, "focus": 0, "gap": 4} if end_id else None,
            "startArrowhead": start_arrow,
            "endArrowhead": end_arrow
        }
        elements.append(el)

        if start_el:
            if start_el.get("boundElements") is None:
                start_el["boundElements"] = []
            start_el["boundElements"].append({"id": id_name, "type": "arrow"})
        if end_el:
            if end_el.get("boundElements") is None:
                end_el["boundElements"] = []
            end_el["boundElements"].append({"id": id_name, "type": "arrow"})
        return el

    # ==========================================
    # 0. HEADER & TITLE (y = 30 .. 80)
    # ==========================================
    add_text("title_main", 50, 30, "UPHILL AI 🏔️ — SYSTEM ARCHITECTURE & DATA FLOW", font_size=24, color="#0f172a")
    add_text("title_sub", 50, 60, "Multi-Platform Endurance Coaching • Deterministic Physics Engines • Grounded Gemini RAG • Enterprise Data Platform", font_size=13, color="#2563eb")

    # ==========================================
    # 1. CLIENT LAYER (Column 1: x = 50 .. 420)
    # ==========================================
    add_rect("room_client", 50, 140, 370, 720, bg="#fff7ed", stroke="#fdba74", stroke_width=1, stroke_style="dashed", opacity=70, roundness=3)
    add_text("room_client_title", 65, 152, "CLIENT LAYER (CROSS-PLATFORM)", font_size=14, color="#c2410c")
    add_text("room_client_desc", 65, 172, "Static Export Web + Native Mobile Shell", font_size=11, color="#7c2d12")

    # Web App Component
    add_rect("card_web", 65, 195, 340, 155, bg="#ffedd5", stroke="#ea580c", stroke_width=2)
    add_logo("nextjs", 80, 205, 24)
    add_logo("react", 112, 205, 24)
    add_logo("tailwind", 144, 205, 24)
    add_logo("typescript", 176, 205, 24)
    add_text("card_web_title", 210, 208, "Next.js 16 Web App", font_size=14, color="#9a3412")
    add_text("card_web_body", 80, 240, "• React 19 App Router (Static HTML Export)\n• Tailwind CSS v4 + Custom HSL Design Tokens\n• AppContext Unified State • i18n (EN/VI)\n• BYOK (Bring Your Own Key) Gemini Storage", font_size=11, color="#431407")

    # Mobile App Component
    add_rect("card_mobile", 65, 365, 340, 155, bg="#ffedd5", stroke="#ea580c", stroke_width=2)
    add_logo("capacitor", 80, 375, 24)
    add_text("card_mobile_title", 115, 378, "Capacitor 8.5 Mobile Shell", font_size=14, color="#9a3412")
    add_text("card_mobile_body", 80, 410, "• Native iOS & Android Runtime Shells\n• Native Haptics & Local Notifications API\n• Offline-First Cache & Safe Area Navigation\n• Real-Time Workout & Calendar Synchronization", font_size=11, color="#431407")

    # Athlete Profile Card
    add_rect("card_profile_state", 65, 535, 340, 140, bg="#fed7aa", stroke="#ea580c", stroke_width=2)
    add_text("card_profile_title", 80, 545, "👤 Athlete Physiology Profile State", font_size=13, color="#9a3412")
    add_text("card_profile_body", 80, 570, "• Aerobic Threshold (AeT) & Anaerobic (AnT) HR\n• Flat Base Pace Normalization (min/km)\n• Goal Race Profile (Distance, Elevation, Terrain)\n• Active Injury History & Training Availability", font_size=11, color="#431407")

    # Telemetry Input formats
    add_rect("card_telemetry_input", 65, 690, 340, 145, bg="#fef08a", stroke="#ca8a04", stroke_width=2)
    add_text("card_telemetry_title", 80, 700, "📂 Multimodal Telemetry Uploads", font_size=13, color="#854d0e")
    add_text("card_telemetry_body", 80, 725, "• GPX Route Files (Elevation, Grade, Splits)\n• Garmin .FIT Files (Heart Rate, Power, Cadence)\n• Real-Time Weather Forecast Feeds (Heat/Rain)\n• DUV Ultramarathon Historical Result Databases", font_size=11, color="#713f12")


    # ==========================================
    # 2. BACKEND API & GATEWAY (Column 2: x = 470 .. 840)
    # ==========================================
    add_rect("room_backend", 470, 140, 370, 720, bg="#f0fdf4", stroke="#86efac", stroke_width=1, stroke_style="dashed", opacity=70, roundness=3)
    add_text("room_backend_title", 485, 152, "API GATEWAY & SECURITY", font_size=14, color="#15803d")
    add_text("room_backend_desc", 485, 172, "FastAPI High-Performance Async Core", font_size=11, color="#166534")

    # FastAPI Main App
    add_rect("card_fastapi", 485, 195, 340, 125, bg="#dcfce7", stroke="#16a34a", stroke_width=2)
    add_logo("fastapi", 500, 205, 24)
    add_logo("python", 532, 205, 24)
    add_text("card_fastapi_title", 568, 208, "FastAPI Gateway (main.py)", font_size=14, color="#14532d")
    add_text("card_fastapi_body", 500, 237, "• Async Job-Based Plan Generation Queue\n• Router Modules (Analytics, Chat, KB, Tools)\n• Pydantic v2 Strict Contract Validation\n• Prometheus Auto-Instrumentation", font_size=11, color="#14532d")

    # Auth & Sessions
    add_rect("card_auth", 485, 335, 340, 110, bg="#dcfce7", stroke="#16a34a", stroke_width=2)
    add_text("card_auth_title", 500, 345, "🔒 Auth & Security Service", font_size=13, color="#14532d")
    add_text("card_auth_body", 500, 370, "• JWT Token Sessions in PostgreSQL\n• Google & Facebook OAuth2 Handlers\n• Bring-Your-Own-Key (BYOK) Resolver\n• Role-Based Access Control (Admin / Athlete)", font_size=11, color="#14532d")

    # Parsers
    add_rect("card_parsers", 485, 460, 340, 110, bg="#dcfce7", stroke="#16a34a", stroke_width=2)
    add_text("card_parsers_title", 500, 470, "⏱️ Telemetry & Weather Parsers", font_size=13, color="#14532d")
    add_text("card_parsers_body", 500, 495, "• GpxParser: Terrain Slopes, Elevation Gain\n• FitParser: Garmin Cadence & Heart Rate\n• WeatherService: Heat Index & Rainfall APIs\n• Deterministic Treadmill Gradient Converter", font_size=11, color="#14532d")

    # SQLAlchemy Core / DB Access
    add_rect("card_db_access", 485, 585, 340, 110, bg="#dcfce7", stroke="#16a34a", stroke_width=2)
    add_logo("postgresql", 500, 595, 24)
    add_text("card_db_title", 535, 598, "SQLAlchemy Core (db.py)", font_size=13, color="#14532d")
    add_text("card_db_body", 500, 627, "• Parameterized Raw SQL (text() helpers)\n• High Throughput, Zero Heavy ORM Overhead\n• Alembic Versioning + Idempotent init_db()\n• Connection Pooling for High Concurrency", font_size=11, color="#14532d")

    # Event Producer (Kafka)
    add_rect("card_kafka_prod", 485, 710, 340, 110, bg="#e0e7ff", stroke="#4338ca", stroke_width=2)
    add_logo("kafka", 500, 720, 24)
    add_text("card_kafka_prod_title", 535, 723, "Kafka Event Producer", font_size=13, color="#312e81")
    add_text("card_kafka_prod_body", 500, 752, "• Publishes: workout_logged, plan_generated\n• Non-blocking background worker daemon\n• Structured Telemetry Stream Serialization", font_size=11, color="#1e1b4b")


    # ==========================================
    # 3. PHYSIOLOGICAL & AI ENGINES (Column 3: x = 890 .. 1320)
    # Divided into: 1. Plan Generator, 2. Coach Uphill, 3. Specialized Tools & Labs
    # ==========================================
    add_rect("room_engines", 890, 140, 430, 720, bg="#faf5ff", stroke="#d8b4fe", stroke_width=1, stroke_style="dashed", opacity=70, roundness=3)
    add_text("room_engines_title", 905, 152, "PHYSIOLOGICAL & AI ENGINES", font_size=14, color="#7e22ce")
    add_text("room_engines_desc", 905, 172, "Periodization • Grounded Coach • Specialized Tools", font_size=11, color="#581c87")

    # 1. Plan Generator Engine
    add_rect("card_plan_gen", 905, 195, 400, 175, bg="#f3e8ff", stroke="#9333ea", stroke_width=2)
    add_text("card_plan_title", 920, 205, "📋 1. Plan Generator (Periodization Engine)", font_size=13, color="#581c87")
    add_text("card_plan_tech", 920, 225, "Technique: Rule-Based Periodization + Async Job Workers", font_size=10, color="#7c3aed")
    add_text("card_plan_body", 920, 245, "• 5-Zone Model Anchored on AeT/AnT (Uphill Athlete)\n• Automated 80/20 Intensity Volume Compliance Audit\n• Muscular Endurance (ME) Blocks (Weighted Steps, Hills)\n• Deterministic Treadmill Speed & Incline Solver\n• Sequential Block Generator with Injury Swapping", font_size=11, color="#3b0764")

    # 2. Coach Uphill Chatbot
    add_rect("card_gemini_rag", 905, 385, 400, 175, bg="#ede9fe", stroke="#7c3aed", stroke_width=2)
    add_logo("gemini", 920, 395, 24)
    add_logo("qdrant", 952, 395, 24)
    add_text("card_gemini_title", 988, 398, "2. Coach Uphill (Grounded AI Chatbot)", font_size=13, color="#4c1d95")
    add_text("card_gemini_tech", 920, 425, "Technique: Qdrant Vector RAG + Gemini 2.5 Flash + Refusal Policy", font_size=10, color="#6d28d9")
    add_text("card_gemini_body", 920, 445, "• Grounded on Distilled kb_chunks & Coaching Literature\n• Live Athlete Context: Active Calendar & Fatigue State\n• Strict Zero-Hallucination Refusal Safeguards\n• Full Native Bilingual Generative Coaching (EN / VI)\n• Sweat Rate & Hydration Math Verification", font_size=11, color="#2e1065")

    # 3. Specialized Tools & Labs
    add_rect("card_tools_suite", 905, 575, 400, 245, bg="#ede9fe", stroke="#7c3aed", stroke_width=2)
    add_text("card_tools_title", 920, 585, "🛠️ 3. Specialized Tools, Labs & Ingestion", font_size=13, color="#4c1d95")
    add_text("card_tools_tech", 920, 605, "Technique: Minetti Physics + Tavily Scraping + YouTube Parser", font_size=10, color="#6d28d9")
    tools_detail_text = (
        "• Pace Strategy: Minetti (2002) Energy Cost Curve,\n"
        "  Altitude (>1500m) & Live Heat Degradation Splits\n"
        "• Goal Determiner: ITRA Terrain Inversion, Asymmetric\n"
        "  A/B/C Goals, DUV Ultramarathon Rank Transfer\n"
        "• Gear Finder: 100% Full-Catalog Grounded Trail Shoes\n"
        "• Nutrition Lab: Dynamic 60-90g/h Carb & Sodium Plan\n"
        "• Continuous KB Distillation: NotebookLM Sweeps +\n"
        "  Evoke Endurance Podcast YouTube Transcript Crawler"
    )
    add_text("card_tools_body", 920, 625, tools_detail_text, font_size=11, color="#2e1065")


    # ==========================================
    # 4. DATA PLATFORM & STORAGE (Column 4: x = 1370 .. 1850)
    # ==========================================
    add_rect("room_data", 1370, 140, 470, 720, bg="#eef2ff", stroke="#a5b4fc", stroke_width=1, stroke_style="dashed", opacity=70, roundness=3)
    add_text("room_data_title", 1385, 152, "ENTERPRISE DATA PLATFORM & STORAGE", font_size=14, color="#4338ca")
    add_text("room_data_desc", 1385, 172, "Kafka, Spark, DuckDB/dbt, Airflow & Observability", font_size=11, color="#312e81")

    # Storage Row (Qdrant on left, Postgres on right)
    add_rect("card_qdrant", 1385, 195, 210, 115, bg="#fee2e2", stroke="#ef4444", stroke_width=2)
    add_logo("qdrant", 1395, 205, 24)
    add_text("card_qd_title", 1430, 208, "Qdrant Vector DB", font_size=13, color="#7f1d1d")
    add_text("card_qd_body", 1395, 237, "• gemini-embedding-2\n• uphill_kb_scheduler\n• Hybrid Vector Search", font_size=11, color="#7f1d1d")

    add_rect("card_postgres", 1615, 195, 210, 115, bg="#e0e7ff", stroke="#4f46e5", stroke_width=2)
    add_logo("postgresql", 1625, 205, 24)
    add_text("card_pg_title", 1660, 208, "PostgreSQL 16", font_size=13, color="#1e1b4b")
    add_text("card_pg_body", 1625, 237, "• Users & Sessions Table\n• Workouts & Calendar Plans\n• Distilled KB Chunks", font_size=11, color="#1e1b4b")

    # Kafka Broker & Consumer
    add_rect("card_kafka_cluster", 1385, 325, 440, 95, bg="#e0e7ff", stroke="#4f46e5", stroke_width=2)
    add_logo("kafka", 1395, 335, 24)
    add_text("card_kafka_title", 1430, 338, "Apache Kafka 3.7 (Docker Kraft Cluster)", font_size=13, color="#1e1b4b")
    add_text("card_kafka_body", 1395, 365, "• Topics: uphill.workouts, uphill.plans, uphill.telemetry\n• Dedicated Python Consumer Worker Daemon (kafka_consumer_worker.py)", font_size=11, color="#1e1b4b")

    # Spark & Delta Lake
    add_rect("card_spark", 1385, 435, 440, 95, bg="#ffedd5", stroke="#ea580c", stroke_width=2)
    add_logo("spark", 1395, 445, 24)
    add_text("card_spark_title", 1430, 448, "Apache Spark 3.5 & Delta Lake", font_size=13, color="#7c2d12")
    add_text("card_spark_body", 1395, 475, "• Distributed Batch Aggregations (spark_delta_dim_user)\n• Training Load & Volume Progression Feature Tables", font_size=11, color="#7c2d12")

    # DuckDB + dbt Warehouse
    add_rect("card_duckdb", 1385, 545, 440, 105, bg="#fef9c3", stroke="#ca8a04", stroke_width=2)
    add_logo("duckdb", 1395, 555, 24)
    add_logo("dbt", 1427, 555, 24)
    add_text("card_duck_title", 1460, 558, "DuckDB + dbt Core Data Warehouse", font_size=13, color="#713f12")
    add_text("card_duck_body", 1395, 587, "• Incremental Warehouse Extractor (warehouse_extractor.py)\n• Dimensional Models: dim_user, fct_workouts, fct_plans\n• Automated dbt Data Quality Testing & Snapshots", font_size=11, color="#713f12")

    # Bottom Row in Col 4: Airflow & Observability side by side
    add_rect("card_airflow", 1385, 665, 210, 155, bg="#e0f2fe", stroke="#0284c7", stroke_width=2)
    add_logo("airflow", 1395, 675, 24)
    add_text("card_airflow_title", 1430, 678, "Apache Airflow 2.9", font_size=12, color="#0c4a6e")
    add_text("card_airflow_body", 1395, 707, "• kb_distill_dag (Weekly)\n• dw_elt_dag (dbt ELT)\n• spark_delta_dim_user_dag\n• Automated Retries", font_size=10, color="#0c4a6e")

    add_rect("card_observability", 1615, 665, 210, 155, bg="#f1f5f9", stroke="#64748b", stroke_width=2)
    add_logo("prometheus", 1625, 675, 24)
    add_logo("grafana", 1657, 675, 24)
    add_logo("metabase", 1689, 675, 24)
    add_text("card_obs_title", 1722, 678, "Observability & BI", font_size=12, color="#0f172a")
    add_text("card_obs_body", 1625, 707, "• Prometheus & Grafana\n• Real-Time API Metrics\n• Metabase BI Dashboards\n• Retention & Load Analytics", font_size=10, color="#334155")


    # ==========================================
    # 5. CONNECTIONS & ARROWS (Carefully Routed & Non-Overlapping)
    # ==========================================

    # A. Client to Gateway
    add_arrow("arrow_web_to_api", "card_web", "card_fastapi", [(405, 245), (485, 245)], stroke="#ea580c", stroke_width=2)
    add_arrow("arrow_mobile_to_api", "card_mobile", "card_fastapi", [(405, 415), (445, 415), (445, 275), (485, 275)], stroke="#ea580c", stroke_width=2)
    add_arrow("arrow_telemetry_to_parsers", "card_telemetry_input", "card_parsers", [(405, 740), (445, 740), (445, 515), (485, 515)], stroke="#ca8a04", stroke_width=2)

    # B. Gateway to Engines (Col 2 -> Col 3)
    add_arrow("arrow_api_to_plangen", "card_fastapi", "card_plan_gen", [(825, 245), (905, 245)], stroke="#16a34a", stroke_width=2)
    add_arrow("arrow_api_to_gemini", "card_fastapi", "card_gemini_rag", [(825, 270), (865, 270), (865, 460), (905, 460)], stroke="#16a34a", stroke_width=2)
    add_arrow("arrow_api_to_tools", "card_fastapi", "card_tools_suite", [(825, 290), (865, 290), (865, 680), (905, 680)], stroke="#16a34a", stroke_width=2)

    # C. Col 2 DB Access -> PostgreSQL (Clean Top Highway at y = 95, completely above rooms!)
    add_arrow("arrow_dbaccess_to_pg", "card_db_access", "card_postgres", [(825, 620), (865, 620), (865, 95), (1720, 95), (1720, 195)], stroke="#16a34a", stroke_width=2)

    # D. Col 2 Kafka Producer -> Kafka Cluster (Clean Bottom Highway at y = 875, completely below rooms!)
    add_arrow("arrow_prod_to_kafka", "card_kafka_prod", "card_kafka_cluster", [(825, 760), (865, 760), (865, 875), (1350, 875), (1350, 370), (1385, 370)], stroke="#4338ca", stroke_width=2)

    # E. Gemini RAG -> Qdrant Vector DB (Clean Inter-Column Gutter at x = 1345)
    add_arrow("arrow_gemini_to_qdrant", "card_gemini_rag", "card_qdrant", [(1305, 460), (1345, 460), (1345, 245), (1385, 245)], stroke="#7c3aed", stroke_width=2)

    # F. Tools Suite -> Airflow DAGs (Direct horizontal link across gap)
    add_arrow("arrow_tools_to_airflow", "card_tools_suite", "card_airflow", [(1305, 730), (1385, 730)], stroke="#0284c7", stroke_width=2)

    # G. Col 4 Internal Data Platform Flow (Top to Bottom)
    add_arrow("arrow_kafka_to_spark", "card_kafka_cluster", "card_spark", [(1605, 420), (1605, 435)], stroke="#4f46e5", stroke_width=2)
    add_arrow("arrow_spark_to_duck", "card_spark", "card_duckdb", [(1605, 530), (1605, 545)], stroke="#ea580c", stroke_width=2)
    add_arrow("arrow_airflow_to_duck", "card_airflow", "card_duckdb", [(1490, 665), (1490, 650)], stroke="#0284c7", stroke_width=2)
    add_arrow("arrow_duck_to_obs", "card_duckdb", "card_observability", [(1720, 650), (1720, 665)], stroke="#ca8a04", stroke_width=2)

    return {
        "type": "excalidraw",
        "version": 2,
        "source": "https://excalidraw.com",
        "elements": elements,
        "appState": {
            "viewBackgroundColor": "#ffffff",
            "gridSize": None
        },
        "files": files_dict
    }

def main():
    diagram_data = create_excalidraw_diagram()

    paths = [
        Path("/Users/vietvo/Documents/antigravity/uphill-ai/.claude/worktrees/readme-rewrite/assets/architecture/uphill_ai_architecture.excalidraw"),
        Path("/Users/vietvo/Documents/antigravity/uphill-ai/assets/architecture/uphill_ai_architecture.excalidraw"),
        Path("/Users/vietvo/Documents/antigravity/uphill-ai/docs/architecture/uphill_ai_architecture.excalidraw")
    ]

    for p in paths:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(diagram_data, indent=2), encoding="utf-8")
        print(f"Wrote Excalidraw JSON to: {p}")

if __name__ == "__main__":
    main()
