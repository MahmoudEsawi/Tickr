import SwiftUI

public struct TaskRowView: View {
    let task: TaskItem
    let onToggle: () -> Void
    let onDelete: () -> Void

    @State private var isHovered = false

    public var body: some View {
        HStack(spacing: 12) {
            // Checkbox button
            Button(action: onToggle) {
                ZStack {
                    Circle()
                        .stroke(task.isCompleted ? Color.green : Color.secondary.opacity(0.4), lineWidth: 1.5)
                        .frame(width: 18, height: 18)

                    if task.isCompleted {
                        Circle()
                            .fill(Color.green)
                            .frame(width: 12, height: 12)
                        
                        Image(systemName: "checkmark")
                            .font(.system(size: 8, weight: .bold))
                            .foregroundColor(.white)
                    }
                }
            }
            .buttonStyle(.plain)

            // Title & Category tag
            VStack(alignment: .leading, spacing: 3) {
                Text(task.title)
                    .font(.system(size: 13, weight: task.isCompleted ? .regular : .medium))
                    .strikethrough(task.isCompleted, color: .secondary)
                    .foregroundColor(task.isCompleted ? .secondary : .primary)
                    .lineLimit(2)

                HStack(spacing: 6) {
                    Circle()
                        .fill(Color(hex: task.category.colorHex))
                        .frame(width: 6, height: 6)

                    Text(task.category.rawValue)
                        .font(.system(size: 10, weight: .medium))
                        .foregroundColor(.secondary)
                }
            }

            Spacer()

            // Delete button (reveals on hover)
            if isHovered {
                Button(action: onDelete) {
                    Image(systemName: "xmark.circle.fill")
                        .foregroundColor(.secondary.opacity(0.8))
                        .font(.system(size: 14))
                }
                .buttonStyle(.plain)
                .transition(.opacity.combined(with: .scale))
            }
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 8)
        .background(
            RoundedRectangle(cornerRadius: 8)
                .fill(isHovered ? Color.primary.opacity(0.04) : Color.clear)
        )
        .contentShape(Rectangle())
        .onHover { hovering in
            withAnimation(.easeInOut(duration: 0.15)) {
                isHovered = hovering
            }
        }
    }
}
