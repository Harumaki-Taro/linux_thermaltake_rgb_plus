import time
from threading import Thread

import numpy as np
from psutil import sensors_temperatures

from linux_thermaltake_rgb_plus import Model, Manager
from linux_thermaltake_rgb_plus import logger


class FanModel(Model):
    @classmethod
    def factory(cls, config):
        subclass_dict = {clazz.model: clazz for clazz in cls.inheritors()}
        try:
            return subclass_dict.get(config.pop('model').lower())(config)
        except KeyError as e:
            logger.warn('%s not found in config item', e)

    def main(self):
        """
        returns an integer between 0 and 100 to set the fan speed too
        """
        raise NotImplementedError


class TempTargetModel(FanModel):
    model = 'temp_target'

    def __init__(self, config):
        self.sensor_name = config.get('sensor_name', 'coretemp')
        self.target = float(config.get('target'))
        self.multiplier = config.get('multiplier', 5)
        self.last_speed = 10

    def main(self):
        temp = self._get_temp()
        speed = (((temp - self.target) * self.multiplier) + self.last_speed) / 2

        if speed < 0:
            speed = 0
        elif speed > 100:
            speed = 100

        logger.debug(f'Temperature is {temp}°C, setting fan speed to {speed}%')
        return speed

    def _get_temp(self):
        return sensors_temperatures().get(self.sensor_name)[0].current

    def __str__(self) -> str:
        return f'target {self.target}°C on sensor {self.sensor_name}'


class LockedSpeedModel(FanModel):
    model = 'locked_speed'

    def __init__(self, config):
        speed = config.get('speed')
        if not 0 <= speed <= 100:
            raise ValueError(f'Speed must be between 0 and 100, got {speed}')
        self.speed = speed

    def main(self):
        logger.debug(f'Setting fan speed to {self.speed}%')
        return self.speed

    def __str__(self) -> str:
        return f'locked speed {self.speed}%'


class CurveModel(FanModel):
    """
    ユーザ指定の温度, スピードに基づいた fan curve
    """
    model = 'curve'

    def __init__(self, config):
        self.points = np.array(config.get('points'))
        self.temps = self.points[:, 0]
        self.speeds = self.points[:, 1]
        self.sensor_name = config.get('sensor_name', 'coretemp')
        logger.debug(f'curve fan points: {self.points}')

        if np.min(self.speeds) < 0:
            raise ValueError(f'Fan curve contains negative speeds, speed be in [0, 100]')
        if np.max(self.speeds) > 100:
            raise ValueError(f'Fan curve contains speeds greater than 100, '
                             'speed should be in [0, 100]')
        if np.any(np.diff(self.temps) <= 0):
            raise ValueError(f'Fan curve points should be strictly monotonically increasing, '
                             'configuration error ?')
        if np.any(np.diff(self.speeds) < 0):
            raise ValueError(f'Curve fan speeds should be monotonically increasing, '
                             'configuration error ?')

    def main(self):
        """
        現在の温度に対応する回転数を返す
        """
        temp = self._get_temp()
        speed = np.interp(x=temp, xp=self.temps, fp=self.speeds)

        if speed < 0:
            speed = 0
        if speed > 100:
            speed = 100

        logger.debug(f'Temperature is {temp}°C, setting fan speed to {speed}%')
        return speed

    def _get_temp(self):
        return sensors_temperatures().get(self.sensor_name)[0].current

    def __str__(self) -> str:
        return f'curve {self.points}'


class FanManager(Manager):
    def __init__(self, initial_model: FanModel = None, name: str = None):
        super().__init__(initial_model, name)
        self._continue = False
        self._thread = Thread(target=self._main_loop)
        logger.debug(f'creating FanManager object: [Model: {initial_model}]')

    def set_model(self, model: FanModel):
        logger.debug(f'setting fan model: {model.__class__.__name__}')
        if isinstance(model, FanModel):
            logger.debug(f'SUCCESS: set fan model: {model.__class__.__name__}')
            self._model = model

    def _main_loop(self):
        last_speed = None
        while self._contine:
            speed = int(round(self._model.main()))

            hoge = None
            for dev in self._devices:
                hoge = dev.get_fan_speed()
                logger.debug(f'now fan speed {hoge}')

            if last_speed != speed:
                last_speed = speed
                logger.debug(f'new fan speed {speed}')
                for dev in self._devices:
                    dev.set_fan_speed(speed)
            time.sleep(1)
        logger.debug(f'exiting {self.__class__.__name__} main loop')

    def start(self):
        logger.info(f'Starting fan manager ({self._model})...')
        self._contine = True
        self._thread.start()

    def stop(self):
        logger.info(f'Stopping fan manager...')
        self._continue = False
        self._thread.join()

