#!/usr/bin/env python3
import sys
import os
import json
import datetime
import subprocess
import Cocoa
import WebKit
import objc

DIARY_DIR = os.path.expanduser("~/Projects/esawi.dev")
DIARY_PATH = os.path.join(DIARY_DIR, "src/data/diary.json")
BACKUP_DIR = os.path.expanduser("~/Library/Application Support/Tickr")
BACKUP_FILE = os.path.join(BACKUP_DIR, "tasks.json")
UI_HTML_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui", "index.html")

def load_tasks_from_disk():
    if os.path.exists(DIARY_PATH):
        try:
            with open(DIARY_PATH, "r", encoding="utf-8") as f:
                diary = json.load(f)
            
            tasks = []
            id_counter = 1
            
            # Pending tasks
            for item in diary.get("log", {}).get("pending", []):
                tasks.append({
                    "id": id_counter,
                    "title": item,
                    "category": "Project",
                    "done": False
                })
                id_counter += 1
            
            # Completed tasks (most recent first)
            for item in reversed(diary.get("log", {}).get("completed", [])):
                cat = item.get("type", "Project").capitalize()
                tasks.append({
                    "id": id_counter,
                    "title": item.get("description", ""),
                    "category": cat,
                    "done": True,
                    "date": item.get("date", "")
                })
                id_counter += 1
            
            if tasks:
                return tasks
        except Exception as e:
            print("Error reading diary.json:", e)

    return []

