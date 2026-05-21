// swift-tools-version: 5.9

import PackageDescription

let package = Package(
    name: "EUDAMEDLocalBeta",
    platforms: [
        .macOS(.v13)
    ],
    products: [
        .executable(name: "EUDAMEDLocalBeta", targets: ["EUDAMEDLocalBeta"])
    ],
    targets: [
        .executableTarget(name: "EUDAMEDLocalBeta")
    ]
)
