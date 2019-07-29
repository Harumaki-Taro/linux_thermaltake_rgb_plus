import os

import yaml

from linux_thermaltake_rgb_plus import logger


class Config:
    abs_config_dir = '/etc/linux_thermaltake_rgb_plus'
    rel_config_dir = 'linux_thermaltake_rgb_plus/assets'
    config_file_name = 'config.yml'

    def __init__(self):
        self.controllers = None
        self.fan_manager = None
        self.lighting_manager = None

        # if we have config in /etc, use it, otherwise try and use repository config file
        if os.path.isdir(self.abs_config_dir):
            if os.path.isfile(os.path.join(self.abs_config_dir, self.config_file_name)):
                self.config_dir = self.abs_config_dir
        elif os.path.isdir(self.rel_config_dir):
            if os.path.isfile(os.path.join(self.rel_config_dir, self.config_file_name)):
                self.config_dir = self.rel_config_dir
        else:

            raise Exception(f'{os.path.isdir(self.abs_config_dir)}: No config file found')

        config = self.load_config()
        self.parse_config(config)

    def load_config(self):
        with open('{}/{}'.format(self.config_dir, self.config_file_name)) as cfg:
            cfg_str = cfg.readlines()

        cfg_lines = []
        for s in cfg_str:
            # remove comments and blank lines
            if not s.strip().startswith('#') and len(s) > 1:
                cfg_lines.append(s)

        cfg = ''.join(cfg_lines)
        logger.debug('raw config file\n** start **\n\n%s\n** end **\n', cfg)
        return yaml.load(cfg)

    def parse_config(self, config):
        self.controllers = config.get('controllers')
        logger.debug(config.get('controllers'))

        self.fan_manager = config.get('fan_managers')
        logger.debug(config.get('fan_managers'))

        self.lighting_manager = config.get('lighting_manager')
        logger.debug(config.get('lighting_manager'))

