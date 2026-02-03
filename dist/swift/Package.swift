// swift-tools-version:5.9
import PackageDescription

let package = Package(
    name: "Parable",
    products: [
        .library(
            name: "Parable",
            targets: ["Parable"]
        )
    ],
    targets: [
        .target(
            name: "Parable",
            path: "Sources/Parable"
        ),
        .executableTarget(
            name: "RunTests",
            dependencies: ["Parable"],
            path: "Sources/RunTests"
        )
    ]
)
