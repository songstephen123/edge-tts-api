"""
配置模块
"""
import sys
import importlib.util

# Load the config.py module directly
spec = importlib.util.spec_from_file_location("app.config.config", "/Users/songstephen/edge-tts-skill/app/config.py")
config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_module)

settings = config_module.settings
tts_config = config_module.tts_config

__all__ = ["settings", "tts_config"]
