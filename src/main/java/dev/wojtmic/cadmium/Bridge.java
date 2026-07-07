package dev.wojtmic.cadmium;

import org.bukkit.event.EventHandler;
import org.bukkit.event.Listener;
import org.bukkit.event.block.BlockBreakEvent;
import org.bukkit.event.block.BlockPlaceEvent;
import io.papermc.paper.event.player.AsyncChatEvent;
import org.bukkit.event.entity.EntityDamageEvent;
import org.bukkit.event.entity.EntityDeathEvent;
import org.bukkit.event.entity.PlayerDeathEvent;
import org.bukkit.event.player.PlayerInteractEntityEvent;
import org.bukkit.event.player.PlayerJoinEvent;
import org.bukkit.event.player.PlayerQuitEvent;
import org.graalvm.polyglot.Context;
import org.graalvm.polyglot.Value;

public class Bridge implements Listener {

    private final Value dispatch;
    private final Value eventsEnum;

    public Bridge(Context context) {
        Value cadmium = context.eval("python", "import cadmium; cadmium");
        this.dispatch = cadmium.getMember("_dispatch");
        this.eventsEnum = cadmium.getMember("EVENTS");
    }

    private void dispatch(String eventName, Object event) {
        Value enumValue = eventsEnum.getMember(eventName);
        if (enumValue == null) {
            throw new IllegalStateException(
                    "Cadmium internal error: Bridge dispatched event name '" + eventName
                            + "' but cadmium.EVENTS has no matching member. Add it to the EVENTS "
                            + "enum in cadmium/__init__.py.");
        }
        dispatch.execute(enumValue, event);
    }

    @EventHandler
    public void onPlayerJoin(PlayerJoinEvent event) {
        dispatch("player_join", event);
    }

    @EventHandler
    public void onPlayerQuit(PlayerQuitEvent event) {
        dispatch("player_quit", event);
    }

    @EventHandler
    public void onPlayerDeath(PlayerDeathEvent event) {
        dispatch("player_death", event);
    }

    @EventHandler
    public void onBlockBreak(BlockBreakEvent event) {
        dispatch("block_break", event);
    }

    @EventHandler
    public void onBlockPlace(BlockPlaceEvent event) {
        dispatch("block_place", event);
    }

    @EventHandler
    public void onChat(AsyncChatEvent event) {
        dispatch("chat", event);
    }

    @EventHandler
    public void onEntityDeath(EntityDeathEvent event) {
        dispatch("entity_death", event);
    }

    @EventHandler
    public void onEntityDamage(EntityDamageEvent event) {
        dispatch("entity_damage", event);
    }

    @EventHandler
    public void onPlayerInteractEntity(PlayerInteractEntityEvent event) {
        dispatch("player_interact_entity", event);
    }
}