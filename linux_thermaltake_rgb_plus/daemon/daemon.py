import time
from threading import Thread

from linux_thermaltake_rgb_plus.controllers import ThermaltakeController
from linux_thermaltake_rgb_plus.fan_manager import FanModel, FanManager
from linux_thermaltake_rgb_plus.daemon.config import Config
from linux_thermaltake_rgb_plus.lighting_manager import LightingEffect, LightingManager
from linux_thermaltake_rgb_plus import devices, logger
from linux_thermaltake_rgb_plus.devices import ThermaltakeDevice


class ThermaltakeDaemon:
    def __init__(self):
        logger.info('initializing thermaltake rgb daemon')

        logger.debug('loading config')
        self.config = Config()

        # logger.debug('creating lighting manager')
        # lighting_model = LightingEffect.factory(self.config.lighting_manager)
        # self.lighting_manager = LightingManager(lighting_model, 'default')

        self.attached_devices = {}
        self.controllers = {}

        logger.debug('configuring controllers')
        for controller in self.config.controllers:
            self.controllers[controller['unit']] \
                = ThermaltakeController.factory(controller['type'], controller['unit'])

            for id, model in controller['devices'].items():
                logger.debug(' configuring devices for controller %s: %s',
                             controller['type'], controller['unit'])
                dev = ThermaltakeDevice.factory(model)
                self.controllers[controller['unit']].attach_device(id, dev)
                self.register_attached_device(controller['unit'], id, dev)

        # self.prepare_fan_manager()
        self.fan_managers = self.prepare_manager(self.config.fan_manager,
                                                 FanModel,
                                                 FanManager)
        self.lighting_managers = self.prepare_manager(self.config.lighting_manager,
                                                      LightingEffect,
                                                      LightingManager)

        self._thread = Thread(target=self._main_loop)
        self._continue = False

    def _register_devices_to_manager(self, manager, unit_ports):
        for unit_port in unit_ports:
            try:
                dev = self.attached_devices[unit_port]
            except KeyError as e:
                logger.error('device {unit_port} is not registered.')
                raise e

            if isinstance(dev, devices.ThermaltakeFanDevice):
                logger.debug('  registering %s with fan manager %s',
                             dev.model, manager._name)
                manager.attach_device(dev)

    def _convert_devicesDict_to_unit_ports(self, devices_dict):
        unit_ports = []
        for unit, ports in devices_dict.items():
            for port in ports:
                unit_ports.append(f'{unit}:{port}')

        return unit_ports

    def prepare_manager(self, config_managers, Model, Manager):
        managers = {}
        rested_devices = list(self.attached_devices.keys())

        # mageger を設定する
        i = 0
        default_num = None
        for conf_mngr in config_managers:
            setting_name = conf_mngr['setting']
            if setting_name.lower() == 'default':
                # default が config.yaml 中に複数ある場合, 最後に 'default'.lower() だったものを
                # default として設定する.
                default_num = i
                i += 1
                continue
            model = Model.factory(conf_mngr)
            managers[setting_name] = Manager(model, setting_name)

            unit_ports = self._convert_devicesDict_to_unit_ports(conf_mngr['devices'])
            self._register_devices_to_manager(manager=managers[setting_name],
                                              unit_ports=unit_ports)
            for unit_port in unit_ports:
                rested_devices.remove(unit_port)
            i += 1

        # default manager を設定する.
        if default_num is None:
            logger.debug('default fan manager is not existed.')
            raise KeyError

        default_manager = config_managers[default_num]
        model = Model.factory(default_manager)
        managers['default'] = Manager(model, 'default')
        self._register_devices_to_manager(manager=managers['default'],
                                          unit_ports=rested_devices)

        return managers

    def prepare_fan_manager(self):
        logger.debug('prepare fan managers')
        self.fan_managers = {}
        rested_devices = list(self.attached_devices.keys())

        # fan_managerを設定する
        i = 0
        default_num = None
        for fan_manager in self.config.fan_manager:
            setting_name = fan_manager['setting']
            if setting_name.lower() == 'default':
                # default が複数あった場合, 最後に 'default'.lower() だったものを default として設定する.
                default_num = i
                i += 1
                continue

            fan_model = FanModel.factory(fan_manager)
            self.fan_managers[setting_name] = FanManager(fan_model, setting_name)

            unit_ports = self._convert_devicesDict_to_unit_ports(fan_manager['devices'])
            self._register_devices_to_manager(manager=self.fan_managers[setting_name],
                                              unit_ports=unit_ports)
            for unit_port in unit_ports:
                rested_devices.remove(unit_port)

            i += 1

        # default fan manager を設定する.
        if default_num is None:
            logger.debug('default fan manager is not existed.')
            raise KeyError

        default_fan_manager = self.config.fan_manager[default_num]
        fan_model = FanModel.factory(default_fan_manager)
        self.fan_managers['default'] = FanManager(fan_model, 'default')
        self._register_devices_to_manager(manager=self.fan_managers['default'],
                                          unit_ports=rested_devices)

    def register_attached_device(self, unit, port, dev=None):
        self.attached_devices[f'{unit}:{port}'] = dev

    def run(self):
        self._continue = True

        logger.debug('starting main thread')
        self._thread.start()

        logger.debug('starting lighting manager')
        for lighting_manager in self.lighting_managers.values():
            lighting_manager.start()

        logger.debug('startig fan manager')
        for fan_manager in self.fan_managers.values():
            fan_manager.start()

    def stop(self):
        logger.debug('recieved exit command')
        self._continue = False

        logger.debug('stopping lighting manager')
        for lighting_manager in self.lighting_managers.values():
            lighting_manager.stop()

        logger.debug('stopping fan manager')
        for fan_manager in self.fan_managers.values():
            fan_manager.stop()

        logger.debug('stopping main thread')
        self._thread.join()

        logger.debug('saving controller profiles')
        for controller in self.controllers.values():
            controller.save_profile()

    def _main_loop(self):
        while self._continue:
            time.sleep(1)

