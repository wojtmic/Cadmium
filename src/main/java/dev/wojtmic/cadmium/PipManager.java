package dev.wojtmic.cadmium;

import java.io.IOException;
import java.io.InputStream;
import java.io.UncheckedIOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.ArrayList;
import java.util.List;
import java.util.jar.JarFile;
import java.util.logging.Logger;

import static dev.wojtmic.cadmium.Cadmium.autoSync;
import static dev.wojtmic.cadmium.Utils.*;

public class PipManager {

    private final Logger logger;
    private Path bundledPython;

    public PipManager(Logger logger) {
        this.logger = logger;
    }

    public void setup() throws IOException, InterruptedException {
        bundledPython = extractBundledPython();

        logger.info("Ensuring pip is available...");
        ensurePip();

        if (autoSync) {
            logger.info("Syncing Python dependencies...");
            syncDependencies();
            logger.info("Sync complete.");
        }
    }

    public Path getVenvPath() {
        return Cadmium.dataFolder.toPath().resolve("venv").toAbsolutePath();
    }

    public Path getSitePackages() {
        Path venv = getVenvPath();
        Path lib = venv.resolve("lib").resolve("python3.12").resolve("site-packages");
        if (Files.exists(lib)) return lib;
        return venv.resolve("Lib").resolve("site-packages");
    }

    private Path getGraalPyBinary() {
        Path venv = getVenvPath();
        return venv.resolve(isWindows() ? "Scripts/graalpy.exe" : "bin/graalpy");
    }
    public Path getBundledPython() {
        return bundledPython;
    }

    private void ensurePip() throws IOException, InterruptedException {
        try {
            runProcess(
                    java.util.Map.of(),
                    getGraalPyBinary().toString(), "-m", "pip", "--version"
            );
            logger.info("pip already available.");
        } catch (IOException e) {
            logger.info("pip not found, bootstrapping via ensurepip...");
            runProcess(
                    java.util.Map.of(),
                    getGraalPyBinary().toString(), "-m", "ensurepip", "--upgrade"
            );
        }
    }

    private void syncDependencies() throws IOException, InterruptedException {
        Path pyproject = Cadmium.dataFolder.toPath().resolve("pyproject.toml");
        if (!Files.exists(pyproject)) {
            logger.warning("No pyproject.toml found, skipping dependency sync.");
            return;
        }

        List<String> deps = parseDependencies(pyproject);
        if (deps.isEmpty()) {
            logger.info("No dependencies declared, nothing to sync.");
            return;
        }

        List<String> command = new ArrayList<>();
        command.add(getGraalPyBinary().toString());
        command.add("-m");
        command.add("pip");
        command.add("install");
        command.addAll(deps);

        runProcessVisible(java.util.Map.of(), command.toArray(new String[0]));
    }

    private List<String> parseDependencies(Path pyproject) throws IOException {
        com.moandjiezana.toml.Toml toml = new com.moandjiezana.toml.Toml().read(pyproject.toFile());
        List<String> deps = toml.getList("project.dependencies");
        return deps != null ? deps : new ArrayList<>();
    }

    private Path extractBundledPython() throws IOException {
        Path dest = Cadmium.dataFolder.toPath().resolve(".cadmium_bundle");
        Files.createDirectories(dest);
        try (JarFile jar = new JarFile(Cadmium.pluginFile)) {
            jar.stream()
                    .filter(e -> e.getName().startsWith("python/") && !e.isDirectory())
                    .forEach(e -> {
                        try {
                            String relative = e.getName().substring("python/".length());
                            Path target = dest.resolve(relative);
                            Files.createDirectories(target.getParent());
                            try (InputStream is = jar.getInputStream(e)) {
                                Files.copy(is, target, StandardCopyOption.REPLACE_EXISTING);
                            }
                        } catch (IOException ex) {
                            throw new UncheckedIOException(ex);
                        }
                    });
        } catch (UncheckedIOException e) {
            throw e.getCause();
        }
        return dest;
    }

    private boolean isWindows() {
        return System.getProperty("os.name").toLowerCase().contains("win");
    }
}