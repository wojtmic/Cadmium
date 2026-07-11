package dev.wojtmic.cadmium;

import org.apache.commons.compress.archivers.tar.TarArchiveEntry;
import org.apache.commons.compress.archivers.tar.TarArchiveInputStream;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.zip.GZIPInputStream;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;

public class Utils {
    public static void extractFromTarGz(Path archive, String entryName, Path dest) throws IOException {
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

    public static void extractFromZip(Path archive, String entryName, Path dest) throws IOException {
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

    public static String runProcess(String... command) throws IOException, InterruptedException {
        Process process = new ProcessBuilder(command)
                .directory(Cadmium.dataFolder)
                .redirectErrorStream(false)
                .start();

        String output;
        try (var reader = process.inputReader()) {
            output = reader.readLine();
        }

        int exitCode = process.waitFor();
        if (exitCode != 0) {
            throw new IOException("Command failed (exit " + exitCode + "): " + String.join(" ", command));
        }

        return output == null ? "" : output.trim();
    }
}