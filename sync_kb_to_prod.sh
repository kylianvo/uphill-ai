#!/bin/bash
set -e

# Bundles the local->prod KB sync workflow into one command: review the
# backend/kb_seed/*.json diff produced by a local distillation run (admin
# endpoints or the Airflow kb_distill DAG), commit it, push, and deploy via
# deploy_kb.sh. Deliberately still manually invoked and requires an explicit
# confirmation before anything is committed or pushed -- kb_seed content is
# AI-structured from live web sources (Tavily/Gemini), and this repo has
# already caught real data-quality bugs in that content during development
# (a hallucinated race result, a duplicated brand name, and a near-miss where
# an under-seeded local DB would have deleted most of a domain's catalog on
# export). Auto-committing and auto-deploying that content with no human
# review is a real risk, not a hypothetical one -- see the comment on this in
# CLAUDE.md's KB lifecycle section. This script keeps a human decision point
# right before "push"; it does not remove it.
#
# Usage: ./sync_kb_to_prod.sh [--domain gear|nutrition|scheduler|race_courses|all]
# Defaults to --domain all (gear+nutrition+scheduler -- matches deploy_kb.sh,
# which excludes race_courses from "all"; deploy it explicitly).

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

# Scope strictly to the requested domain's seed file(s) -- not the whole
# backend/kb_seed/ directory. Committing/pushing everything in that directory
# regardless of --domain would silently sweep in unrelated changes (e.g. a
# different domain's in-progress or unreviewed distillation output).
if [ "$DOMAIN" = "all" ]; then
  SEED_FILES="backend/kb_seed/gear.json backend/kb_seed/nutrition.json backend/kb_seed/scheduler.json"
else
  SEED_FILES="backend/kb_seed/$DOMAIN.json"
fi

# Snapshot which of those files actually changed, once, up front. This exact
# list is reused for both the diff shown below AND the git add/commit after
# confirmation -- never re-queried in between -- so what gets committed is
# guaranteed to be exactly what was reviewed. Re-querying git status after
# the confirmation prompt would open a gap where a concurrent write to
# kb_seed/ (a background DAG run, for instance) changes what actually gets
# committed to something the operator never saw and never approved.
CHANGED_FILES=""
for f in $SEED_FILES; do
  if [ -n "$(git status --porcelain -- "$f")" ]; then
    CHANGED_FILES="$CHANGED_FILES $f"
  fi
done

if [ -z "$CHANGED_FILES" ]; then
  echo "No changes in: $SEED_FILES -- nothing to sync. Run a distillation first."
  exit 0
fi

echo "=== Changes to:$CHANGED_FILES ==="
git diff --stat -- $CHANGED_FILES
echo
git diff -- $CHANGED_FILES
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

# Re-check the same file set right before committing. If it no longer matches
# what was just reviewed above, something wrote to these files while the
# operator was reading the diff -- abort rather than silently committing
# content that was never actually shown to them.
CHANGED_FILES_NOW=""
for f in $SEED_FILES; do
  if [ -n "$(git status --porcelain -- "$f")" ]; then
    CHANGED_FILES_NOW="$CHANGED_FILES_NOW $f"
  fi
done
if [ "$CHANGED_FILES_NOW" != "$CHANGED_FILES" ]; then
  echo "ERROR: these files changed on disk after the diff above was shown:" >&2
  echo "  reviewed:$CHANGED_FILES" >&2
  echo "  now:     $CHANGED_FILES_NOW" >&2
  echo "Aborting without committing -- re-run this script to review the current state." >&2
  exit 1
fi

git add -- $CHANGED_FILES
git commit -m "chore(kb): sync $DOMAIN seed data from local distillation"
git push

echo
echo "=== Deploying to prod ==="
./deploy_kb.sh --domain "$DOMAIN"