def save_tasks_to_disk(tasks):
    # 1. Save backup to local App Support
    try:
        if not os.path.exists(BACKUP_DIR):
            os.makedirs(BACKUP_DIR, exist_ok=True)
        with open(BACKUP_FILE, "w", encoding="utf-8") as f:
            json.dump(tasks, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print("Backup save error:", e)

    # 2. Synchronize with esawi.dev diary.json
    if os.path.exists(DIARY_PATH):
        try:
            with open(DIARY_PATH, "r", encoding="utf-8") as f:
                diary = json.load(f)

            if "log" not in diary:
                diary["log"] = {"completed": [], "pending": []}

            # Update pending array
            diary["log"]["pending"] = [
                t["title"] for t in tasks if not t.get("done", False)
            ]

            # Update completed array
            today_str = datetime.date.today().isoformat()
            completed_items = []
            
            for t in tasks:
                if t.get("done", False):
                    cat = t.get("category", "project").lower()
                    date_val = t.get("date") or today_str
                    completed_items.append({
                        "type": cat,
                        "description": t["title"],
                        "date": date_val
                    })

            diary["log"]["completed"] = list(reversed(completed_items))

            with open(DIARY_PATH, "w", encoding="utf-8") as f:
                json.dump(diary, f, indent=2, ensure_ascii=False)
            
            print(f"✓ Synchronized {len(tasks)} tasks with esawi.dev diary.json")
        except Exception as e:
            print("Error syncing diary.json:", e)

class ScriptHandler(Cocoa.NSObject):
    def userContentController_didReceiveScriptMessage_(self, userContentController, message):
        body = message.body()
        action = None
        data = None

        if isinstance(body, (dict, Cocoa.NSDictionary)):
            action = body.get("action")
            data = body.get("data")
        elif isinstance(body, str):
            try:
                parsed = json.loads(body)
                action = parsed.get("action")
                data = parsed.get("data")
            except Exception:
                pass

        if action == "save" and data is not None:
            if isinstance(data, str):
                try:
                    tasks_list = json.loads(data)
                except Exception:
                    tasks_list = []
            else:
                tasks_list = list(data)
            
            save_tasks_to_disk(tasks_list)
            
            app_delegate = Cocoa.NSApp().delegate()
            if app_delegate:
                app_delegate.update_badge_count(tasks_list)

        elif action == "publish":
            # Save first
            if data is not None:
                tasks_list = json.loads(data) if isinstance(data, str) else list(data)
                save_tasks_to_disk(tasks_list)
            
            # Commit and push to git
            try:
                cmd = f"cd {DIARY_DIR} && git add src/data/diary.json && git commit -m 'chore(diary): sync completed tasks from Tickr ⚡' && git push origin main"
                proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                stdout, stderr = proc.communicate()
                print("Git publish output:", stdout, stderr)
                
                app_delegate = Cocoa.NSApp().delegate()
                if app_delegate and app_delegate.webView:
                    app_delegate.webView.evaluateJavaScript_completionHandler_("if(window.onPublishSuccess) onPublishSuccess();", None)
            except Exception as e:
                print("Publish error:", e)

        elif action == "quit":
            Cocoa.NSApplication.sharedApplication().terminate_(None)

class AppDelegate(Cocoa.NSObject):
    def applicationDidFinishLaunching_(self, notification):
        Cocoa.NSApp().setActivationPolicy_(Cocoa.NSApplicationActivationPolicyAccessory)

        # Status Bar Item in Menu Bar
        self.statusItem = Cocoa.NSStatusBar.systemStatusBar().statusItemWithLength_(Cocoa.NSVariableStatusItemLength)
        button = self.statusItem.button()
        button.setTitle_("⚡ Tickr")
        button.setTarget_(self)
        button.setAction_(objc.selector(self.togglePopover_, signature=b"v@:@"))

        # WKWebView Configuration
        contentController = WebKit.WKUserContentController.alloc().init()
        self.handler = ScriptHandler.alloc().init()
        contentController.addScriptMessageHandler_name_(self.handler, "tickr")

        config = WebKit.WKWebViewConfiguration.alloc().init()
        config.setUserContentController_(contentController)

        # Create WKWebView
        frame = Cocoa.NSMakeRect(0, 0, 370, 480)
        self.webView = WebKit.WKWebView.alloc().initWithFrame_configuration_(frame, config)
        self.webView.setValue_forKey_(False, "drawsBackground")

        # Load HTML
        file_url = Cocoa.NSURL.fileURLWithPath_(UI_HTML_PATH)
        self.webView.loadFileURL_allowingReadAccessToURL_(file_url, file_url.URLByDeletingLastPathComponent())

        # Load initial tasks from diary.json
        tasks = load_tasks_from_disk()
        self.update_badge_count(tasks)
        tasks_json = json.dumps(tasks)
        js_code = f"setTimeout(function() {{ if(window.initTasks) initTasks({tasks_json}); }}, 350);"
        self.webView.evaluateJavaScript_completionHandler_(js_code, None)

        # Popover
        self.popover = Cocoa.NSPopover.alloc().init()
        self.popover.setContentSize_(Cocoa.NSMakeSize(370, 480))
        self.popover.setBehavior_(Cocoa.NSPopoverBehaviorTransient)
        self.popover.setAnimates_(True)

        viewController = Cocoa.NSViewController.alloc().init()
        viewController.setView_(self.webView)
        self.popover.setContentViewController_(viewController)

    def update_badge_count(self, tasks):
        active = sum(1 for t in tasks if not t.get("done", False))
        button = self.statusItem.button()
        if button:
            if active > 0:
                button.setTitle_(f"⚡ {active}")
            else:
                button.setTitle_("⚡ ✓")

    def togglePopover_(self, sender):
        button = self.statusItem.button()
        if self.popover.isShown():
            self.popover.performClose_(sender)
        else:
            tasks = load_tasks_from_disk()
            tasks_json = json.dumps(tasks)
            self.webView.evaluateJavaScript_completionHandler_(f"if(window.initTasks) initTasks({tasks_json});", None)
            self.popover.showRelativeToRect_ofView_preferredEdge_(button.bounds(), button, Cocoa.NSMinYEdge)
            Cocoa.NSApp().activateIgnoringOtherApps_(True)

def main():
    app = Cocoa.NSApplication.sharedApplication()
    delegate = AppDelegate.alloc().init()
    app.setDelegate_(delegate)
    app.run()

if __name__ == "__main__":
    main()
