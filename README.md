# Cadmium
Cadmium is a scripting plugin for Minecraft, much like [Skript](https://modrinth.com/plugin/skript). However, instead of a custom DSL, Cadmium uses Python with almost full support for the PyPI package ecosystem. 

![paper](https://cdn.jsdelivr.net/npm/@intergrav/devins-badges@3/assets/cozy/supported/paper_vector.svg)
![bukkit](https://cdn.jsdelivr.net/npm/@intergrav/devins-badges@3/assets/cozy/unsupported/spigot_vector.svg)

[![github](https://cdn.jsdelivr.net/npm/@intergrav/devins-badges@3/assets/cozy/available/github_vector.svg)](https://github.com/wojtmic/Cadmium)
[![hangar](https://cdn.jsdelivr.net/npm/@intergrav/devins-badges@3/assets/cozy/available/hangar_vector.svg)](https://hangar.papermc.io/wojtmic/cadmium)
[![modrinth](https://cdn.jsdelivr.net/npm/@intergrav/devins-badges@3/assets/cozy/available/modrinth_vector.svg)](https://modrinth.com/plugin/cadmium-code)

# Features
Cadmium uses **Python 3.12** as its scripting layer, which allows for almost full (read Packages) **suppport for PyPI packages**. On top, Paper/Bukkit API abstractions are provided, allowing for **Pythonic syntax to define Commands, hook into Events and more**.

## DISCLAIMER
**Cadmium is in beta**. This means you might see rough edges here and there, or missing features. Please file an Issue as a feature request in that case!

## Packages
Cadmium runs on GraalVM/GraalPy. This means that some PyPI packages will not work. A comprehensive list is available [here](https://graalpy.org/python-developers/compatibility/).<br>
From testing, generally speaking async libraries/drivers don't work and async might behave weirdly. However, pure-Python packages should load fine.

