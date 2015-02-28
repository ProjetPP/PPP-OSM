"""Configuration module."""
import os
import json
import logging
from ppp_libmodule.config import Config as BaseConfig
from ppp_libmodule.exceptions import InvalidConfig

class Config(BaseConfig):
    config_path_variable = 'PPP_OSM_CONFIG'
    
    def parse_config(self, data):
        self.search_api = data['search_api']

