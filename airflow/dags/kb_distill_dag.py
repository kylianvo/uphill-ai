"""Weekly KB distillation: sweep -> validate -> embed, per domain, in parallel.
gear/nutrition-products source from live web discovery (Tavily); nutrition-principles/
scheduler still sweep NotebookLM. A separate race_results task group enriches the
hand-curated race_courses KB with newly-discovered result-year stats (winner times,
finisher counts, percentiles) for races that already have a curated `results` block --
it doesn't fit the sweep/validate/embed shape (race_courses is hand-curated, not one of
the three DOMAINS distilled via distill_domain) so it calls kb_distiller's dedicated
discover_race_results_web/save_race_results functions directly.
See docs/superpowers/specs/2026-07-27-airflow-kb-distill-design.md for the full design."""

import asyncio
from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.task_group import TaskGroup

DOMAINS = ("gear", "nutrition", "scheduler")

default_args = {"owner": "uphill-ai", "retries": 1}


def _sweep(domain: str, **context):
    from config import settings
    from services.kb_distiller import sweep_domain

    api_key = settings.GEMINI_API_KEY
    rows = asyncio.run(sweep_domain(domain, api_key, {}))
    if not rows and domain != "gear":
        raise RuntimeError(f"Distillation produced an empty result for '{domain}' — keeping existing KB.")
    return rows


def _validate(domain: str, **context):
    from services.kb_distiller import validate_domain_rows

    ti = context["ti"]
    rows = ti.xcom_pull(task_ids=f"{domain}.sweep_{domain}")
    return validate_domain_rows(domain, rows)


def _embed(domain: str, **context):
    from config import settings
    from services.kb_distiller import save_domain

    ti = context["ti"]
    rows = ti.xcom_pull(task_ids=f"{domain}.validate_{domain}")
    api_key = settings.GEMINI_API_KEY
    return asyncio.run(save_domain(domain, rows, api_key))


def _discover_race_results(**context):
    from config import settings
    from services.kb_distiller import discover_race_results_web

    return asyncio.run(discover_race_results_web(settings.GEMINI_API_KEY, settings.TAVILY_API_KEY, {}))


def _save_race_results(**context):
    from services.kb_distiller import save_race_results

    ti = context["ti"]
    updates = ti.xcom_pull(task_ids="race_results.discover_race_results")
    return save_race_results(updates)


with DAG(
    dag_id="kb_distill",
    default_args=default_args,
    schedule_interval="@weekly",
    start_date=datetime(2026, 7, 20),
    catchup=False,
    tags=["kb", "uphill-ai"],
) as dag:
    for domain in DOMAINS:
        with TaskGroup(group_id=domain) as tg:
            sweep_task = PythonOperator(
                task_id=f"sweep_{domain}",
                python_callable=_sweep,
                op_kwargs={"domain": domain},
                execution_timeout=None,  # NotebookLM/Tavily+Gemini sweeps can run several minutes
            )
            validate_task = PythonOperator(
                task_id=f"validate_{domain}",
                python_callable=_validate,
                op_kwargs={"domain": domain},
            )
            embed_task = PythonOperator(
                task_id=f"embed_{domain}",
                python_callable=_embed,
                op_kwargs={"domain": domain},
            )
            sweep_task >> validate_task >> embed_task

    with TaskGroup(group_id="race_results") as race_results_tg:
        discover_task = PythonOperator(
            task_id="discover_race_results",
            python_callable=_discover_race_results,
            execution_timeout=None,  # Tavily+Gemini per tracked race can run several minutes
        )
        save_task = PythonOperator(
            task_id="save_race_results",
            python_callable=_save_race_results,
        )
        discover_task >> save_task
