# ⚡ Tickr Technical Architecture & Comprehensive Guide

This document provides in-depth technical documentation, architecture specifications, API references, and developer workflows for **Tickr**.

---

## 🏗️ System Architecture

Tickr is engineered as a hybrid native macOS application. It combines native **Cocoa AppKit** status bar life-cycle management with high-performance hardware-accelerated **WebKit (WKWebView)** UI rendering.

```mermaid
graph TD
    User([macOS User]) -->|Global Hotkey ⌥Space / ⌘⇧T| NSApp[AppKit NSApplication]
    User -->|Click Status Icon| StatusItem[NSStatusItem / Menu Bar]
    
    subgraph Native Cocoa Runtime (PyObjC)
        StatusItem --> Popover[NSPopover HUD]
        NSApp --> KeyMonitor[NSEvent Global Monitor]
        Popover --> WebContainer[WKWebView Container]
        ScriptHandler[WKScriptMessageHandler] <-->|Bidirectional IPC| WebContainer
    end

    subgraph Audio Synthesis Engine
        WebContainer --> WebAudio[Web Audio API]
        WebAudio --> Oscillators[Crown Ticks & Snaps]
        WebAudio --> NoiseBuffer[Synthesized Rain Generator]
    end

    subgraph Data & Sync Layer
        ScriptHandler --> LocalStore[~/Library/Application Support/Tickr/]
        LocalStore --> TasksJSON[tasks.json]
        LocalStore --> NotesJSON[notes_history.json]
        LocalStore --> SettingsJSON[tags.json / Sound prefs]
        ScriptHandler --> DiarySync[esawi.dev/src/data/diary.json]
        DiarySync --> GitDeploy[Git Commit & Push -> Vercel CI/CD]
    end

    subgraph CLI Companion
        Terminal([Terminal / Raycast / Alfred]) --> CLI[cli.py]
        CLI <--> TasksJSON
    end
```

---

## 💻 Native macOS Integration (PyObjC)

### 1. Status Bar Item (`NSStatusItem`)
* Configured with `NSVariableStatusItemLength` to accommodate dynamic Pomodoro countdown timers and pending task badge counters (` 3`, ` 24:15`).
* Uses Retina `@2x` template icons (`assets/menu_icon.png`).

### 2. Floating Window Level Pinning
Tickr supports keeping the HUD floating on top of all macOS applications without auto-dismissing:
```python
if self.is_pinned:
    self.popover.setBehavior_(Cocoa.NSPopoverBehaviorApplicationDefined)
    win = self.webView.window()
    if win:
        win.setLevel_(Cocoa.NSFloatingWindowLevel)
        win.setHidesOnDeactivate_(False)
        win.setCollectionBehavior_(
            Cocoa.NSWindowCollectionBehaviorCanJoinAllSpaces | 
            Cocoa.NSWindowCollectionBehaviorFullScreenAuxiliary
        )
```

### 3. Global Hotkey Event Tap
Tickr registers both global and local key monitors using `NSEvent.addGlobalMonitorForEventsMatchingMask_handler_`:
* <kbd>⌘</kbd> + <kbd>⇧</kbd> + <kbd>T</kbd> / <kbd>⌥</kbd> + <kbd>Space</kbd>: Instant HUD summon.

---

## 🔊 Web Audio Synthesis Engine

Tickr features a 100% synthesized sound design engine built on the **Web Audio API** (zero external MP3/WAV assets):

1. **Mechanical Digital Crown Clicks**:
   * Synthesized using a `triangle` oscillator with rapid exponential frequency drop ($1400\text{ Hz} \rightarrow 180\text{ Hz}$ over $15\text{ ms}$).
2. **Task Completion Snap**:
   * Fast frequency ramp ($580\text{ Hz} \rightarrow 880\text{ Hz}$ over $80\text{ ms}$) creating a satisfying haptic snap.
3. **Ambient Focus Rain Generator**:
   * Continuous procedural pink noise algorithm passed through a $800\text{ Hz}$ lowpass `BiquadFilterNode`.

---

## ⌨️ CLI Companion Tool (`cli.py`)

Tickr includes a standalone command-line interface located at [`cli.py`](file:///Users/airm2/my-green-graph/tickr/cli.py):

### Commands
```bash
# Add a new task
./cli.py add "Refactor auth middleware" --tag CODE

# List pending & completed tasks
./cli.py list

# Generate markdown daily standup summary
./cli.py standup
```

### Raycast & Alfred Integration
You can link `cli.py` to Raycast Script Commands or Alfred Workflows for instant capture from your launcher.

---

## 📦 Build & Release Automation (`package.sh`)

To bundle a production `.app` and generate DMG installers:

```bash
chmod +x package.sh
./package.sh
```

### Build Steps:
1. **Bundle App Structure**: Assembles `Tickr.app/Contents/MacOS/Tickr`, `Info.plist`, `Resources/AppIcon.icns`.
2. **Code Signing**: Applies ad-hoc signature via `codesign --force --deep --sign - Tickr.app`.
3. **Distribution Assets**:
   * `dist/Tickr-v1.0.0-macOS.zip`
   * `dist/Tickr-v1.0.0.dmg` (built with `create-dmg` / `hdiutil`)

---

## 🍺 Homebrew Cask Formula

The Cask definition is located at [`Casks/tickr.rb`](file:///Users/airm2/my-green-graph/tickr/Casks/tickr.rb):

```ruby
cask "tickr" do
  version "1.0.0"
  sha256 "f160b13970b5f5ddae7ce51a8ba929f6487e452a22be1fb71d9d1a9da9600e5a"

  url "https://github.com/MahmoudEsawi/Tickr/releases/download/v#{version}/Tickr-v#{version}-macOS.zip"
  name "Tickr"
  desc "Minimalist macOS menu bar task engine, Pomodoro timer & scratchpad"
  homepage "https://github.com/MahmoudEsawi/Tickr"

  app "Tickr.app"

  zap trash: [
    "~/Library/Application Support/Tickr",
    "~/Library/LaunchAgents/com.mahmoudesawi.tickr.plist",
  ]
end
```

---

## 🛠️ Troubleshooting & FAQ

### 1. Gatekeeper: "Tickr cannot be opened because Apple cannot check it for malicious software"
Tickr is open-source and ad-hoc signed. To allow execution:
```bash
xattr -cr /Applications/Tickr.app
```
*Or:* Right-click `Tickr.app` in Finder $\rightarrow$ select **Open** $\rightarrow$ click **Open**.

### 2. Autostart at Boot Not Triggering
Verify the launch agent plist exists:
```bash
cat ~/Library/LaunchAgents/com.mahmoudesawi.tickr.plist
```
To manually reload:
```bash
launchctl unload ~/Library/LaunchAgents/com.mahmoudesawi.tickr.plist
launchctl load ~/Library/LaunchAgents/com.mahmoudesawi.tickr.plist
```

---

## 👨‍💻 Developer & Maintainer

**Mahmoud Al-Esawi**
* Website: [esawi.dev](https://esawi.dev)
* GitHub: [@MahmoudEsawi](https://github.com/MahmoudEsawi)
* Live Diary: [esawi.dev/diary](https://esawi.dev/diary)
