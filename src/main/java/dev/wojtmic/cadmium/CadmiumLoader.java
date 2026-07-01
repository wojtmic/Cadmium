package dev.wojtmic.cadmium;

import io.papermc.paper.plugin.loader.PluginClasspathBuilder;
import io.papermc.paper.plugin.loader.PluginLoader;
import io.papermc.paper.plugin.loader.library.impl.MavenLibraryResolver;
import org.eclipse.aether.artifact.DefaultArtifact;
import org.eclipse.aether.graph.Dependency;
import org.eclipse.aether.repository.RemoteRepository;

public class CadmiumLoader implements PluginLoader {
    @Override
    public void classloader(PluginClasspathBuilder builder) {
        MavenLibraryResolver resolver = new MavenLibraryResolver();
        resolver.addRepository(new RemoteRepository.Builder(
                "central", "default", MavenLibraryResolver.MAVEN_CENTRAL_DEFAULT_MIRROR).build());

        resolver.addDependency(new Dependency(
                new DefaultArtifact("org.graalvm.polyglot:polyglot:25.0.3"), null));
        resolver.addDependency(new Dependency(
                new DefaultArtifact("org.graalvm.python:python-embedding:25.0.3"), null));
        resolver.addDependency(new Dependency(
                new DefaultArtifact("org.apache.commons:commons-compress:1.27.1"), null));
        resolver.addDependency(new Dependency(
                new DefaultArtifact("com.moandjiezana.toml:toml4j:0.7.2"), null));

        builder.addLibrary(resolver);
    }
}