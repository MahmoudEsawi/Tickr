import Foundation

public enum TaskCategory: String, CaseIterable, Codable, Identifiable {
    case general = "General"
    case work = "Work"
    case personal = "Personal"
    case urgent = "Urgent"
    case ideas = "Ideas"

    public var id: String { rawValue }

    public var icon: String {
        switch self {
        case .general: return "tray.fill"
        case .work: return "briefcase.fill"
        case .personal: return "person.fill"
        case .urgent: return "exclamationmark.triangle.fill"
        case .ideas: return "lightbulb.fill"
        }
    }

    public var colorHex: String {
        switch self {
        case .general: return "#64748B"
        case .work: return "#3B82F6"
        case .personal: return "#10B981"
        case .urgent: return "#EF4444"
        case .ideas: return "#8B5CF6"
        }
    }
}

public struct TaskItem: Identifiable, Codable, Equatable {
    public var id: UUID
    public var title: String
    public var isCompleted: Bool
    public var category: TaskCategory
    public var createdAt: Date
    public var completedAt: Date?

    public init(
        id: UUID = UUID(),
        title: String,
        isCompleted: Bool = false,
        category: TaskCategory = .general,
        createdAt: Date = Date(),
        completedAt: Date? = nil
    ) {
        self.id = id
        self.title = title
        self.isCompleted = isCompleted
        self.category = category
        self.createdAt = createdAt
        self.completedAt = completedAt
    }
}
