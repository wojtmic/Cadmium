package dev.wojtmic.cadmium;

import com.moandjiezana.toml.Toml;
import org.eclipse.jgit.api.FetchCommand;
import org.eclipse.jgit.api.Git;
import org.eclipse.jgit.api.ResetCommand;
import org.eclipse.jgit.lib.Repository;
import org.eclipse.jgit.transport.UsernamePasswordCredentialsProvider;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.logging.Logger;

public class GitManager {

    private final Logger logger;

    public GitManager(Logger logger) {
        this.logger = logger;
    }

    public void setup() throws IOException {
        Path pyproject = Cadmium.dataFolder.toPath().resolve("pyproject.toml");
        if (!Files.exists(pyproject)) {
            return;
        }

        Toml toml = new Toml().read(pyproject.toFile());
        if (!toml.containsTable("tool.cadmium.git")) {
            return;
        }

        boolean enabled = getBoolean(toml, "tool.cadmium.git.enabled", true);
        if (!enabled) {
            return;
        }

        String url = getString(toml, "tool.cadmium.git.url", null);
        if (url == null || url.isBlank()) {
            logger.warning("[git] tool.cadmium.git is configured but no 'url' was given, skipping.");
            return;
        }

        String branch = getString(toml, "tool.cadmium.git.branch", null);
        String directory = getString(toml, "tool.cadmium.git.directory", ".");
        String username = getString(toml, "tool.cadmium.git.username", null);
        String password = getString(toml, "tool.cadmium.git.password", null);

        Path target = Cadmium.dataFolder.toPath().resolve(directory).normalize().toAbsolutePath();
        if (!target.startsWith(Cadmium.dataFolder.toPath().toAbsolutePath())) {
            throw new IOException("git.directory escapes the plugin data folder: " + directory);
        }

        UsernamePasswordCredentialsProvider credentials = null;
        if (password != null && !password.isBlank()) {
            boolean looksLikeSsh = url.startsWith("ssh://") || url.startsWith("git@") || url.contains(":") && !url.contains("://");
            if (looksLikeSsh) {
                logger.warning("[git] A password is set but the URL looks like an SSH remote (" + url
                        + "). UsernamePasswordCredentialsProvider only applies to HTTP(S) - it will be ignored, "
                        + "and auth will fall back to your machine's SSH keys/agent.");
            }
            credentials = new UsernamePasswordCredentialsProvider(
                    username != null ? username : "", password);
        }

        try {
            if (!isGitRepo(target)) {
                initRepo(target, url);
            }
            pull(target, branch, credentials);
        } catch (org.eclipse.jgit.api.errors.GitAPIException e) {
            throw new IOException("Git sync failed: " + e.getMessage(), e);
        }
    }

    private boolean isGitRepo(Path target) {
        return Files.isDirectory(target.resolve(".git"));
    }

    private void initRepo(Path target, String url) throws IOException, org.eclipse.jgit.api.errors.GitAPIException {
        logger.info("[git] Initializing git repo in " + target + " (existing files are kept, tracked files will be synced to remote)...");
        Files.createDirectories(target);
        try (Git git = Git.init().setDirectory(target.toFile()).call()) {
            git.getRepository().getConfig().setString("remote", "origin", "url", url);
            git.getRepository().getConfig().setString(
                    "remote", "origin", "fetch", "+refs/heads/*:refs/remotes/origin/*");
            git.getRepository().getConfig().save();
        }
    }

    private void pull(Path target, String branch,
                      UsernamePasswordCredentialsProvider credentials) throws IOException, org.eclipse.jgit.api.errors.GitAPIException {
        logger.info("[git] Syncing " + target + " to remote (local changes will be overwritten)...");
        try (Git git = Git.open(target.toFile())) {
            Repository repo = git.getRepository();

            FetchCommand fetch = git.fetch();
            if (credentials != null) {
                fetch.setCredentialsProvider(credentials);
            }
            fetch.call();

            String targetBranch = (branch != null && !branch.isBlank()) ? branch : resolveRemoteDefaultBranch(git, credentials);

            // Move HEAD via direct ref update, not CheckoutCommand, since
            // checkout refuses to overwrite existing working-tree files.
            // The hard reset below does the actual file overwrite.
            String localRef = "refs/heads/" + targetBranch;
            String remoteRef = "refs/remotes/origin/" + targetBranch;
            if (repo.exactRef(localRef) == null) {
                org.eclipse.jgit.lib.ObjectId remoteObjectId = repo.resolve(remoteRef);
                if (remoteObjectId == null) {
                    throw new IOException("Remote branch not found after fetch: " + remoteRef);
                }
                org.eclipse.jgit.lib.RefUpdate createRef = repo.updateRef(localRef);
                createRef.setNewObjectId(remoteObjectId);
                createRef.update();
            }
            if (!targetBranch.equals(repo.getBranch())) {
                repo.updateRef(org.eclipse.jgit.lib.Constants.HEAD).link(localRef);
            }

            git.reset()
                    .setMode(ResetCommand.ResetType.HARD)
                    .setRef("origin/" + targetBranch)
                    .call();

            git.clean()
                    .setCleanDirectories(true)
                    .setForce(true)
                    .call();

            logger.info("[git] Sync complete (reset to origin/" + targetBranch + ").");
        }
    }

    /**
     * Asks the remote directly which branch its HEAD points at (e.g. "main"
     * vs "master"), via ls-remote. Falls back to the local repo's current
     * branch name if the server doesn't report a symbolic HEAD.
     */
    private String resolveRemoteDefaultBranch(Git git, UsernamePasswordCredentialsProvider credentials)
            throws IOException, org.eclipse.jgit.api.errors.GitAPIException {
        var lsRemote = git.lsRemote().setRemote("origin");
        if (credentials != null) {
            lsRemote.setCredentialsProvider(credentials);
        }
        java.util.Map<String, org.eclipse.jgit.lib.Ref> refs = lsRemote.callAsMap();
        org.eclipse.jgit.lib.Ref head = refs.get("HEAD");
        if (head != null && head.isSymbolic()) {
            String target = head.getTarget().getName(); // refs/heads/<branch>
            String prefix = "refs/heads/";
            if (target.startsWith(prefix)) {
                return target.substring(prefix.length());
            }
        }
        return git.getRepository().getBranch();
    }

    private String getString(Toml toml, String key, String def) {
        String value = toml.getString(key, def);
        return resolveEnv(value);
    }

    private boolean getBoolean(Toml toml, String key, boolean def) {
        Boolean value = toml.getBoolean(key, def);
        return value != null ? value : def;
    }

    private String resolveEnv(String value) {
        if (value == null || value.isEmpty() || value.charAt(0) != '$') {
            return value;
        }
        String varName = value.substring(1);
        String resolved = System.getenv(varName);
        if (resolved == null) {
            logger.warning("[git] Environment variable '" + varName + "' referenced in pyproject.toml is not set.");
            return "";
        }
        return resolved;
    }
}