// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "Tickr",
    platforms: [
        .macOS(.v13)
    ],
    products: [
        .executable(name: "Tickr", targets: ["Tickr"])
    ],
    targets: [
        .executableTarget(
            name: "Tickr",
            path: "Sources/Tickr"
        )
    ]
)
