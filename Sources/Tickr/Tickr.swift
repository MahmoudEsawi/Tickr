import SwiftUI
import AppKit

final class AppDelegate: NSObject, NSApplicationDelegate {
    func applicationDidFinishLaunching(_ notification: Notification) {
        // Set as an accessory app (Menu bar app without dock clutter)
        NSApplication.shared.setActivationPolicy(.accessory)
    }
}

@main
struct TickrApp: App {
    @NSApplicationDelegateAdaptor(AppDelegate.self) var appDelegate

    var body: some Scene {
        MenuBarExtra("Tickr", systemImage: "checklist") {
            MainView()
        }
        .menuBarExtraStyle(.window)
    }
}
