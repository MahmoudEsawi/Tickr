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
TAGS_FILE = os.path.join(BACKUP_DIR, "tags.json")
NOTE_FILE = os.path.join(BACKUP_DIR, "scratchpad.md")
LAUNCH_AGENT_PATH = os.path.expanduser("~/Library/LaunchAgents/com.mahmoudesawi.tickr.plist")
ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
ICON_PATH = os.path.join(ASSETS_DIR, "menu_icon.png")
UI_HTML_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui", "index.html")

def send_native_notification(title, message):
    try:
        clean_title = title.replace('"', '\\"')
        clean_msg = message.replace('"', '\\"')
        cmd = f'osascript -e \'display notification "{clean_msg}" with title "⚡ Tickr" subtitle "{clean_title}" sound name "Glass"\''
        subprocess.Popen(cmd, shell=True)
    except Exception as e:
        print("Notification error:", e)

def is_launch_at_login():
    return os.path.exists(LAUNCH_AGENT_PATH)

def set_launch_at_login(enable):
    try:
        if enable:
            os.makedirs(os.path.dirname(LAUNCH_AGENT_PATH), exist_ok=True)
            app_target = "/Applications/Tickr.app" if os.path.exists("/Applications/Tickr.app") else sys.executable
            plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.mahmoudesawi.tickr</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/open</string>
        <string>{app_target}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
