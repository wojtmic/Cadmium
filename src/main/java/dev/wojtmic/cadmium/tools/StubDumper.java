package dev.wojtmic.cadmium.tools;

import java.io.FileWriter;
import java.io.IOException;
import java.lang.reflect.*;
import java.util.*;

public class StubDumper {

    private static final String[] CLASSES = {
            "org.bukkit.Bukkit",
            "org.bukkit.Server",
            "org.bukkit.GameMode",
            "org.bukkit.Location",
            "org.bukkit.Material",
            "org.bukkit.NamespacedKey",
            "org.bukkit.attribute.Attribute",
            "org.bukkit.attribute.AttributeModifier",
            "org.bukkit.attribute.AttributeModifier$Operation",
            "org.bukkit.enchantments.Enchantment",
            "org.bukkit.entity.EntityType",
            "org.bukkit.entity.LivingEntity",
            "org.bukkit.entity.Player",
            "org.bukkit.event.inventory.InventoryType",
            "org.bukkit.scoreboard.Team",
            "org.bukkit.scoreboard.Team$Option",
            "org.bukkit.scoreboard.Team$OptionStatus",
            "org.bukkit.scoreboard.NameTagVisibility",
            "org.bukkit.inventory.EquipmentSlotGroup",
            "org.bukkit.inventory.ItemFlag",
            "org.bukkit.inventory.ItemStack",
            "org.bukkit.persistence.PersistentDataType",
            "org.bukkit.scheduler.BukkitRunnable",
            "io.papermc.paper.datacomponent.DataComponentType",
            "io.papermc.paper.datacomponent.DataComponentTypes",
            "java.time.Duration",
            "java.util.Date",
            "java.util.UUID",
            "net.kyori.adventure.text.minimessage.MiniMessage",
            "net.kyori.adventure.title.Title",
            "net.kyori.adventure.title.Title$Times",

            "org.bukkit.event.entity.EntityDeathEvent",
            "org.bukkit.event.entity.EntityDamageEvent",
            "org.bukkit.event.player.PlayerInteractEntityEvent",
            "org.bukkit.event.player.PlayerMoveEvent",
            "io.papermc.paper.event.entity.EntityKnockbackEvent",
            "io.papermc.paper.event.entity.EntityPushedByEntityAttackEvent",
            "io.papermc.paper.event.player.AsyncChatEvent",
            "org.bukkit.event.player.PlayerJoinEvent",
            "org.bukkit.event.player.PlayerQuitEvent",
            "org.bukkit.event.entity.PlayerDeathEvent",
            "org.bukkit.event.player.PlayerCommandPreprocessEvent",
            "org.bukkit.event.entity.EntitySpawnEvent",
            "org.bukkit.event.player.PlayerFishEvent",
            "org.bukkit.event.player.PlayerGameModeChangeEvent",
            "org.bukkit.event.block.BlockBreakEvent",
            "org.bukkit.event.block.BlockPlaceEvent",
            "org.bukkit.event.inventory.InventoryClickEvent",
    };

    public static void dump(String outputPath) throws IOException {
        StringBuilder json = new StringBuilder("{\"classes\":[");
        boolean firstClass = true;

        for (String className : CLASSES) {
            Class<?> cls;
            try {
                cls = Class.forName(className);
            } catch (ClassNotFoundException e) {
                System.err.println("SKIP (not found): " + className);
                continue;
            }

            if (!firstClass) json.append(",");
            firstClass = false;

            json.append("{");
            json.append("\"name\":\"").append(escape(cls.getName())).append("\",");
            json.append("\"is_enum\":").append(cls.isEnum()).append(",");
            json.append("\"is_interface\":").append(cls.isInterface()).append(",");

            Class<?> sup = cls.getSuperclass();
            json.append("\"superclass\":");
            json.append(sup != null && sup != Object.class ? "\"" + escape(sup.getName()) + "\"" : "null");
            json.append(",");

            json.append("\"interfaces\":[");
            Class<?>[] ifaces = cls.getInterfaces();
            for (int i = 0; i < ifaces.length; i++) {
                if (i > 0) json.append(",");
                json.append("\"").append(escape(ifaces[i].getName())).append("\"");
            }
            json.append("],");

            json.append("\"enum_constants\":[");
            if (cls.isEnum()) {
                Object[] constants = cls.getEnumConstants();
                for (int i = 0; i < constants.length; i++) {
                    if (i > 0) json.append(",");
                    json.append("\"").append(escape(((Enum<?>) constants[i]).name())).append("\"");
                }
            }
            json.append("],");

            json.append("\"methods\":[");
            boolean firstMethod = true;
            Set<String> seen = new HashSet<>();
            for (Method m : cls.getMethods()) {
                if (m.getDeclaringClass() == Object.class) continue;
                if (!Modifier.isPublic(m.getModifiers())) continue;
                String sig = m.getName() + Arrays.toString(m.getParameterTypes());
                if (!seen.add(sig)) continue;

                if (!firstMethod) json.append(",");
                firstMethod = false;

                json.append("{");
                json.append("\"name\":\"").append(escape(m.getName())).append("\",");
                json.append("\"return_type\":\"").append(escape(typeName(m.getGenericReturnType()))).append("\",");
                json.append("\"static\":").append(Modifier.isStatic(m.getModifiers())).append(",");
                json.append("\"params\":[");
                Type[] ptypes = m.getGenericParameterTypes();
                for (int i = 0; i < ptypes.length; i++) {
                    if (i > 0) json.append(",");
                    json.append("\"").append(escape(typeName(ptypes[i]))).append("\"");
                }
                json.append("]");
                json.append("}");
            }
            json.append("],");

            json.append("\"fields\":[");
            boolean firstField = true;
            for (Field f : cls.getFields()) {
                if (f.getDeclaringClass() == Object.class) continue;
                if (!firstField) json.append(",");
                firstField = false;
                json.append("{");
                json.append("\"name\":\"").append(escape(f.getName())).append("\",");
                json.append("\"type\":\"").append(escape(typeName(f.getGenericType()))).append("\",");
                json.append("\"static\":").append(Modifier.isStatic(f.getModifiers()));
                json.append("}");
            }
            json.append("]");

            json.append("}");
        }
        json.append("]}");

        try (FileWriter w = new FileWriter(outputPath)) {
            w.write(json.toString());
        }
    }

    private static String typeName(Type t) {
        if (t instanceof Class<?> c) {
            if (c.isArray()) return typeName(c.getComponentType()) + "[]";
            return c.getName();
        }
        if (t instanceof ParameterizedType pt) {
            return typeName(pt.getRawType());
        }
        return t.getTypeName();
    }

    private static String escape(String s) {
        return s.replace("\\", "\\\\").replace("\"", "\\\"");
    }
}