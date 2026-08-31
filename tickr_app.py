#!/usr/bin/env python3
"""
Tickr macOS Native Menu Bar Daemon
PyObjC AppKit + WebKit hybrid runtime with IPC message routing.
"""
import sys
import os
import json
import datetime
import subprocess
import Cocoa
import WebKit
import objc

# System Paths
DIARY_DIR = os.path.expanduser("~/Projects/esawi.dev")
DIARY_PATH = os.path.join(DIARY_DIR, "src/data/diary.json")
BACKUP_DIR = os.path.expanduser("~/Library/Application Support/Tickr")
BACKUP_FILE = os.path.join(BACKUP_DIR, "tasks.json")
TAGS_FILE = os.path.join(BACKUP_DIR, "tags.json")
NOTES_HISTORY_FILE = os.path.join(BACKUP_DIR, "notes_history.json")
LAUNCH_AGENT_PATH = os.path.expanduser("~/Library/LaunchAgents/com.mahmoudesawi.tickr.plist")
ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
ICON_PATH = os.path.join(ASSETS_DIR, "menu_icon.png")
UI_HTML_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui", "index.html")

DEFAULT_TAGS = ["PROJECT", "CODE", "HACKATHON", "DAILY", "IDEAS"]

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
    return DEFAULT_TAGS

