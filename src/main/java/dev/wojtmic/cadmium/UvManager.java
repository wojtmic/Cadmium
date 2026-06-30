package dev.wojtmic.cadmium;

import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.nio.file.attribute.PosixFilePermission;
import java.util.Set;
import java.util.logging.Logger;
import java.util.zip.GZIPInputStream;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;
import org.apache.commons.compress.archivers.tar.TarArchiveEntry;
import org.apache.commons.compress.archivers.tar.TarArchiveInputStream;

public class UvManager {

    private static final String UV_VERSION = "0.11.25";
    private static final String UV_BASE_URL =
            "https://releases.astral.sh/github/uv/releases/download/" + UV_VERSION + "/";

    private final Path dataFolder;
    private final Logger logger;
    private Path uvBinary;

    public UvManager(File dataFolder, Logger logger) {
        this.dataFolder = dataFolder.toPath();
        this.logger = logger;
    }

    public void setup() throws IOException, InterruptedException {
        uvBinary = dataFolder.resolve(isWindows() ? "uv.exe" : "uv").toAbsolutePath();

        if (!Files.exists(uvBinary)) {
            logger.info("[Cadmium] Downloading uv...");
            downloadUv();
            logger.info("[Cadmium] uv downloaded.");
        }

        Path venv = dataFolder.resolve(".venv").toAbsolutePath();
        if (!Files.exists(venv)) {
            logger.info("[Cadmium] Creating venv...");
            runProcess(uvBinary.toString(), "venv", venv.toString());
            logger.info("[Cadmium] Venv created.");
        }

        Path requirements = dataFolder.resolve("requirements.txt").toAbsolutePath();
        if (Files.exists(requirements)) {
            logger.info("[Cadmium] Installing requirements...");
            runProcess(uvBinary.toString(), "pip", "install",
                    "-r", requirements.toString(),
                    "--python", venv.toString());
            logger.info("[Cadmium] Requirements installed.");
        }
    }

    public Path getSitePackages() {
        Path venv = dataFolder.resolve(".venv").toAbsolutePath();
        // GraalPy is Python 3.12
        Path lib = venv.resolve("lib").resolve("python3.12").resolve("site-packages");
        if (Files.exists(lib)) return lib;
        // Windows layout
        return venv.resolve("Lib").resolve("site-packages");
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

        Path tmp = dataFolder.resolve("uv_download_tmp");
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

    private void extractFromTarGz(Path archive, String entryName, Path dest) throws IOException {
        try (TarArchiveInputStream tar = new TarArchiveInputStream(
                new GZIPInputStream(Files.newInputStream(archive)))) {
            TarArchiveEntry entry;
            while ((entry = tar.getNextEntry()) != null) {
                if (entry.getName().endsWith("/" + entryName) || entry.getName().equals(entryName)) {
                    Files.copy(tar, dest, StandardCopyOption.REPLACE_EXISTING);
                    return;
                }
            }
        }
        throw new IOException("Could not find '" + entryName + "' in tar.gz archive");
    }

    private void extractFromZip(Path archive, String entryName, Path dest) throws IOException {
        try (ZipInputStream zip = new ZipInputStream(Files.newInputStream(archive))) {
            ZipEntry entry;
            while ((entry = zip.getNextEntry()) != null) {
                if (entry.getName().endsWith("/" + entryName) || entry.getName().equals(entryName)) {
                    Files.copy(zip, dest, StandardCopyOption.REPLACE_EXISTING);
                    return;
                }
            }
        }
        throw new IOException("Could not find '" + entryName + "' in zip archive");
    }

    private void runProcess(String... command) throws IOException, InterruptedException {
        Process process = new ProcessBuilder(command)
                .directory(dataFolder.toFile())
                .inheritIO()
                .start();
        int exit = process.waitFor();
        if (exit != 0) {
            throw new IOException("Command failed with exit code " + exit + ": "
                    + String.join(" ", command));
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