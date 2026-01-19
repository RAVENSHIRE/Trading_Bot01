"""Configuration management"""

import configparser
import os
from pathlib import Path
from typing import Optional


class Config:
    """Configuration loader"""
    
    def __init__(self, config_file: str = "config/trading_config.ini"):
        self.config = configparser.ConfigParser()
        
        if os.path.exists(config_file):
            self.config.read(config_file)
        
        self.config_file = config_file
    
    def get(self, section: str, key: str, fallback: Optional[str] = None) -> str:
        """Get configuration value"""
        try:
            value = self.config.get(section, key)
            # Replace environment variables
            if value.startswith("${") and value.endswith("}"):
                env_var = value[2:-1]
                return os.getenv(env_var, fallback or "")
            return value
        except configparser.NoOptionError:
            return fallback or ""
    
    def get_int(self, section: str, key: str, fallback: int = 0) -> int:
        """Get integer configuration value"""
        try:
            return self.config.getint(section, key)
        except (configparser.NoOptionError, ValueError):
            return fallback
    
    def get_float(self, section: str, key: str, fallback: float = 0.0) -> float:
        """Get float configuration value"""
        try:
            return self.config.getfloat(section, key)
        except (configparser.NoOptionError, ValueError):
            return fallback
    
    def get_bool(self, section: str, key: str, fallback: bool = False) -> bool:
        """Get boolean configuration value"""
        try:
            return self.config.getboolean(section, key)
        except (configparser.NoOptionError, ValueError):
            return fallback