def save_tags(tags):
    try:
        os.makedirs(BACKUP_DIR, exist_ok=True)
        with open(TAGS_FILE, "w", encoding="utf-8") as f:
            json.dump(tags, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print("Save tags error:", e)

def load_notes_history():
    if os.path.exists(NOTES_HISTORY_FILE):
        try:
            with open(NOTES_HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def save_notes_history(notes):
    try:
        os.makedirs(BACKUP_DIR, exist_ok=True)
        with open(NOTES_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(notes, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print("Save notes error:", e)

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
    """Handles WebKit JS -> Python IPC actions via clean dispatcher."""

    def userContentController_didReceiveScriptMessage_(self, userContentController, message):
        body = message.body()
        payload = {}

        if isinstance(body, (dict, Cocoa.NSDictionary)):
            payload = dict(body)
        elif isinstance(body, str):
            try:
                payload = json.loads(body)
            except Exception:
                pass

        action = payload.get("action")
        app_delegate = Cocoa.NSApp().delegate()

        # Handle custom tags update if present
        tags = payload.get("tags")
        if tags:
            tags_list = json.loads(tags) if isinstance(tags, str) else list(tags)
            save_tags(tags_list)

        # Action Dispatcher Map
        dispatch_table = {
            "save": lambda: self._handle_save(payload.get("data"), app_delegate),
            "save_notes_history": lambda: self._handle_save_notes(payload.get("notes")),
            "timer_update": lambda: app_delegate.update_timer_display(payload.get("text", "")) if app_delegate else None,
            "set_autostart": lambda: set_launch_at_login(payload.get("enabled", False)),
            "notify": lambda: send_native_notification(payload.get("title", "Tickr"), payload.get("message", "")),
            "open_url": lambda: self._handle_open_url(payload.get("url", "")),
            "toggle_pin": lambda: app_delegate.toggle_pin() if app_delegate else None,
            "publish": lambda: self._handle_publish(payload.get("data"), app_delegate),
            "quit": lambda: Cocoa.NSApplication.sharedApplication().terminate_(None)
        }

        handler = dispatch_table.get(action)
        if handler:
            try:
                handler()
            except Exception as e:
                print(f"Error handling action '{action}':", e)

    def _handle_save(self, data, app_delegate):
        if data is not None:
            tasks_list = json.loads(data) if isinstance(data, str) else list(data)
            save_tasks_to_disk(tasks_list)
            if app_delegate:
                app_delegate.update_badge_count(tasks_list)

    def _handle_save_notes(self, notes):
        if notes is not None:
            notes_list = json.loads(notes) if isinstance(notes, str) else list(notes)
            save_notes_history(notes_list)

    def _handle_open_url(self, url_str):
        if url_str:
            Cocoa.NSWorkspace.sharedWorkspace().openURL_(Cocoa.NSURL.URLWithString_(url_str))

    def _handle_publish(self, data, app_delegate):
        if data is not None:
            tasks_list = json.loads(data) if isinstance(data, str) else list(data)
            save_tasks_to_disk(tasks_list)

        if os.path.exists(DIARY_DIR):
            try:
                subprocess.run(["git", "add", "src/data/diary.json"], cwd=DIARY_DIR, check=True)
                subprocess.run(["git", "commit", "-m", "chore(diary): sync completed tasks from Tickr ⚡"], cwd=DIARY_DIR, check=False)
                subprocess.run(["git", "push", "origin", "main"], cwd=DIARY_DIR, check=True)
                
                send_native_notification("Live Deployed", "Your completed tasks are now live on esawi.dev/diary")
                
                if app_delegate and app_delegate.webView:
                    app_delegate.webView.evaluateJavaScript_completionHandler_("if(window.onPublishSuccess) onPublishSuccess();", None)
            except Exception as e:
                print("Publish error:", e)

class AppDelegate(Cocoa.NSObject):
    def applicationDidFinishLaunching_(self, notification):
        Cocoa.NSApp().setActivationPolicy_(Cocoa.NSApplicationActivationPolicyAccessory)
        self.active_timer_text = ""
        self.is_pinned = False

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

        frame = Cocoa.NSMakeRect(0, 0, 360, 420)
        self.webView = WebKit.WKWebView.alloc().initWithFrame_configuration_(frame, config)
        self.webView.setValue_forKey_(False, "drawsBackground")

        file_url = Cocoa.NSURL.fileURLWithPath_(UI_HTML_PATH)
        self.webView.loadFileURL_allowingReadAccessToURL_(file_url, file_url.URLByDeletingLastPathComponent())

        tasks = load_tasks_from_disk()
        tags = load_tags()
        notes_history = load_notes_history()
        autostart = is_launch_at_login()
        self.update_badge_count(tasks)
        
        tasks_json = json.dumps(tasks)
        tags_json = json.dumps(tags)
        notes_json = json.dumps(notes_history)
        js_code = f"setTimeout(function() {{ if(window.initAppState) initAppState({tasks_json}, {tags_json}, {json.dumps(autostart)}, {notes_json}, {json.dumps(self.is_pinned)}); }}, 350);"
        self.webView.evaluateJavaScript_completionHandler_(js_code, None)

        self.popover = Cocoa.NSPopover.alloc().init()
        self.popover.setContentSize_(Cocoa.NSMakeSize(360, 420))
        self.popover.setBehavior_(Cocoa.NSPopoverBehaviorTransient)
        self.popover.setAnimates_(True)

        viewController = Cocoa.NSViewController.alloc().init()
        viewController.setView_(self.webView)
        self.popover.setContentViewController_(viewController)

        self.setup_global_hotkeys()

    def toggle_pin(self):
        self.is_pinned = not self.is_pinned
        win = self.webView.window()

        if self.is_pinned:
            self.popover.setBehavior_(Cocoa.NSPopoverBehaviorApplicationDefined)
            if win:
                win.setLevel_(Cocoa.NSFloatingWindowLevel)
                win.setHidesOnDeactivate_(False)
                win.setCollectionBehavior_(Cocoa.NSWindowCollectionBehaviorCanJoinAllSpaces | Cocoa.NSWindowCollectionBehaviorFullScreenAuxiliary)
            send_native_notification("📌 HUD Pinned", "Tickr is pinned and will stay floating on top.")
        else:
            self.popover.setBehavior_(Cocoa.NSPopoverBehaviorTransient)
            if win:
                win.setLevel_(Cocoa.NSNormalWindowLevel)
                win.setHidesOnDeactivate_(True)
            send_native_notification("HUD Unpinned", "Tickr returned to standard auto-dismiss.")

        if self.webView:
            self.webView.evaluateJavaScript_completionHandler_(f"if(window.onPinStateChanged) onPinStateChanged({json.dumps(self.is_pinned)});", None)

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
            notes_history = load_notes_history()
            autostart = is_launch_at_login()
            tasks_json = json.dumps(tasks)
            tags_json = json.dumps(tags)
            notes_json = json.dumps(notes_history)
            self.webView.evaluateJavaScript_completionHandler_(f"if(window.initAppState) initAppState({tasks_json}, {tags_json}, {json.dumps(autostart)}, {notes_json}, {json.dumps(self.is_pinned)});", None)
            self.popover.showRelativeToRect_ofView_preferredEdge_(button.bounds(), button, Cocoa.NSMinYEdge)
            
            win = self.webView.window()
            if win and self.is_pinned:
                win.setLevel_(Cocoa.NSFloatingWindowLevel)
                win.setHidesOnDeactivate_(False)
                win.setCollectionBehavior_(Cocoa.NSWindowCollectionBehaviorCanJoinAllSpaces | Cocoa.NSWindowCollectionBehaviorFullScreenAuxiliary)
            
            Cocoa.NSApp().activateIgnoringOtherApps_(True)

def main():
    app = Cocoa.NSApplication.sharedApplication()
    delegate = AppDelegate.alloc().init()
    app.setDelegate_(delegate)
    app.run()

if __name__ == "__main__":
    main()
