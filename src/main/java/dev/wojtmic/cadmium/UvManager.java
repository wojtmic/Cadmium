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
import java.util.Set;
import java.util.jar.JarFile;
import java.util.logging.Logger;

import static dev.wojtmic.cadmium.Cadmium.autoSync;
import static dev.wojtmic.cadmium.Cadmium.uvOverride;
import static dev.wojtmic.cadmium.Utils.*;

public class UvManager {

    private static final String UV_VERSION = "0.11.25";
    private static final String UV_BASE_URL =
            "https://releases.astral.sh/github/uv/releases/download/" + UV_VERSION + "/";

    private final Logger logger;
    private Path uvBinary;
    private Path bundledPython;

    public UvManager(Logger logger) {
        this.logger = logger;
    }

    public void setup() throws IOException, InterruptedException {
        switch (uvOverride) {
            case "auto" -> {
                if (isWindows()) {
                    uvBinary = Path.of(runProcess("where", "uv"));
                } else {
                    uvBinary = Path.of(runProcess("which", "uv"));
                }
                if (!Files.exists(uvBinary)) {
                    uvBinary = Cadmium.dataFolder.toPath().resolve(isWindows() ? "uv.exe" : "uv").toAbsolutePath();
                    if (!Files.exists(uvBinary)) {
                        logger.info("[Cadmium] Downloading uv...");
                        downloadUv();
                        logger.info("[Cadmium] uv downloaded.");
                    }
                    logger.info("[Cadmium] Using self-installed uv.");
                } else {
                    logger.info("[Cadmium] Using system uv.");
                }
            }
            case "download" -> {
                uvBinary = Cadmium.dataFolder.toPath().resolve(isWindows() ? "uv.exe" : "uv").toAbsolutePath();
                if (!Files.exists(uvBinary)) {
                    logger.info("[Cadmium] Downloading uv...");
                    downloadUv();
                    logger.info("[Cadmium] uv downloaded.");
                }
                logger.info("[Cadmium] Using self-installed uv.");
            }
            case "system" -> {
                if (isWindows()) {
                    uvBinary = Path.of(runProcess("where", "uv"));
                } else {
                    uvBinary = Path.of(runProcess("which", "uv"));
                }
                if (!Files.exists(uvBinary)) {
                    logger.severe("[Cadmium] uv isn't installed! Change uv-path or install uv system-wide.");
                }
                logger.info("[Cadmium] Using system uv.");
            }
            default -> uvBinary = Path.of(uvOverride);
        }

        if (autoSync) {
            logger.info("[Cadmium] Syncing Python Project...");
            runProcess(uvBinary.toString(), "sync");
            logger.info("[Cadmium] Sync complete.");
        }

        bundledPython = extractBundledPython();
    }

    public Path getSitePackages() {
        Path venv = Cadmium.dataFolder.toPath().resolve(".venv").toAbsolutePath();

        Path lib = venv.resolve("lib").resolve("python3.12").resolve("site-packages");
        if (Files.exists(lib)) return lib;

        return venv.resolve("Lib").resolve("site-packages");
    }

    public Path getBundledPython() {
        return bundledPython;
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

    private void downloadUv() throws IOException {
        String filename = getUvFilename();
        String url = UV_BASE_URL + filename;

        HttpClient client = HttpClient.newBuilder()
                .followRedirects(HttpClient.Redirect.ALWAYS)
                .build();
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(url))
                .build();

        Path tmp = Cadmium.dataFolder.toPath().resolve("uv_download_tmp");
        try {
            HttpResponse<InputStream> response = client.send(
                    request, HttpResponse.BodyHandlers.ofInputStream());

            try (InputStream body = response.body()) {
                Files.copy(body, tmp, StandardCopyOption.REPLACE_EXISTING);
            }

            if (filename.endsWith(".zip")) {
                extractFromZip(tmp, isWindows() ? "uv.exe" : "uv", uvBinary);
            } else {
                extractFromTarGz(tmp, "uv", uvBinary);
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new IOException("Download interrupted", e);
        } finally {
            Files.deleteIfExists(tmp);
        }

        if (!isWindows()) {
            Files.setPosixFilePermissions(uvBinary, Set.of(
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

    private String getUvFilename() {
        String os = System.getProperty("os.name").toLowerCase();
        String arch = System.getProperty("os.arch").toLowerCase();

        String target;
        if (os.contains("win")) {
            target = arch.contains("aarch64") || arch.contains("arm")
                    ? "aarch64-pc-windows-msvc"
                    : "x86_64-pc-windows-msvc";
            return "uv-" + target + ".zip";
        } else if (os.contains("mac") || os.contains("darwin")) {
            target = arch.contains("aarch64") || arch.contains("arm")
                    ? "aarch64-apple-darwin"
                    : "x86_64-apple-darwin";
        } else {
            // Linux
            target = arch.contains("aarch64") || arch.contains("arm")
                    ? "aarch64-unknown-linux-gnu"
                    : "x86_64-unknown-linux-gnu";
        }
        return "uv-" + target + ".tar.gz";
    }

    private boolean isWindows() {
        return System.getProperty("os.name").toLowerCase().contains("win");
    }
}