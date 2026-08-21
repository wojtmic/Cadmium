package dev.wojtmic.cadmium;

import java.io.IOException;
import java.io.InputStream;
import java.io.UncheckedIOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.nio.file.attribute.PosixFilePermission;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.jar.JarFile;
import java.util.logging.Logger;

import static dev.wojtmic.cadmium.Cadmium.autoSync;
import static dev.wojtmic.cadmium.Utils.*;

public class PipManager {

    private static final String GRAALPY_VERSION = "25.2.4";
    private static final String GRAALPY_BASE_URL =
            "https://github.com/oracle/graalpython/releases/download/graal-" + GRAALPY_VERSION + "/";

    private final Logger logger;
    private Path bundledPython;
    private Path graalPyHome; // the extracted standalone GraalPy distribution

    public PipManager(Logger logger) {
        this.logger = logger;
    }

    public void setup() throws IOException, InterruptedException {
        bundledPython = extractBundledPython();

        graalPyHome = Cadmium.dataFolder.toPath().resolve(".graalpy").toAbsolutePath();
        if (!Files.exists(getBaseGraalPyBinary())) {
            logger.info("No GraalPy distribution found, downloading...");
            downloadAndExtractGraalPy();
            logger.info("GraalPy downloaded.");
        }

        Path venv = getVenvPath();
        if (!Files.exists(getVenvBinary())) {
            logger.info("No venv found, creating one...");
            runProcessVisible(
                    java.util.Map.of(),
                    getBaseGraalPyBinary().toString(), "-m", "venv", venv.toString()
            );
            logger.info("venv created.");
        }

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

    public Path getBundledPython() {
        return bundledPython;
    }

    private Path getVenvBinary() {
        return getVenvPath().resolve(isWindows() ? "Scripts/graalpy.exe" : "bin/graalpy");
    }

    private Path getBaseGraalPyBinary() {
        return graalPyHome.resolve(isWindows() ? "graalpy.exe" : "bin/graalpy");
    }

    private void ensurePip() throws IOException, InterruptedException {
        try {
            runProcessVisible(
                    java.util.Map.of(),
                    getVenvBinary().toString(), "-m", "pip", "--version"
            );
            logger.info("pip already available.");
        } catch (IOException e) {
            logger.info("pip not found, bootstrapping via ensurepip...");
            runProcessVisible(
                    java.util.Map.of(),
                    getVenvBinary().toString(), "-m", "ensurepip", "--upgrade"
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
        command.add(getVenvBinary().toString());
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

    private void downloadAndExtractGraalPy() throws IOException, InterruptedException {
        String filename = getGraalPyAssetName();
        String url = GRAALPY_BASE_URL + filename;

        Files.createDirectories(graalPyHome);
        Path tmp = Cadmium.dataFolder.toPath().resolve("graalpy_download_tmp");

        HttpClient client = HttpClient.newBuilder()
                .followRedirects(HttpClient.Redirect.ALWAYS)
                .build();
        HttpRequest request = HttpRequest.newBuilder().uri(URI.create(url)).build();

        try {
            HttpResponse<InputStream> response = client.send(request, HttpResponse.BodyHandlers.ofInputStream());
            if (response.statusCode() != 200) {
                throw new IOException("Failed to download GraalPy (HTTP " + response.statusCode() + "): " + url);
            }
            try (InputStream body = response.body()) {
                Files.copy(body, tmp, StandardCopyOption.REPLACE_EXISTING);
            }

            if (filename.endsWith(".zip")) {
                extractZip(tmp, graalPyHome);
            } else {
                extractTarGz(tmp, graalPyHome);
            }
        } finally {
            Files.deleteIfExists(tmp);
        }

        if (!isWindows()) {
            makeExecutable(getBaseGraalPyBinary());
        }
    }

    private String getGraalPyAssetName() {
        String os = System.getProperty("os.name").toLowerCase();
        String arch = System.getProperty("os.arch").toLowerCase();
        boolean isArm = arch.contains("aarch64") || arch.contains("arm");

        if (os.contains("win")) {
            return "graalpy3.12-" + GRAALPY_VERSION + "-windows-amd64.zip";
        } else if (os.contains("mac") || os.contains("darwin")) {
            return "graalpy3.12-" + GRAALPY_VERSION + "-macos-" + (isArm ? "aarch64" : "amd64") + ".tar.gz";
        } else {
            return "graalpy3.12-" + GRAALPY_VERSION + "-linux-" + (isArm ? "aarch64" : "amd64") + ".tar.gz";
        }
    }

    private void makeExecutable(Path path) throws IOException {
        Files.setPosixFilePermissions(path, Set.of(
                PosixFilePermission.OWNER_READ,
                PosixFilePermission.OWNER_WRITE,
                PosixFilePermission.OWNER_EXECUTE,
                PosixFilePermission.GROUP_READ,
                PosixFilePermission.GROUP_EXECUTE,
                PosixFilePermission.OTHERS_READ,
                PosixFilePermission.OTHERS_EXECUTE
        ));
    }
}