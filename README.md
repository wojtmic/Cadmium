# Cadmium
Cadmium is a scripting plugin for Minecraft, much like [Skript](https://modrinth.com/plugin/skript). However, instead of a custom DSL, Cadmium uses Python with almost full support for the PyPI package ecosystem. 

![paper](https://cdn.jsdelivr.net/npm/@intergrav/devins-badges@3/assets/cozy/supported/paper_vector.svg)
![bukkit](https://cdn.jsdelivr.net/npm/@intergrav/devins-badges@3/assets/cozy/unsupported/spigot_vector.svg)

[![github](https://cdn.jsdelivr.net/npm/@intergrav/devins-badges@3/assets/cozy/available/github_vector.svg)](https://github.com/wojtmic/Cadmium)
[![hangar](https://cdn.jsdelivr.net/npm/@intergrav/devins-badges@3/assets/cozy/available/hangar_vector.svg)](https://hangar.papermc.io/wojtmic/cadmium)
[![modrinth](https://cdn.jsdelivr.net/npm/@intergrav/devins-badges@3/assets/cozy/available/modrinth_vector.svg)](https://modrinth.com/projects/cadmium-code)

# Features
Cadmium uses **Python 3.12** as its scripting layer, which allows for almost full (read Technicals) **suppport for PyPI packages**. On top, Paper/Bukkit API abstractions are provided, allowing for **Pythonic syntax to define Commands, hook into Events and more**.

## DISCLAIMER
**ALL ABSTRACTIONS FOR PAPER APIS ARE NOT COMPLETE YET**<br>
As of now, Cadmium is in **BETA**. Currently, Java reflection is gonna be required in most cases. Cadmium is **not production ready** yet. API coverage will increase with updates.

### Technicals
Cadmium runs on GraalVM/GraalPy. This means that some PyPI packages will not work, including `requests` (use `httpx` instead). A more comprehensive list is available [here](https://graalpy.org/python-developers/compatibility/).
