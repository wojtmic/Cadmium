package dev.wojtmic.cadmium;

import net.kyori.adventure.audience.Audience;
import org.apache.commons.compress.archivers.tar.TarArchiveEntry;
import org.apache.commons.compress.archivers.tar.TarArchiveInputStream;
import org.apache.commons.compress.compressors.gzip.GzipCompressorInputStream;
import org.bukkit.Bukkit;
import org.bukkit.entity.Player;

import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.nio.file.attribute.PosixFilePermission;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.zip.GZIPInputStream;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;

public class Utils {
    public static boolean isWindows() {
        return System.getProperty("os.name").toLowerCase().contains("win");
    }

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
        return runProcess(java.util.Map.of(), command);
    }

    public static String runProcess(java.util.Map<String, String> env, String... command) throws IOException, InterruptedException {
        ProcessBuilder builder = new ProcessBuilder(command)
                .directory(Cadmium.dataFolder)
                .redirectErrorStream(false);
        builder.environment().putAll(env);
        Process process = builder.start();

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

    public static void runProcessVisible(java.util.Map<String, String> env, String... command) throws IOException, InterruptedException {
        ProcessBuilder builder = new ProcessBuilder(command)
                .directory(Cadmium.dataFolder)
                .inheritIO();
        builder.environment().putAll(env);
        Process process = builder.start();

        int exitCode = process.waitFor();
        if (exitCode != 0) {
            throw new IOException("Command failed (exit " + exitCode + "): " + String.join(" ", command));
        }
    }


    public static List<Audience> getReloadRecipients(String permission, Player exclude) {
        List<Audience> recipients = new ArrayList<>();
        recipients.add(Bukkit.getConsoleSender());
        for (Player p : Bukkit.getOnlinePlayers()) {
            if (p.equals(exclude)) continue;
            if (p.hasPermission(permission)) {
                recipients.add(p);
            }
        }
        return recipients;
    }

    public static void extractTarGz(Path archive, Path destination) throws IOException {
        Files.createDirectories(destination);

        try (InputStream fileIn = Files.newInputStream(archive);
             GzipCompressorInputStream gzipIn = new GzipCompressorInputStream(fileIn);
             TarArchiveInputStream tarIn = new TarArchiveInputStream(gzipIn)) {

            String stripPrefix = null;
            TarArchiveEntry entry;

            while ((entry = tarIn.getNextEntry()) != null) {
                if (!tarIn.canReadEntryData(entry)) {
                    continue;
                }

                String name = entry.getName();
                if (stripPrefix == null) {
                    stripPrefix = detectTopLevelDir(name);
                }
                String relative = stripPrefix != null ? stripLeadingDir(name, stripPrefix) : name;
                if (relative.isEmpty()) {
                    continue;
                }

                Path target = safeResolve(destination, relative);

                if (entry.isDirectory()) {
                    Files.createDirectories(target);
                } else if (entry.isSymbolicLink()) {
                    Files.createDirectories(target.getParent());
                    Path linkTarget = Path.of(entry.getLinkName());
                    Files.deleteIfExists(target);
                    Files.createSymbolicLink(target, linkTarget);
                } else {
                    Files.createDirectories(target.getParent());
                    Files.copy(tarIn, target, StandardCopyOption.REPLACE_EXISTING);
                    applyUnixMode(target, entry.getMode());
                }
            }
        }
    }

    public static void extractZip(Path archive, Path destination) throws IOException {
        Files.createDirectories(destination);

        try (InputStream fileIn = Files.newInputStream(archive);
             ZipInputStream zipIn = new ZipInputStream(fileIn)) {

            String stripPrefix = null;
            ZipEntry entry;

            while ((entry = zipIn.getNextEntry()) != null) {
                String name = entry.getName();
                if (stripPrefix == null) {
                    stripPrefix = detectTopLevelDir(name);
                }
                String relative = stripPrefix != null ? stripLeadingDir(name, stripPrefix) : name;
                if (relative.isEmpty()) {
                    zipIn.closeEntry();
                    continue;
                }

                Path target = safeResolve(destination, relative);

                if (entry.isDirectory()) {
                    Files.createDirectories(target);
                } else {
                    Files.createDirectories(target.getParent());
                    Files.copy(zipIn, target, StandardCopyOption.REPLACE_EXISTING);
                }
                zipIn.closeEntry();
            }
        }
    }

    public static void makeTreeExecutable(Path root) throws IOException {
        if (isWindows()) return;

        Files.walk(root).forEach(p -> {
            try {
                Files.setPosixFilePermissions(p, Set.of(
                        PosixFilePermission.OWNER_READ, PosixFilePermission.OWNER_WRITE, PosixFilePermission.OWNER_EXECUTE,
                        PosixFilePermission.GROUP_READ, PosixFilePermission.GROUP_EXECUTE,
                        PosixFilePermission.OTHERS_READ, PosixFilePermission.OTHERS_EXECUTE
                ));
            } catch (IOException ignored) {
            }
        });
    }

    private static void applyUnixMode(Path target, int mode) throws IOException {
        if (isWindows()) return;

        Set<PosixFilePermission> perms = java.util.EnumSet.noneOf(PosixFilePermission.class);
        if ((mode & 0400) != 0) perms.add(PosixFilePermission.OWNER_READ);
        if ((mode & 0200) != 0) perms.add(PosixFilePermission.OWNER_WRITE);
        if ((mode & 0100) != 0) perms.add(PosixFilePermission.OWNER_EXECUTE);
        if ((mode & 0040) != 0) perms.add(PosixFilePermission.GROUP_READ);
        if ((mode & 0010) != 0) perms.add(PosixFilePermission.GROUP_EXECUTE);
        if ((mode & 0004) != 0) perms.add(PosixFilePermission.OTHERS_READ);
        if ((mode & 0001) != 0) perms.add(PosixFilePermission.OTHERS_EXECUTE);

        try {
            Files.setPosixFilePermissions(target, perms);
        } catch (UnsupportedOperationException ignored) {
        }
    }

    private static String detectTopLevelDir(String firstEntryName) {
        int slash = firstEntryName.indexOf('/');
        return slash > 0 ? firstEntryName.substring(0, slash + 1) : null;
    }

    private static String stripLeadingDir(String name, String prefix) {
        return name.startsWith(prefix) ? name.substring(prefix.length()) : name;
    }

    private static Path safeResolve(Path destination, String relative) throws IOException {
        Path target = destination.resolve(relative).normalize();
        if (!target.startsWith(destination)) {
            throw new IOException("Archive entry escapes destination directory: " + relative);
        }
        return target;
    }
}