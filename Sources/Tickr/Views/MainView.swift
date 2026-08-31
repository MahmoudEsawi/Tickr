import SwiftUI

public struct MainView: View {
    @StateObject private var viewModel = TaskViewModel()

    public var body: some View {
        VStack(spacing: 0) {
            // Header Component
            HeaderView(viewModel: viewModel)

            Divider()

            // Quick Task Input Field
            HStack(spacing: 8) {
                // Category Picker Menu
                Menu {
                    ForEach(TaskCategory.allCases) { category in
                        Button(action: { viewModel.newTaskCategory = category }) {
                            Label(category.rawValue, systemImage: category.icon)
                        }
                    }
                } label: {
                    HStack(spacing: 4) {
                        Circle()
                            .fill(Color(hex: viewModel.newTaskCategory.colorHex))
                            .frame(width: 8, height: 8)
                        Image(systemName: "chevron.down")
                            .font(.system(size: 8))
                            .foregroundColor(.secondary)
                    }
                    .padding(.horizontal, 6)
                    .padding(.vertical, 5)
                    .background(Color.primary.opacity(0.05))
                    .cornerRadius(6)
                }
                .menuStyle(.borderlessButton)
                .fixedSize()

                // Text Input
                TextField("Add a quick task and press ↵", text: $viewModel.newTaskTitle)
                    .textFieldStyle(.plain)
                    .font(.system(size: 13))
                    .onSubmit {
                        viewModel.addTask()
                    }

                // Add Action Button
                if !viewModel.newTaskTitle.trimmingCharacters(in: .whitespaces).isEmpty {
                    Button(action: { viewModel.addTask() }) {
                        Image(systemName: "arrow.up.circle.fill")
                            .font(.system(size: 18))
                            .foregroundColor(.blue)
                    }
                    .buttonStyle(.plain)
                    .transition(.scale.combined(with: .opacity))
                }
            }
            .padding(.horizontal, 14)
            .padding(.vertical, 10)
            .background(Color.primary.opacity(0.02))

            Divider()

            // Task List / Scrollable Container
            if viewModel.filteredTasks.isEmpty {
                VStack(spacing: 10) {
                    Spacer()
                    Image(systemName: viewModel.searchQuery.isEmpty ? "sparkles" : "magnifyingglass")
                        .font(.system(size: 28))
                        .foregroundColor(.secondary.opacity(0.6))

                    Text(viewModel.searchQuery.isEmpty ? "All caught up! 🎉" : "No matching tasks found")
                        .font(.system(size: 13, weight: .medium))
                        .foregroundColor(.secondary)

                    if viewModel.searchQuery.isEmpty {
                        Text("Add a task above to keep your momentum.")
                            .font(.system(size: 11))
                            .foregroundColor(.secondary.opacity(0.7))
                    }
                    Spacer()
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
                .frame(height: 220)
            } else {
                ScrollView {
                    LazyVStack(spacing: 2) {
                        ForEach(viewModel.filteredTasks) { task in
                            TaskRowView(
                                task: task,
                                onToggle: { viewModel.toggleTask(id: task.id) },
                                onDelete: { viewModel.deleteTask(id: task.id) }
                            )
                        }
                    }
                    .padding(.vertical, 6)
                    .padding(.horizontal, 4)
                }
                .frame(height: 260)
            }

            Divider()

            // Footer Toolbar
            HStack {
                Text("\(viewModel.activeCount) active")
                    .font(.system(size: 11))
                    .foregroundColor(.secondary)

                Spacer()

                if viewModel.completedCount > 0 {
                    Button("Clear Done (\(viewModel.completedCount))") {
                        viewModel.clearCompleted()
                    }
                    .font(.system(size: 11))
                    .buttonStyle(.plain)
                    .foregroundColor(.secondary)
                    .onHover { inside in
                        if inside {
                            NSCursor.pointingHand.push()
                        } else {
                            NSCursor.pop()
                        }
                    }

                    Text("•")
                        .foregroundColor(.secondary.opacity(0.5))
                        .font(.system(size: 10))
                }

                Button("Quit") {
                    NSApplication.shared.terminate(nil)
                }
                .font(.system(size: 11))
                .buttonStyle(.plain)
                .foregroundColor(.secondary)
            }
            .padding(.horizontal, 14)
            .padding(.vertical, 8)
            .background(Color.primary.opacity(0.02))
        }
        .frame(width: 340)
        .background(.ultraThinMaterial)
    }
}
