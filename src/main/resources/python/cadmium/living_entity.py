from dataclasses import dataclass
import java
from cadmium.entity import Entity, entity_from_raw
from cadmium.block import block_from

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
        self.raw.kill()

    @property
    def burn_time(self) -> int:
        return self.raw.getFireTicks()

    @burn_time.setter
    def burn_time(self, val: int):
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

    # @property
    # def equipment(self):
    #     return self.raw.getEquipment()

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

    def heal(self, amount: int = 0):
        if not amount: self.health = self.max_health
        else: self.health += amount

    @property
    def burning(self) -> bool:
        return self.raw.getFireTicks() > 0

    @property
    def alive(self) -> bool:
        return not self.raw.isDead()

    @property
    def target_entity(self):
        loc = self.raw.getEyeLocation()
        result = self.raw.getWorld().rayTraceEntities(
            loc,
            loc.getDirection(),
            100.0,
            lambda e: e != self.raw
        )
        return entity_from_raw(result.getHitEntity()) if result else None

    @property
    def target_block(self):
        block = self.raw.getTargetBlockExact(100)
        return block_from(block) if block else None

    def get_target_block(self, dist: int = 100):
        block = self.raw.getTargetBlockExact(dist)
        return block_from(block) if block else None

    def __repr__(self):
        return f"LivingEntity({self.raw.getType()}, {self.uuid})"