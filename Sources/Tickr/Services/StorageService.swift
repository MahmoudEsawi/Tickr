import Foundation

public final class StorageService: @unchecked Sendable {
    public static let shared = StorageService()

    private let fileManager = FileManager.default
    private let fileName = "tasks.json"

    private var appSupportURL: URL {
        let paths = fileManager.urls(for: .applicationSupportDirectory, in: .userDomainMask)
        let appDirectory = paths[0].appendingPathComponent("Tickr", isDirectory: true)
        
        if !fileManager.fileExists(atPath: appDirectory.path) {
            try? fileManager.createDirectory(at: appDirectory, withIntermediateDirectories: true)
        }
        return appDirectory
    }

    private var fileURL: URL {
        appSupportURL.appendingPathComponent(fileName)
    }

    private init() {}

    public func loadTasks() -> [TaskItem] {
        guard fileManager.fileExists(atPath: fileURL.path) else {
            return defaultTasks()
        }

        do {
            let data = try Data(contentsOf: fileURL)
            let decoder = JSONDecoder()
            decoder.dateDecodingStrategy = .iso8601
            return try decoder.decode([TaskItem].self, from: data)
        } catch {
            print("Failed to load tasks: \(error)")
            return defaultTasks()
        }
    }

    public func saveTasks(_ tasks: [TaskItem]) {
        do {
            let encoder = JSONEncoder()
            encoder.outputFormatting = .prettyPrinted
            encoder.dateEncodingStrategy = .iso8601
            let data = try encoder.encode(tasks)
            try data.write(to: fileURL, options: [.atomicWrite])
        } catch {
            print("Failed to save tasks: \(error)")
        }
    }

    private func defaultTasks() -> [TaskItem] {
        return [
            TaskItem(title: "Welcome to Tickr! ⚡", category: .general),
            TaskItem(title: "Click the checkbox to complete a task", category: .ideas),
            TaskItem(title: "Press ↵ to quickly add tasks", category: .work),
            TaskItem(title: "Filter by status or color categories above", category: .personal)
        ]
    }
}