</dict>
</plist>"""
            with open(LAUNCH_AGENT_PATH, "w", encoding="utf-8") as f:
                f.write(plist_content)
            send_native_notification("Autostart Enabled", "Tickr will start automatically when your Mac boots.")
        else:
            if os.path.exists(LAUNCH_AGENT_PATH):
                os.remove(LAUNCH_AGENT_PATH)
    except Exception as e:
        print("Autostart setting error:", e)

def load_tags():
    if os.path.exists(TAGS_FILE):
        try:
            with open(TAGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return ["PROJECT", "CODE", "HACKATHON", "DAILY", "IDEAS"]

def save_tags(tags):
    try:
        if not os.path.exists(BACKUP_DIR):
            os.makedirs(BACKUP_DIR, exist_ok=True)
        with open(TAGS_FILE, "w", encoding="utf-8") as f:
            json.dump(tags, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print("Save tags error:", e)

def load_note():
    if os.path.exists(NOTE_FILE):
        try:
            with open(NOTE_FILE, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            pass
    return ""

def save_note(text):
    try:
        if not os.path.exists(BACKUP_DIR):
            os.makedirs(BACKUP_DIR, exist_ok=True)
        with open(NOTE_FILE, "w", encoding="utf-8") as f:
            f.write(text)
    except Exception as e:
        print("Save note error:", e)

def load_tasks_from_disk():
    if os.path.exists(DIARY_PATH):
        try:
            with open(DIARY_PATH, "r", encoding="utf-8") as f:
                diary = json.load(f)
            
            tasks = []
            id_counter = 1
            
            for item in diary.get("log", {}).get("pending", []):
                tasks.append({
                    "id": id_counter,
                    "title": item,
                    "category": "PROJECT",
                    "done": False
                })
                id_counter += 1
            
            for item in reversed(diary.get("log", {}).get("completed", [])):
                cat = item.get("type", "PROJECT").upper()
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
    try:
        if not os.path.exists(BACKUP_DIR):
            os.makedirs(BACKUP_DIR, exist_ok=True)
        with open(BACKUP_FILE, "w", encoding="utf-8") as f:
            json.dump(tasks, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print("Backup save error:", e)

    if os.path.exists(DIARY_PATH):
        try:
            with open(DIARY_PATH, "r", encoding="utf-8") as f:
                diary = json.load(f)

            if "log" not in diary:
                diary["log"] = {"completed": [], "pending": []}

            diary["log"]["pending"] = [
                t["title"] for t in tasks if not t.get("done", False)
            ]

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
        except Exception as e:
            print("Error syncing diary.json:", e)

class ScriptHandler(Cocoa.NSObject):
    def userContentController_didReceiveScriptMessage_(self, userContentController, message):
        body = message.body()
        action = None
        data = None
        tags = None

        if isinstance(body, (dict, Cocoa.NSDictionary)):
            action = body.get("action")
            data = body.get("data")
            tags = body.get("tags")
        elif isinstance(body, str):
            try:
                parsed = json.loads(body)
                action = parsed.get("action")
                data = parsed.get("data")
                tags = parsed.get("tags")
            except Exception:
                pass

        app_delegate = Cocoa.NSApp().delegate()

        if tags:
            tags_list = json.loads(tags) if isinstance(tags, str) else list(tags)
            save_tags(tags_list)

        if action == "save" and data is not None:
            tasks_list = json.loads(data) if isinstance(data, str) else list(data)
            save_tasks_to_disk(tasks_list)
            if app_delegate:
                app_delegate.update_badge_count(tasks_list)

        elif action == "save_note":
            note_text = body.get("text", "") if isinstance(body, (dict, Cocoa.NSDictionary)) else ""
            save_note(note_text)

        elif action == "timer_update":
            time_text = body.get("text", "") if isinstance(body, (dict, Cocoa.NSDictionary)) else ""
            if app_delegate:
                app_delegate.update_timer_display(time_text)

        elif action == "set_autostart":
            enable = body.get("enabled", False) if isinstance(body, (dict, Cocoa.NSDictionary)) else False
            set_launch_at_login(enable)

        elif action == "notify":
            title = body.get("title", "Tickr") if isinstance(body, (dict, Cocoa.NSDictionary)) else "Tickr"
            msg = body.get("message", "") if isinstance(body, (dict, Cocoa.NSDictionary)) else ""
            send_native_notification(title, msg)

        elif action == "publish":
            if data is not None:
                tasks_list = json.loads(data) if isinstance(data, str) else list(data)
                save_tasks_to_disk(tasks_list)
            
            try:
                cmd = f"cd {DIARY_DIR} && git add src/data/diary.json && git commit -m 'chore(diary): sync completed tasks from Tickr ⚡' && git push origin main"
                proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                stdout, stderr = proc.communicate()
                
                send_native_notification("🚀 Live Deployed", "Your completed tasks are now live on esawi.dev/diary")
                
                if app_delegate and app_delegate.webView:
                    app_delegate.webView.evaluateJavaScript_completionHandler_("if(window.onPublishSuccess) onPublishSuccess();", None)
            except Exception as e:
                print("Publish error:", e)

        elif action == "quit":
            Cocoa.NSApplication.sharedApplication().terminate_(None)

class AppDelegate(Cocoa.NSObject):
    def applicationDidFinishLaunching_(self, notification):
        Cocoa.NSApp().setActivationPolicy_(Cocoa.NSApplicationActivationPolicyAccessory)
        self.active_timer_text = ""

        # Status Bar Item in Menu Bar
        self.statusItem = Cocoa.NSStatusBar.systemStatusBar().statusItemWithLength_(Cocoa.NSVariableStatusItemLength)
        button = self.statusItem.button()

        if os.path.exists(ICON_PATH):
            icon_img = Cocoa.NSImage.alloc().initWithContentsOfFile_(ICON_PATH)
            if icon_img:
                icon_img.setSize_(Cocoa.NSMakeSize(18, 18))
                button.setImage_(icon_img)
                button.setImagePosition_(Cocoa.NSImageLeft)

        button.setTarget_(self)
        button.setAction_(objc.selector(self.togglePopover_, signature=b"v@:@"))

        # WKWebView Configuration
        contentController = WebKit.WKUserContentController.alloc().init()
        self.handler = ScriptHandler.alloc().init()
        contentController.addScriptMessageHandler_name_(self.handler, "tickr")

        config = WebKit.WKWebViewConfiguration.alloc().init()
        config.setUserContentController_(contentController)

        frame = Cocoa.NSMakeRect(0, 0, 320, 210)
        self.webView = WebKit.WKWebView.alloc().initWithFrame_configuration_(frame, config)
        self.webView.setValue_forKey_(False, "drawsBackground")

        file_url = Cocoa.NSURL.fileURLWithPath_(UI_HTML_PATH)
        self.webView.loadFileURL_allowingReadAccessToURL_(file_url, file_url.URLByDeletingLastPathComponent())

        tasks = load_tasks_from_disk()
        tags = load_tags()
        autostart = is_launch_at_login()
        note = load_note()
        self.update_badge_count(tasks)
        
        tasks_json = json.dumps(tasks)
        tags_json = json.dumps(tags)
        note_json = json.dumps(note)
        js_code = f"setTimeout(function() {{ if(window.initAppState) initAppState({tasks_json}, {tags_json}, {json.dumps(autostart)}, {note_json}); }}, 350);"
        self.webView.evaluateJavaScript_completionHandler_(js_code, None)

        self.popover = Cocoa.NSPopover.alloc().init()
        self.popover.setContentSize_(Cocoa.NSMakeSize(320, 210))
        self.popover.setBehavior_(Cocoa.NSPopoverBehaviorTransient)
        self.popover.setAnimates_(True)

        viewController = Cocoa.NSViewController.alloc().init()
        viewController.setView_(self.webView)
        self.popover.setContentViewController_(viewController)

        self.setup_global_hotkeys()

    def setup_global_hotkeys(self):
        def handle_global_event(event):
            flags = event.modifierFlags()
            chars = event.charactersIgnoringModifiers()
            
            is_cmd = bool(flags & Cocoa.NSEventModifierFlagCommand)
            is_shift = bool(flags & Cocoa.NSEventModifierFlagShift)
            is_opt = bool(flags & Cocoa.NSEventModifierFlagOption)
            
            if is_cmd and is_shift and (chars and chars.lower() == 't'):
                self.togglePopover_(None)
            elif is_opt and (chars and chars == ' '):
                self.togglePopover_(None)

        Cocoa.NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(Cocoa.NSEventMaskKeyDown, handle_global_event)
        Cocoa.NSEvent.addLocalMonitorForEventsMatchingMask_handler_(Cocoa.NSEventMaskKeyDown, lambda event: (handle_global_event(event), event)[1])

    def update_timer_display(self, time_text):
        self.active_timer_text = time_text
        tasks = load_tasks_from_disk()
        self.update_badge_count(tasks)

    def update_badge_count(self, tasks):
        button = self.statusItem.button()
        if not button:
            return
        
        if self.active_timer_text:
            button.setTitle_(f" {self.active_timer_text}")
        else:
            active = sum(1 for t in tasks if not t.get("done", False))
            if active > 0:
                button.setTitle_(f" {active}")
            else:
                button.setTitle_("")

    def togglePopover_(self, sender):
        button = self.statusItem.button()
        if self.popover.isShown():
            self.popover.performClose_(sender)
        else:
            tasks = load_tasks_from_disk()
            tags = load_tags()
            autostart = is_launch_at_login()
            note = load_note()
            tasks_json = json.dumps(tasks)
            tags_json = json.dumps(tags)
            note_json = json.dumps(note)
            self.webView.evaluateJavaScript_completionHandler_(f"if(window.initAppState) initAppState({tasks_json}, {tags_json}, {json.dumps(autostart)}, {note_json});", None)
            self.popover.showRelativeToRect_ofView_preferredEdge_(button.bounds(), button, Cocoa.NSMinYEdge)
            Cocoa.NSApp().activateIgnoringOtherApps_(True)

def main():
    app = Cocoa.NSApplication.sharedApplication()
    delegate = AppDelegate.alloc().init()
    app.setDelegate_(delegate)
    app.run()

if __name__ == "__main__":
    main()
