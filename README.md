<div align="center">

# ⚡ Tickr for Mac

### **Minimalist Menu Bar To-Do List & Quick-Capture Engine for macOS**

[![Swift 6.0](https://img.shields.io/badge/Swift-6.0-F05138.svg?logo=swift&logoColor=white)](https://swift.org)
[![Platform: macOS 13+](https://img.shields.io/badge/Platform-macOS%2013%2B-black.svg?logo=apple&logoColor=white)](https://apple.com/macos)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-Welcome-brightgreen.svg)](https://github.com/MahmoudEsawi)

<p align="center">
  <b>A distraction-free, ultra-lightweight macOS Menu Bar to-do app. Keep your daily task list always one click away from your status bar.</b>
</p>

</div>

---

## ✨ Features

- 📌 **Always in Your Menu Bar**: Lives right in the macOS top status bar using native `MenuBarExtra`. No heavy windows cluttering your workspace.
- ⚡ **Instant Quick-Add**: Type your task and press <kbd>Return ↵</kbd> to add it instantly.
- 🎨 **Categorized & Color-Coded**: Organize tasks with colorful categories:
  - 🔵 **Work** (`#3B82F6`)
  - 🟢 **Personal** (`#10B981`)
  - 🔴 **Urgent** (`#EF4444`)
  - 🟣 **Ideas** (`#8B5CF6`)
  - ⚪ **General** (`#64748B`)
- 🔍 **Real-Time Search & Filtering**: Instant search and status tabs (`All`, `Active`, `Done`).
- 📊 **Visual Progress Bar**: Track your daily completion rate at a glance.
- 💾 **100% Offline & Private**: Tasks are saved automatically in `~/Library/Application Support/Tickr/tasks.json`.
- 🔋 **Zero Battery & Memory Impact**: Native SwiftUI implementation using < 20 MB of RAM.

---

## 🏗️ Architecture & Structure

```text
Tickr/
├── Package.swift               # Swift Package Manager configuration
├── Sources/
│   └── Tickr/
│       ├── Tickr.swift         # App entry point (@main & MenuBarExtra)
│       ├── Models/
│       │   └── TaskItem.swift  # Task data structure and Category definitions
│       ├── Services/
│       │   └── StorageService.swift # Atomic JSON persistence in Application Support
│       ├── ViewModels/
│       │   └── TaskViewModel.swift  # Observable state manager & filter logic
│       └── Views/
│           ├── ColorExtension.swift # Hex color utility
│           ├── HeaderView.swift     # Search bar, category pills, progress bar
│           ├── MainView.swift       # Main popover container & quick input
│           └── TaskRowView.swift    # Interactive row with checkbox & delete action
└── README.md
```

---

## 🚀 How to Run (Without Full Xcode!)

You can run and build Tickr directly from your terminal:

```bash
# 1. Navigate to the project directory
cd tickr

# 2. Run the application
swift run

# 3. Build a release binary
swift build -c release
```

---

## 📄 License

Distributed under the **MIT License**.
