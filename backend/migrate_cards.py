import json
import sqlite3
import sys
import os
from sqlalchemy import text

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db import engine, save_knowledge_cards, clear_knowledge_cards, get_knowledge_card_count

BACKUP_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge_cards_backup.json")
SQLITE_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "coach.db")

def dump_sqlite_to_json():
    """Reads knowledge cards from SQLite coach.db and saves to a JSON file."""
    if not os.path.exists(SQLITE_DB):
        print(f"Error: SQLite database not found at {SQLITE_DB}")
        sys.exit(1)
        
    print(f"Connecting to SQLite database: {SQLITE_DB}")
    conn = sqlite3.connect(SQLITE_DB)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='knowledge_cards';")
        if not cursor.fetchone():
            print("Error: 'knowledge_cards' table does not exist in SQLite database.")
            sys.exit(1)
            
        cursor.execute("SELECT chapter_title, summary, key_points, tags, topic, source_label FROM knowledge_cards;")
        rows = cursor.fetchall()
        
        cards = []
        for r in rows:
            # Parse JSON strings from SQLite if stored as strings
            try:
                kp = json.loads(r["key_points"])
            except:
                kp = r["key_points"]
                
            try:
                tg = json.loads(r["tags"])
            except:
                tg = r["tags"]
                
            cards.append({
                "chapter_title": r["chapter_title"],
                "summary": r["summary"],
                "key_points": kp,
                "tags": tg,
                "topic": r["topic"],
                "source_label": r["source_label"]
            })
            
        print(f"Found {len(cards)} knowledge cards in SQLite.")
        
        with open(BACKUP_FILE, "w", encoding="utf-8") as f:
            json.dump(cards, f, indent=2, ensure_ascii=False)
            
        print(f"🎉 Successfully backed up {len(cards)} cards to {BACKUP_FILE}")
        
    except Exception as e:
        print(f"Error dumping SQLite: {e}")
        sys.exit(1)
    finally:
        conn.close()

def load_json_to_db():
    """Reads knowledge cards from JSON and saves them to the active SQL database."""
    if not os.path.exists(BACKUP_FILE):
        print(f"Error: Backup file not found at {BACKUP_FILE}")
        sys.exit(1)
        
    print(f"Reading backup from {BACKUP_FILE}")
    with open(BACKUP_FILE, "r", encoding="utf-8") as f:
        cards = json.load(f)
        
    print(f"Loaded {len(cards)} cards from backup file.")
    print("Clearing existing knowledge cards in target database...")
    
    try:
        clear_knowledge_cards()
        print("Existing cards cleared.")
        
        print("Inserting cards into database...")
        saved = save_knowledge_cards(cards)
        print(f"🎉 Successfully loaded {saved}/{len(cards)} cards into the target database.")
        print(f"Current card count in DB: {get_knowledge_card_count()}")
        
    except Exception as e:
        print(f"Error loading to database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python migrate_cards.py [dump|load]")
        sys.exit(1)
        
    action = sys.argv[1].lower()
    if action == "dump":
        dump_sqlite_to_json()
    elif action == "load":
        load_json_to_db()
    else:
        print(f"Unknown action: {action}. Use 'dump' or 'load'.")
        sys.exit(1)
