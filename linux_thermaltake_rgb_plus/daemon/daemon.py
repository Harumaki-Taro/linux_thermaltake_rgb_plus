import time
from threading import Thread

from linux_thermaltake_rgb_plus.controllers import ThermaltakeController
from linux_thermaltake_rgb_plus.fan_manager import FanModel, FanManager
from linux_thermaltake_rgb_plus.daemon.config import Config
from linux_thermaltake_rgb_plus.lighting_manager import LightingEffect
from linux_thermaltake_rgb_plus import devices, logger
from linux_thermaltake_rgb_plus.devices import ThermaltakeDevice


class ThermaltakeDaemon:
    def __init__(self):
        logger.info('initializing thermaltake rgb daemon')

        logger.debug('loading config')
        self.config = Config()

        logger.debug('creating lighting manager')
        self.lighting_manager = LightingEffect.factory(self.config.lighting_manager)

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

        self.prepare_fan_manager()

        self._thread = Thread(target=self._main_loop)
        self._continue = False

    def prepare_fan_manager(self):
        logger.debug('prepare fan managers')
        self.fan_managers = {}

        rested_devices = list(self.attached_devices.keys())

        for fan_manager in self.config.fan_manager:
            setting_name = fan_manager['setting']
            if setting_name.lower() == 'default':
                continue

            fan_model = FanModel.factory(fan_manager)
            self.fan_managers[setting_name] = FanManager(fan_model)
            now_manager = self.fan_managers[setting_name]

            for unit, ports in fan_manager['devices'].items():
                for port in ports:
                    try:
                        dev = self.attached_devices[f'{unit}:{port}']
                    except KeyError as e:
                        logger.error('device {unit}:{port} is not registered.')
                        raise e

                    if isinstance(dev, devices.ThermaltakeFanDevice):
                        logger.debug('  registering %s with fan manager %s',
                                     dev.model, setting_name)
                        now_manager.attach_device(dev)
                        rested_devices.remove(f'{unit}:{port}')

        for fan_manager in self.config.fan_manager:
            setting_name = fan_manager['setting']
            if setting_name.lower() != 'default':
                continue
            # 設定ファイル中に DEFAULT, Default, default など複数あった場合, 最後の設定が適用される
            # ことになる.
            setting_name = 'default'

            fan_model = FanModel.factory(fan_manager)
            self.fan_managers[setting_name] = FanManager(fan_model)
            now_manager = self.fan_managers[setting_name]

            for dev_unit_port in rested_devices:
                try:
                    dev = self.attached_devices[dev_unit_port]
                except KeyError as e:
                    logger.error('device {unit}:{port} is not registered.')
                    raise e

                if isinstance(dev, devices.ThermaltakeFanDevice):
                    logger.debug('  registering %s with fan manager %s',
                                 dev.model, setting_name)
                    now_manager.attach_device(dev)

    def register_attached_device(self, unit, port, dev=None):
        if isinstance(dev, devices.ThermaltakeRGBDevice):
            logger.debug('  refistering %s with lighting manager', dev.model)
            self.lighting_manager.attach_device(dev)

        self.attached_devices[f'{unit}:{port}'] = dev

    def run(self):
        self._continue = True

        logger.debug('starting main thread')
        self._thread.start()

        logger.debug('starting lighting manager')
        self.lighting_manager.start()

        logger.debug('startig fan manager')
        # self.fan_manager.start()
        for fan_manager in self.fan_managers.values():
            fan_manager.start()

    def stop(self):
        logger.debug('recieved exit command')
        self._continue = False

        logger.debug('stopping lighting manager')
        self.lighting_manager.stop()

        logger.debug('stopping fan manager')
        # self.fan_manager.stop()
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

