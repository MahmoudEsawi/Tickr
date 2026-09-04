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
import html
import re
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
STICKY_HTML_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui", "sticky.html")

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

def markdown_to_notes_html(text):
    if not text:
        return "<div></div>"
    lines = text.splitlines()
    html_lines = []
    in_list = False
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append("<br>")
            continue
            
        # Checklists
        if stripped.startswith("- [ ] ") or stripped.startswith("* [ ] "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            item_text = html.escape(stripped[6:])
            html_lines.append(f"<div>☐ {item_text}</div>")
            continue
        elif stripped.startswith("- [x] ") or stripped.startswith("* [x] ") or stripped.startswith("- [X] ") or stripped.startswith("* [X] "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            item_text = html.escape(stripped[6:])
            html_lines.append(f"<div>☑ <strike>{item_text}</strike></div>")
            continue
            
        # Bullet list
        if stripped.startswith("- ") or stripped.startswith("* ") or stripped.startswith("• "):
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            item_text = html.escape(stripped[2:].strip())
            item_text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", item_text)
            item_text = re.sub(r"`(.+?)`", r"<code>\1</code>", item_text)
            html_lines.append(f"<li>{item_text}</li>")
            continue
            
        if in_list:
            html_lines.append("</ul>")
            in_list = False
            
        # Headings
        if stripped.startswith("### "):
            h_text = html.escape(stripped[4:])
            html_lines.append(f"<h3>{h_text}</h3>")
        elif stripped.startswith("## "):
            h_text = html.escape(stripped[3:])
            html_lines.append(f"<h2>{h_text}</h2>")
        elif stripped.startswith("# "):
            h_text = html.escape(stripped[2:])
            html_lines.append(f"<h1>{h_text}</h1>")
        else:
            line_html = html.escape(line)
            line_html = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", line_html)
            line_html = re.sub(r"`(.+?)`", r"<code>\1</code>", line_html)
            html_lines.append(f"<div>{line_html}</div>")
            
    if in_list:
        html_lines.append("</ul>")
        
    return "".join(html_lines)

def export_note_to_apple_notes(content, title=None):
    try:
        if not content and not title:
            return False
        
        body_html = markdown_to_notes_html(content)
        as_body = body_html.replace("\\", "\\\\").replace('"', '\\"')
        
        script = f'''
tell application "Notes"
    activate
    tell default account
        set newNote to make new note with properties {{body:"{as_body}"}}
        show newNote
    end tell
end tell
'''
        res = subprocess.run(["osascript", "-"], input=script, text=True, capture_output=True)
        if res.returncode == 0:
            send_native_notification("Exported to Notes", "Your note was successfully exported to Apple Notes.")
            return True
        else:
            print("Apple Notes export error:", res.stderr)
            return False
    except Exception as e:
        print("Apple Notes export exception:", e)
        return False

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
            "export_apple_notes": lambda: self._handle_export_notes(payload.get("content", ""), payload.get("title", ""), app_delegate),
            "pin_current_note": lambda: app_delegate.open_sticky_note(payload.get("noteId"), payload.get("content", ""), payload.get("title", ""), payload.get("theme", "system")) if app_delegate else None,
            "close_sticky_note": lambda: app_delegate.close_sticky_note() if app_delegate else None,
            "update_sticky_content": lambda: self._handle_update_sticky(payload, app_delegate),
            "start_sticky_drag": lambda: self._handle_start_sticky_drag(app_delegate),
            "move_sticky_window": lambda: self._handle_move_sticky(payload.get("dx", 0), payload.get("dy", 0), app_delegate),
            "timer_update": lambda: app_delegate.update_timer_display(payload.get("text", "")) if app_delegate else None,
            "set_autostart": lambda: set_launch_at_login(payload.get("enabled", False)),
            "notify": lambda: send_native_notification(payload.get("title", "Tickr"), payload.get("message", "")),
            "open_url": lambda: self._handle_open_url(payload.get("url", "")),
            "toggle_pin": lambda: app_delegate.toggle_pin_current_note() if app_delegate else None,
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

    def _handle_update_sticky(self, payload, app_delegate):
        note_id = str(payload.get("noteId", ""))
        content = payload.get("content", "")
        title = payload.get("title", "Untitled Note")

        notes = load_notes_history()
        now = datetime.datetime.now().isoformat()
        note = next((n for n in notes if str(n.get("id")) == note_id), None)
        if note:
            note["content"] = content
            note["title"] = title
            note["updatedAt"] = now
        else:
            notes.insert(0, {"id": note_id, "title": title, "content": content, "updatedAt": now})
        save_notes_history(notes)

        # Notify main HUD
        if app_delegate and app_delegate.webView:
            js = f"if(window.onExternalNoteUpdated) onExternalNoteUpdated({json.dumps(note_id)}, {json.dumps(title)}, {json.dumps(content)});"
            app_delegate.webView.evaluateJavaScript_completionHandler_(js, None)

    def _handle_start_sticky_drag(self, app_delegate):
        if app_delegate and app_delegate.sticky_panel:
            event = Cocoa.NSApp().currentEvent()
            if event:
                try:
                    app_delegate.sticky_panel.performWindowDragWithEvent_(event)
                except Exception:
                    pass

    def _handle_move_sticky(self, dx, dy, app_delegate):
        if app_delegate and app_delegate.sticky_panel:
            try:
                frame = app_delegate.sticky_panel.frame()
                new_x = frame.origin.x + float(dx)
                new_y = frame.origin.y - float(dy)
                app_delegate.sticky_panel.setFrameOrigin_(Cocoa.NSMakePoint(new_x, new_y))
            except Exception as e:
                pass

    def _handle_export_notes(self, content, title, app_delegate):
        success = export_note_to_apple_notes(content, title)
        if app_delegate and app_delegate.webView:
            js = f"if(window.onExportNotesResult) onExportNotesResult({json.dumps(success)});"
            app_delegate.webView.evaluateJavaScript_completionHandler_(js, None)

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
        self.pinned_note_id = None
        self.sticky_panel = None
        self.sticky_webView = None
        self.sticky_positioned = False

        self.setup_main_menu()

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

        # WKWebView Configuration for Main HUD
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

        self.popoverViewController = Cocoa.NSViewController.alloc().init()
        self.popoverViewController.setView_(self.webView)
        self.popover.setContentViewController_(self.popoverViewController)

        self.setup_global_hotkeys()

    def setup_main_menu(self):
        main_menu = Cocoa.NSMenu.alloc().init()

        # App Submenu
        app_menu_item = Cocoa.NSMenuItem.alloc().init()
        main_menu.addItem_(app_menu_item)
        app_menu = Cocoa.NSMenu.alloc().init()
        app_menu.addItemWithTitle_action_keyEquivalent_("About Tickr", "orderFrontStandardAboutPanel:", "")
        app_menu.addItem_(Cocoa.NSMenuItem.separatorItem())
        app_menu.addItemWithTitle_action_keyEquivalent_("Hide Tickr", "hide:", "h")
        app_menu.addItemWithTitle_action_keyEquivalent_("Hide Others", "hideOtherApplications:", "h")
        app_menu.addItemWithTitle_action_keyEquivalent_("Show All", "unhideAllApplications:", "")
        app_menu.addItem_(Cocoa.NSMenuItem.separatorItem())
        app_menu.addItemWithTitle_action_keyEquivalent_("Quit Tickr", "terminate:", "q")
        app_menu_item.setSubmenu_(app_menu)

        # Standard Edit Submenu: Enables Cmd+A, Cmd+C, Cmd+V, Cmd+X, Cmd+Z, Cmd+Shift+Z
        edit_menu_item = Cocoa.NSMenuItem.alloc().init()
        main_menu.addItem_(edit_menu_item)
        edit_menu = Cocoa.NSMenu.alloc().initWithTitle_("Edit")
        edit_menu.addItemWithTitle_action_keyEquivalent_("Undo", "undo:", "z")
        edit_menu.addItemWithTitle_action_keyEquivalent_("Redo", "redo:", "Z")
        edit_menu.addItem_(Cocoa.NSMenuItem.separatorItem())
        edit_menu.addItemWithTitle_action_keyEquivalent_("Cut", "cut:", "x")
        edit_menu.addItemWithTitle_action_keyEquivalent_("Copy", "copy:", "c")
        edit_menu.addItemWithTitle_action_keyEquivalent_("Paste", "paste:", "v")
        edit_menu.addItemWithTitle_action_keyEquivalent_("Select All", "selectAll:", "a")
        edit_menu_item.setSubmenu_(edit_menu)

        Cocoa.NSApp().setMainMenu_(main_menu)

    def setup_sticky_panel(self):
        if self.sticky_panel is not None:
            return

        self.sticky_panel = Cocoa.NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(
            Cocoa.NSMakeRect(100, 100, 310, 330),
            Cocoa.NSWindowStyleMaskBorderless | Cocoa.NSWindowStyleMaskNonactivatingPanel,
            Cocoa.NSBackingStoreBuffered,
            False
        )
        self.sticky_panel.setLevel_(Cocoa.NSFloatingWindowLevel)
        self.sticky_panel.setMovableByWindowBackground_(True)
        self.sticky_panel.setHasShadow_(True)
        self.sticky_panel.setOpaque_(False)
        self.sticky_panel.setBackgroundColor_(Cocoa.NSColor.clearColor())
        self.sticky_panel.setHidesOnDeactivate_(False)
        self.sticky_panel.setCollectionBehavior_(
            Cocoa.NSWindowCollectionBehaviorCanJoinAllSpaces | 
            Cocoa.NSWindowCollectionBehaviorFullScreenAuxiliary
        )

        contentController = WebKit.WKUserContentController.alloc().init()
        contentController.addScriptMessageHandler_name_(self.handler, "tickr")

        config = WebKit.WKWebViewConfiguration.alloc().init()
        config.setUserContentController_(contentController)

        frame = Cocoa.NSMakeRect(0, 0, 310, 330)
        self.sticky_webView = WebKit.WKWebView.alloc().initWithFrame_configuration_(frame, config)
        self.sticky_webView.setValue_forKey_(False, "drawsBackground")

        sticky_url = Cocoa.NSURL.fileURLWithPath_(STICKY_HTML_PATH)
        self.sticky_webView.loadFileURL_allowingReadAccessToURL_(sticky_url, sticky_url.URLByDeletingLastPathComponent())

        self.sticky_panel.setContentView_(self.sticky_webView)

    def open_sticky_note(self, note_id, content, title, theme="system"):
        self.setup_sticky_panel()
        self.pinned_note_id = str(note_id) if note_id else str(int(datetime.datetime.now().timestamp()*1000))

        if not self.sticky_positioned:
            screen_frame = Cocoa.NSScreen.mainScreen().visibleFrame()
            x = screen_frame.origin.x + screen_frame.size.width - 340
            y = screen_frame.origin.y + screen_frame.size.height - 380
            self.sticky_panel.setFrame_display_(Cocoa.NSMakeRect(x, y, 310, 330), True)
            self.sticky_positioned = True

        self.sticky_panel.makeKeyAndOrderFront_(None)
        Cocoa.NSApp().activateIgnoringOtherApps_(True)

        js = f"setTimeout(function() {{ if(window.initStickyNote) initStickyNote({json.dumps(self.pinned_note_id)}, {json.dumps(title)}, {json.dumps(content)}, {json.dumps(theme)}); }}, 200);"
        self.sticky_webView.evaluateJavaScript_completionHandler_(js, None)

        if self.webView:
            self.webView.evaluateJavaScript_completionHandler_(f"if(window.onNotePinChanged) onNotePinChanged({json.dumps(self.pinned_note_id)}, true);", None)

        send_native_notification("📌 Note Pinned", "Sticky note floating on desktop. Main Tickr remains active in menu bar!")

    def close_sticky_note(self):
        if self.sticky_panel:
            self.sticky_panel.orderOut_(None)
        old_id = self.pinned_note_id
        self.pinned_note_id = None
        if self.webView and old_id:
            self.webView.evaluateJavaScript_completionHandler_(f"if(window.onNotePinChanged) onNotePinChanged({json.dumps(old_id)}, false);", None)
        send_native_notification("Note Unpinned", "Sticky note closed.")

    def toggle_pin_current_note(self):
        if self.pinned_note_id and self.sticky_panel and self.sticky_panel.isVisible():
            self.close_sticky_note()
        else:
            if self.webView:
                self.webView.evaluateJavaScript_completionHandler_("if(window.triggerPinCurrentNote) triggerPinCurrentNote();", None)

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
            pinned_id = json.dumps(self.pinned_note_id)
            self.webView.evaluateJavaScript_completionHandler_(f"if(window.initAppState) initAppState({tasks_json}, {tags_json}, {json.dumps(autostart)}, {notes_json}, {pinned_id});", None)
            self.popover.showRelativeToRect_ofView_preferredEdge_(button.bounds(), button, Cocoa.NSMinYEdge)
            Cocoa.NSApp().activateIgnoringOtherApps_(True)

def main():
    app = Cocoa.NSApplication.sharedApplication()
    delegate = AppDelegate.alloc().init()
    app.setDelegate_(delegate)
    app.run()

if __name__ == "__main__":
    main()
