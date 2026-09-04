#!/usr/bin/env python3
"""
Tickr CLI Companion
Interact with Tickr directly from Terminal, Raycast, and Alfred.
"""
import sys
import os
import json
import argparse
import datetime

BACKUP_DIR = os.path.expanduser("~/Library/Application Support/Tickr")
BACKUP_FILE = os.path.join(BACKUP_DIR, "tasks.json")
DIARY_DIR = os.path.expanduser("~/Projects/esawi.dev")
DIARY_PATH = os.path.join(DIARY_DIR, "src/data/diary.json")

NOTES_HISTORY_FILE = os.path.join(BACKUP_DIR, "notes_history.json")

def load_tasks():
    if os.path.exists(BACKUP_FILE):
        try:
            with open(BACKUP_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def save_tasks(tasks):
    os.makedirs(BACKUP_DIR, exist_ok=True)
    with open(BACKUP_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=2, ensure_ascii=False)

def load_notes():
    if os.path.exists(NOTES_HISTORY_FILE):
        try:
            with open(NOTES_HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def list_notes():
    notes = load_notes()
    print(f"\n📝 Tickr Notes ({len(notes)} total)")
    print("-" * 50)
    for idx, n in enumerate(notes, 1):
        updated = n.get("updatedAt", "")[:16].replace("T", " ")
        print(f"  {idx}. {n.get('title', 'Untitled')} ({updated})")
    if not notes:
        print("  (No notes found)")
    print()

def export_note_cli(index=1):
    notes = load_notes()
    if not notes:
        print("No notes available to export.")
        return
    if index < 1 or index > len(notes):
        print(f"Invalid note index: {index}. Choose between 1 and {len(notes)}.")
        return
    note = notes[index - 1]
    from tickr_app import export_note_to_apple_notes
    ok = export_note_to_apple_notes(note.get("content", ""), note.get("title", ""))
    if ok:
        print(f"✓ Successfully exported '{note.get('title', 'Untitled')}' to Apple Notes!")
    else:
        print("Failed to export note.")

def add_task(title, category="PROJECT"):
    tasks = load_tasks()
    new_task = {
        "id": int(datetime.datetime.now().timestamp() * 1000),
        "title": title,
        "category": category.upper(),
        "done": False,
        "created": datetime.datetime.now().isoformat()
    }
    tasks.insert(0, new_task)
    save_tasks(tasks)
    print(f"✓ Added task: [{new_task['category']}] {new_task['title']}")

def list_tasks():
    tasks = load_tasks()
    pending = [t for t in tasks if not t.get("done", False)]
    done = [t for t in tasks if t.get("done", False)]
    
    print(f"\n⚡ Tickr Tasks ({len(pending)} pending // {len(done)} completed)")
    print("-" * 50)
    for idx, t in enumerate(pending, 1):
        print(f"  {idx}. [ ] [{t.get('category', 'TASK')}] {t['title']}")
    if not pending:
        print("  ✓ All tasks cleared!")
    print()

def print_standup():
    tasks = load_tasks()
    today = datetime.date.today().isoformat()
    completed = [t for t in tasks if t.get("done", False)]
    pending = [t for t in tasks if not t.get("done", False)]
    
    print(f"### 🚀 Daily Standup ({today})\n")
    print("**Completed:**")
    if completed:
        for t in completed:
            print(f"- [x] {t['title']}")
    else:
        print("- (No tasks completed yet)")
        
    print("\n**In Progress:**")
    if pending:
        for t in pending[:5]:
            print(f"- [ ] {t['title']}")
    else:
        print("- (All tasks cleared)")

def main():
    parser = argparse.ArgumentParser(description="Tickr macOS CLI Companion")
    subparsers = parser.add_subparsers(dest="command")

    # Add command
    add_parser = subparsers.add_parser("add", help="Add a new task")
    add_parser.add_argument("title", type=str, help="Task title")
    add_parser.add_argument("--tag", "-t", type=str, default="PROJECT", help="Category tag")

    # List command
    subparsers.add_parser("list", help="List all pending tasks")

    # Standup command
    subparsers.add_parser("standup", help="Generate formatted markdown standup report")

    # Notes list command
    subparsers.add_parser("notes", help="List past markdown scratchpad notes")

    # Export note command
    export_parser = subparsers.add_parser("export-note", help="Export a note to Apple Notes app")
    export_parser.add_argument("index", type=int, nargs="?", default=1, help="Index of the note to export (default: 1 for latest)")

    args = parser.parse_args()

    if args.command == "add":
        add_task(args.title, args.tag)
    elif args.command == "list" or not args.command:
        list_tasks()
    elif args.command == "standup":
        print_standup()
    elif args.command == "notes":
        list_notes()
    elif args.command == "export-note":
        export_note_cli(args.index)

if __name__ == "__main__":
    main()
