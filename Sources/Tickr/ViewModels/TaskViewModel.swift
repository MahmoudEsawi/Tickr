import Foundation
import SwiftUI
import Combine

public enum TaskFilterStatus: String, CaseIterable, Identifiable {
    case all = "All"
    case active = "Active"
    case completed = "Done"

    public var id: String { rawValue }
}

@MainActor
public final class TaskViewModel: ObservableObject {
    @Published public var tasks: [TaskItem] = [] {
        didSet {
            StorageService.shared.saveTasks(tasks)
        }
    }

    @Published public var filterStatus: TaskFilterStatus = .all
    @Published public var selectedCategory: TaskCategory? = nil
    @Published public var searchQuery: String = ""
    @Published public var newTaskTitle: String = ""
    @Published public var newTaskCategory: TaskCategory = .general

    public init() {
        self.tasks = StorageService.shared.loadTasks()
    }

    public var filteredTasks: [TaskItem] {
        tasks.filter { task in
            // Filter by status
            switch filterStatus {
            case .all:
                break
            case .active:
                guard !task.isCompleted else { return false }
            case .completed:
                guard task.isCompleted else { return false }
            }

            // Filter by category
            if let selectedCategory = selectedCategory {
                guard task.category == selectedCategory else { return false }
            }

            // Filter by search query
            if !searchQuery.trimmingCharacters(in: .whitespaces).isEmpty {
                guard task.title.localizedCaseInsensitiveContains(searchQuery) else { return false }
            }

            return true
        }
    }

    public var activeCount: Int {
        tasks.filter { !$0.isCompleted }.count
    }

    public var completedCount: Int {
        tasks.filter { $0.isCompleted }.count
    }

    public func addTask() {
        let trimmed = newTaskTitle.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return }

        let newTask = TaskItem(title: trimmed, category: newTaskCategory)
        withAnimation(.spring(response: 0.35, dampingFraction: 0.7)) {
            tasks.insert(newTask, at: 0)
        }
        newTaskTitle = ""
    }

    public func toggleTask(id: UUID) {
        guard let index = tasks.firstIndex(where: { $0.id == id }) else { return }
        withAnimation(.spring(response: 0.3, dampingFraction: 0.7)) {
            tasks[index].isCompleted.toggle()
            tasks[index].completedAt = tasks[index].isCompleted ? Date() : nil
        }
    }

    public func deleteTask(id: UUID) {
        withAnimation(.easeOut(duration: 0.2)) {
            tasks.removeAll { $0.id == id }
        }
    }

    public func clearCompleted() {
        withAnimation(.easeOut(duration: 0.25)) {
            tasks.removeAll { $0.isCompleted }
        }
    }
}
