plugins {
    java
    application
}

java {
    sourceCompatibility = JavaVersion.VERSION_21
    targetCompatibility = JavaVersion.VERSION_21
}

application {
    mainClass = "parable.RunTests"
}

tasks.jar {
    manifest {
        attributes["Main-Class"] = "parable.RunTests"
    }
}

tasks.register("transpile") {
    description = "Transpile parable.py to Java"
    doLast {
        val sourcePath = project.findProperty("sourceFile")?.toString()
            ?: throw GradleException("Required property 'sourceFile' not set. Use -PsourceFile=/path/to/parable.py")
        val transpilerPath = project.findProperty("transpilerDir")?.toString()
            ?: throw GradleException("Required property 'transpilerDir' not set. Use -PtranspilerDir=/path/to/transpiler")
        val sourceFile = file(sourcePath)
        val outputFile = file("src/main/java/parable/Parable.java")
        outputFile.parentFile.mkdirs()
        val process = ProcessBuilder(
            "uv", "run", "--directory", transpilerPath,
            "python", "-m", "src.tongues", "--target", "java"
        )
            .redirectInput(sourceFile)
            .start()
        val transpiled = process.inputStream.bufferedReader().readText()
        val exitCode = process.waitFor()
        if (exitCode != 0) {
            val err = process.errorStream.bufferedReader().readText()
            throw GradleException("Transpiler failed: $err")
        }
        outputFile.writeText("package parable;\n\n$transpiled")
    }
}

tasks.compileJava {
    dependsOn("transpile")
}
