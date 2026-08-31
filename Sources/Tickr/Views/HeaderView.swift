import SwiftUI

public struct HeaderView: View {
    @ObservedObject var viewModel: TaskViewModel

    public var body: some View {
        VStack(spacing: 12) {
            // App Title & Counters
            HStack {
                HStack(spacing: 8) {
                    Image(systemName: "checkmark.circle.badge.questionmark.fill")
                        .symbolRenderingMode(.hierarchical)
                        .font(.system(size: 18, weight: .semibold))
                        .foregroundColor(.blue)

                    Text("Tickr")
                        .font(.system(size: 15, weight: .bold, design: .rounded))

                    Text("for Mac")
                        .font(.system(size: 11, weight: .medium))
                        .foregroundColor(.secondary)
                }

                Spacer()

                // Progress Badge
                HStack(spacing: 4) {
                    Text("\(viewModel.completedCount)/\(viewModel.tasks.count)")
                        .font(.system(size: 11, weight: .semibold, design: .monospaced))
                        .foregroundColor(.secondary)

                    if !viewModel.tasks.isEmpty {
                        ProgressView(value: Double(viewModel.completedCount), total: Double(viewModel.tasks.count))
                            .progressViewStyle(.linear)
                            .frame(width: 40)
                    }
                }
                .padding(.horizontal, 8)
                .padding(.vertical, 4)
                .background(Color.primary.opacity(0.04))
                .cornerRadius(6)
            }

            // Search Bar
            HStack(spacing: 6) {
                Image(systemName: "magnifyingglass")
                    .foregroundColor(.secondary)
                    .font(.system(size: 12))

                TextField("Search tasks...", text: $viewModel.searchQuery)
                    .textFieldStyle(.plain)
                    .font(.system(size: 12))

                if !viewModel.searchQuery.isEmpty {
                    Button(action: { viewModel.searchQuery = "" }) {
                        Image(systemName: "xmark.circle.fill")
                            .foregroundColor(.secondary)
                            .font(.system(size: 11))
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding(6)
            .background(Color.primary.opacity(0.05))
            .cornerRadius(8)

            // Filter Tabs (All, Active, Done)
            Picker("Filter", selection: $viewModel.filterStatus) {
                ForEach(TaskFilterStatus.allCases) { status in
                    Text(status.rawValue).tag(status)
                }
            }
            .pickerStyle(.segmented)

            // Category Filter Pills
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 6) {
                    CategoryPill(
                        title: "All",
                        icon: "square.grid.2x2",
                        color: Color.secondary,
                        isSelected: viewModel.selectedCategory == nil
                    ) {
                        viewModel.selectedCategory = nil
                    }

                    ForEach(TaskCategory.allCases) { category in
                        CategoryPill(
                            title: category.rawValue,
                            icon: category.icon,
                            color: Color(hex: category.colorHex),
                            isSelected: viewModel.selectedCategory == category
                        ) {
                            viewModel.selectedCategory = (viewModel.selectedCategory == category) ? nil : category
                        }
                    }
                }
                .padding(.vertical, 2)
            }
        }
        .padding(.horizontal, 14)
        .padding(.top, 14)
        .padding(.bottom, 8)
    }
}

struct CategoryPill: View {
    let title: String
    let icon: String
    let color: Color
    let isSelected: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack(spacing: 4) {
                Image(systemName: icon)
                    .font(.system(size: 9))
                Text(title)
                    .font(.system(size: 11, weight: isSelected ? .semibold : .regular))
            }
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
            .background(
                Capsule()
                    .fill(isSelected ? color.opacity(0.2) : Color.primary.opacity(0.04))
            )
            .overlay(
                Capsule()
                    .stroke(isSelected ? color : Color.clear, lineWidth: 1)
            )
            .foregroundColor(isSelected ? color : .secondary)
        }
        .buttonStyle(.plain)
    }
}
