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

        logger.debug('creating fan manager')
        fan_model = FanModel.factory(self.config.fan_manager)
        self.fan_manager = FanManager(fan_model)

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
                dev = ThermaltakeDevice.factory(model, self.controllers[controller['unit']], id)
                self.controllers[controller['unit']].attach_device(id, dev)
                self.register_attached_device(controller['unit'], id, dev)

        self._thread = Thread(target=self._main_loop)
        self._continue = False

    def register_attached_device(self, unit, port, dev=None):
        if isinstance(dev, devices.ThermaltakeFanDevice):
            logger.debug('  registering %s with fan manager', dev.model)
            self.fan_manager.attach_device(dev)

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
        self.fan_manager.start()

    def stop(self):
        logger.debug('recieved exit command')
        self._continue = False

        logger.debug('stopping lighting manager')
        self.lighting_manager.stop()

        logger.debug('stopping fan manager')
        self.fan_manager.stop()

        logger.debug('stopping main thread')
        self._thread.join()

        logger.debug('saving controller profiles')
        for controller in self.controllers.values():
            controller.save_profile()

    def _main_loop(self):
        while self._continue:
            time.sleep(1)

