#!/usr/bin/env python3
import json
import os
import sys
import rumps

STORAGE_DIR = os.path.expanduser("~/Library/Application Support/Tickr")
STORAGE_FILE = os.path.join(STORAGE_DIR, "tasks.json")

class TickrApp(rumps.App):
    def __init__(self):
        super(TickrApp, self).__init__("⚡ Tickr", title="⚡ Tickr")
        self.tasks = self.load_tasks()
        self.rebuild_menu()

    def load_tasks(self):
        if not os.path.exists(STORAGE_DIR):
            os.makedirs(STORAGE_DIR, exist_ok=True)
        if os.path.exists(STORAGE_FILE):
            try:
                with open(STORAGE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        # Default starter tasks
        return [
            {"title": "Welcome to Tickr! ⚡", "done": False, "category": "General"},
            {"title": "Click a task to check it off", "done": False, "category": "Ideas"},
            {"title": "Add your first real task", "done": False, "category": "Work"}
        ]

    def save_tasks(self):
        try:
            with open(STORAGE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.tasks, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print("Error saving tasks:", e)

    def rebuild_menu(self):
        self.menu.clear()

        # Header Stats
        active = sum(1 for t in self.tasks if not t.get("done", False))
        done = sum(1 for t in self.tasks if t.get("done", False))
        self.title = f"⚡ Tickr ({active})" if active > 0 else "⚡ Tickr ✓"

        # Action Items
        self.menu.add(rumps.MenuItem(f"📊 Tasks: {active} active, {done} completed", callback=None))
        self.menu.add(rumps.separator)
        self.menu.add(rumps.MenuItem("➕ Add New Task...", callback=self.add_task_dialog))
        self.menu.add(rumps.separator)

        # Task Items List
        if not self.tasks:
            self.menu.add(rumps.MenuItem("🎉 No pending tasks! (Click + to add)", callback=None))
        else:
            for idx, task in enumerate(self.tasks):
                status_icon = "✅" if task.get("done", False) else "⭕"
                cat = f"[{task.get('category', 'General')}] " if task.get("category") else ""
                item_title = f"{status_icon} {cat}{task['title']}"
                
                menu_item = rumps.MenuItem(item_title, callback=self.make_toggle_callback(idx))
                self.menu.add(menu_item)

        self.menu.add(rumps.separator)

        # Clear / Management options
        if done > 0:
            self.menu.add(rumps.MenuItem(f"🧹 Clear Done ({done})", callback=self.clear_completed))

        # Delete submenu
        if self.tasks:
            delete_menu = rumps.MenuItem("🗑️ Delete a Task")
            for idx, task in enumerate(self.tasks):
                delete_menu.add(rumps.MenuItem(f"Delete: {task['title'][:25]}...", callback=self.make_delete_callback(idx)))
            self.menu.add(delete_menu)

        self.menu.add(rumps.separator)
        self.menu.add(rumps.MenuItem("🚪 Quit Tickr", callback=rumps.quit_application))

    def make_toggle_callback(self, index):
        def callback(sender):
            if 0 <= index < len(self.tasks):
                self.tasks[index]["done"] = not self.tasks[index].get("done", False)
                self.save_tasks()
                self.rebuild_menu()
        return callback

    def make_delete_callback(self, index):
        def callback(sender):
            if 0 <= index < len(self.tasks):
                self.tasks.pop(index)
                self.save_tasks()
                self.rebuild_menu()
        return callback

    def add_task_dialog(self, _):
        window = rumps.Window(
            message="Type your task description:",
            title="➕ Add Task to Tickr",
            default_text="",
            ok="Add Task",
            cancel="Cancel",
            dimensions=(320, 24)
        )
        response = window.run()
        if response.clicked and response.text.strip():
            self.tasks.insert(0, {"title": response.text.strip(), "done": False, "category": "Work"})
            self.save_tasks()
            self.rebuild_menu()
            rumps.notification("Tickr", "Task Added!", f"Added: {response.text.strip()}")

    def clear_completed(self, _):
        self.tasks = [t for t in self.tasks if not t.get("done", False)]
        self.save_tasks()
        self.rebuild_menu()

if __name__ == "__main__":
    app = TickrApp()
    app.run()
