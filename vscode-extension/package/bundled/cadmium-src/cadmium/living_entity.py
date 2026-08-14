from dataclasses import dataclass
import java
from cadmium.entity import Entity

_Attribute = java.type("org.bukkit.attribute.Attribute")
Attributes = _Attribute


@dataclass
class LivingEntity(Entity):

    @property
    def health(self) -> float:
        return self.raw.getHealth()

    @health.setter
    def health(self, val: float):
        self.raw.setHealth(val)

    @property
    def max_health(self) -> float:
        return self.raw.getAttribute(Attributes.MAX_HEALTH).getValue()

    def kill(self):
        self.raw.setHealth(0.0)

    @property
    def fire_ticks(self) -> int:
        return self.raw.getFireTicks()

    @fire_ticks.setter
    def fire_ticks(self, val: int):
        self.raw.setFireTicks(val)

    @property
    def is_invisible(self) -> bool:
        return self.raw.isInvisible()

    @is_invisible.setter
    def is_invisible(self, val: bool):
        self.raw.setInvisible(val)

    def get_attribute(self, attribute):
        instance = self.raw.getAttribute(attribute)
        return instance.getValue() if instance is not None else None

    def set_attribute_base(self, attribute, value: float):
        instance = self.raw.getAttribute(attribute)
        if instance is not None:
            instance.setBaseValue(value)

    def add_potion_effect(self, effect):
        self.raw.addPotionEffect(effect)

    def remove_potion_effect(self, effect_type):
        self.raw.removePotionEffect(effect_type)

    def has_potion_effect(self, effect_type) -> bool:
        return self.raw.hasPotionEffect(effect_type)

    def clear_potion_effects(self):
        self.raw.clearActivePotionEffects()

    @property
    def is_ai_enabled(self) -> bool:
        return self.raw.hasAI()

    @is_ai_enabled.setter
    def is_ai_enabled(self, val: bool):
        self.raw.setAI(val)

    def damage(self, amount: float, source=None):
        if source is None:
            self.raw.damage(amount)
        else:
            self.raw.damage(amount, source)

    @property
    def last_damage_cause(self):
        return self.raw.getLastDamageCause()

    @property
    def equipment(self):
        return self.raw.getEquipment()

    @property
    def tool(self):
        from cadmium.inventory import itemstack_from
        return itemstack_from(self.raw.getEquipment().getItemInMainHand())

    @tool.setter
    def tool(self, item):
        self.raw.getEquipment().setItemInMainHand(item.raw)

    @property
    def off_hand(self):
        from cadmium.inventory import itemstack_from
        return itemstack_from(self.raw.getEquipment().getItemInOffHand())

    @off_hand.setter
    def off_hand(self, item):
        self.raw.getEquipment().setItemInOffHand(item.raw)

    @property
    def helmet(self):
        from cadmium.inventory import itemstack_from
        return itemstack_from(self.raw.getEquipment().getHelmet())

    @helmet.setter
    def helmet(self, item):
        self.raw.getEquipment().setHelmet(item.raw)

    @property
    def chestplate(self):
        from cadmium.inventory import itemstack_from
        return itemstack_from(self.raw.getEquipment().getChestplate())

    @chestplate.setter
    def chestplate(self, item):
        self.raw.getEquipment().setChestplate(item.raw)

    @property
    def leggings(self):
        from cadmium.inventory import itemstack_from
        return itemstack_from(self.raw.getEquipment().getLeggings())

    @leggings.setter
    def leggings(self, item):
        self.raw.getEquipment().setLeggings(item.raw)

    @property
    def boots(self):
        from cadmium.inventory import itemstack_from
        return itemstack_from(self.raw.getEquipment().getBoots())

    @boots.setter
    def boots(self, item):
        self.raw.getEquipment().setBoots(item.raw)

    def __repr__(self):
        return f"LivingEntity({self.raw.getType()}, {self.uuid})"