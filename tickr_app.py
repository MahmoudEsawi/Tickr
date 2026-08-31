#!/usr/bin/env python3
import sys
import os
import json
import Cocoa
import WebKit
import objc

STORAGE_DIR = os.path.expanduser("~/Library/Application Support/Tickr")
STORAGE_FILE = os.path.join(STORAGE_DIR, "tasks.json")
UI_HTML_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui", "index.html")

def load_tasks_from_disk():
    if not os.path.exists(STORAGE_DIR):
        os.makedirs(STORAGE_DIR, exist_ok=True)
    if os.path.exists(STORAGE_FILE):
        try:
            with open(STORAGE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return [
        {"id": 1, "title": "Welcome to Tickr for Mac! ⚡", "category": "Ship", "done": False},
        {"id": 2, "title": "Click any task to check it off with sound ✨", "category": "Focus", "done": False},
        {"id": 3, "title": "Hit ↵ Enter to quickly add new tasks", "category": "Flow", "done": False}
    ]

def save_tasks_to_disk(tasks):
    try:
        with open(STORAGE_FILE, "w", encoding="utf-8") as f:
            json.dump(tasks, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print("Save error:", e)

class ScriptHandler(Cocoa.NSObject):
    def userContentController_didReceiveScriptMessage_(self, userContentController, message):
        body = message.body()
        if isinstance(body, (dict, Cocoa.NSDictionary)):
            action = body.get("action")
            if action == "save":
                data = body.get("data")
                if data is not None:
                    # Convert objc types if needed
                    py_data = json.loads(json.dumps(data)) if not isinstance(data, list) else list(data)
                    save_tasks_to_disk(py_data)
                    app_delegate = Cocoa.NSApp().delegate()
                    if app_delegate:
                        app_delegate.update_badge_count(py_data)
            elif action == "quit":
                Cocoa.NSApplication.sharedApplication().terminate_(None)

class AppDelegate(Cocoa.NSObject):
    def applicationDidFinishLaunching_(self, notification):
        Cocoa.NSApp().setActivationPolicy_(Cocoa.NSApplicationActivationPolicyAccessory)

        # Status Bar Item
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
        config.preferences().setValue_forKey_(True, "developerExtrasEnabled")

        # Create WKWebView
        frame = Cocoa.NSMakeRect(0, 0, 360, 480)
        self.webView = WebKit.WKWebView.alloc().initWithFrame_configuration_(frame, config)
        self.webView.setValue_forKey_(False, "drawsBackground")

        # Load HTML
        file_url = Cocoa.NSURL.fileURLWithPath_(UI_HTML_PATH)
        self.webView.loadFileURL_allowingReadAccessToURL_(file_url, file_url.URLByDeletingLastPathComponent())

        # Load initial tasks on finish
        tasks = load_tasks_from_disk()
        self.update_badge_count(tasks)
        tasks_json = json.dumps(tasks)
        js_code = f"setTimeout(function() {{ if(window.initTasks) initTasks({tasks_json}); }}, 300);"
        self.webView.evaluateJavaScript_completionHandler_(js_code, None)

        # Popover
        self.popover = Cocoa.NSPopover.alloc().init()
        self.popover.setContentSize_(Cocoa.NSMakeSize(360, 480))
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
            # Refresh data
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
