#!/bin/bash
set -e

# Bundles the local->prod KB sync workflow into one command: review the
# backend/kb_seed/*.json diff produced by a local distillation run (admin
# endpoints or the Airflow kb_distill DAG), commit it, push, and deploy via
# deploy_kb.sh. Deliberately still manually invoked and requires an explicit
# confirmation before anything is committed or pushed -- kb_seed content is
# AI-structured from live web sources (Tavily/Gemini), and this repo has
# already caught real data-quality bugs in that content during development
# (a hallucinated race result, a duplicated brand name). Auto-committing and
# auto-deploying that content with no human review is a real risk, not a
# hypothetical one -- see the comment on this in CLAUDE.md's KB lifecycle
# section. This script keeps a human decision point right before "push"; it
# does not remove it.
#
# Usage: ./sync_kb_to_prod.sh [--domain gear|nutrition|scheduler|race_courses|all]
# Defaults to --domain all (passed straight through to deploy_kb.sh, which
# already excludes race_courses from "all" -- deploy it explicitly).

DOMAIN="all"
while [ $# -gt 0 ]; do
  case "$1" in
    --domain)
      DOMAIN="$2"
      shift 2
      ;;
    *)
      echo "ERROR: unknown argument '$1'. Usage: ./sync_kb_to_prod.sh [--domain gear|nutrition|scheduler|race_courses|all]" >&2
      exit 1
      ;;
  esac
done

case "$DOMAIN" in
  gear|nutrition|scheduler|race_courses|all) ;;
  *)
    echo "ERROR: invalid --domain '$DOMAIN'. Must be one of: gear, nutrition, scheduler, race_courses, all." >&2
    exit 1
    ;;
esac

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ -z "$(git status --porcelain -- backend/kb_seed/)" ]; then
  echo "No changes in backend/kb_seed/ -- nothing to sync. Run a distillation first."
  exit 0
fi

echo "=== Changes to backend/kb_seed/ ==="
git diff --stat -- backend/kb_seed/
echo
git diff -- backend/kb_seed/
echo
echo "=== Review the diff above carefully ==="
echo "This is AI-structured content from live web sources (Tavily search + Gemini"
echo "structuring). Check for anything implausible before it goes to production --"
echo "e.g. a stat that looks hallucinated, a duplicated/garbled name, a spec that"
echo "doesn't match the actual product/race."
echo
read -r -p "Commit, push, and deploy this diff to prod (domain: $DOMAIN)? [y/N] " confirm
if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
  echo "Aborted. No changes committed."
  exit 1
fi

CHANGED_FILES=$(git status --porcelain -- backend/kb_seed/ | awk '{print $2}')
git add -- $CHANGED_FILES
git commit -m "chore(kb): sync $DOMAIN seed data from local distillation"
git push

echo
echo "=== Deploying to prod ==="
./deploy_kb.sh --domain "$DOMAIN"
