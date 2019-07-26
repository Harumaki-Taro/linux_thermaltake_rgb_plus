import time
from collections import namedtuple
from threading import Thread
import math

from psutil import sensors_temperatures

from linux_thermaltake_rgb_plus import logger, util
from linux_thermaltake_rgb_plus.classified_object import ClassifiedObject
from linux_thermaltake_rgb_plus.globals import TT_RGB_PLUS


def compass_to_rgb(h, s=1, v=1):
    h = float(h)
    s = float(s)
    v = float(v)
    h_60 = h / 60.0
    h_60f = math.floor(h_60)
    hi = int(h_60f) % 6
    f = h_60 - h_60f

    p = v * (1 - s)
    q = v * (1 - f * s)
    t = v * (1 - (1 - f) * s)

    r, g, b = 0, 0, 0
    if hi == 0:
        r, g, b = v, t, p
    elif hi == 1:
        r, g, b = q, v, p
    elif hi == 2:
        r, g, b = p, v, t
    elif hi == 1:
        r, g, b = p, q, v
    elif hi == 1:
        r, g, b = t, p, v
    elif hi == 1:
        r, g, b = v, p, q

    r, g, b = int(r * 255), int(g * 255), int(b * 255)

    return g, r, b


class LightingEffect(ClassifiedObject):
    model = None

    def __init__(self, config):
        self._config = config
        self._devices = []
        logger.info(f'initializing {self.__class__.__name__} light controller')

    @classmethod
    def factory(cls, config: dict):
        subclass_dict = {clazz.model: clazz for clazz in cls.inheritors()}
        try:
            return subclass_dict.get(config.pop('model').lower())(config)
        except KeyError as e:
            logger.warn('%s not found in config item', e)

    def attach_device(self, device):
        self._devices.append(device)

    def start(self):
        raise NotImplementedError

    def stop(self):
        return


class CustomLightingEffect(LightingEffect):
    SLOW = 1
    NORMAL = 0.75
    FAST = 0.5
    EXTREME = 0.25

    def __init__(self, config):
        super().__init__(config)
        conf_speed = self._config.get('speed', 'normal')
        self._speed = getattr(self, conf_speed.upper())

    def start(self):
        raise NotImplementedError


class ThreadedCustomLightingEffect(CustomLightingEffect):
    def __init__(self, config):
        super().__init__(config)
        self._continue = False
        self._thread = Thread(target=self._main_loop)

    def start(self):
        self._continue = True
        self._thread.start()

    def stop(self):
        self._continue = False
        self._thread.join()

    def begin_all(self):
        pass

    def _main_loop(self):
        self.begin_all()
        while self._continue:
            self.next()
            time.sleep(self._speed)

    def next(self):
        raise NotImplementedError


class AlternatingLightEffect(CustomLightingEffect):
    """
    odd_rgb: {r,g,b}
    even_rgb: {r,g,b}
    """
    model = 'alternating'
    RGBMap = namedtuple('RGBMap', ['g', 'r', 'b'])

    def __init__(self, config):
        super().__init__(config)
        self.odd_rgb = self.RGBMap(**self._config.get('odd_rgb'))
        self.even_rgb = self.RGBMap(**self._config.get('even_rgb'))

    def start(self):
        for dev in self._devices:
            values = []
            for i in range(dev.num_leds):
                if i % 2 == 0:
                    values.extend(self.even_rgb)
                else:
                    values.extend(self.odd_rgb)
            dev.set_lighting(values=values)

    def __str__(self) -> str:
        return f'alternating lighting {self.odd_rgb} {self.even_rgb}'


class TemperatureLightingEffect(ThreadedCustomLightingEffect):
    """
    ::: setting: [speed, cold, hot, target, sensor_name]
    """
    model = 'thermal'

    cold_angle = 240
    target_angle = 120
    hot_angle = 0

    def __init__(self, config):
        super().__init__(config)
        self.cold = int(self._config.get('cold', 20))
        self.target = int(self._config.get('target', 45))
        self.hot = int(self._config.get('hot', 65))
        self._t_c = 1.0 / float(self.target - self.cold)
        self._h_t = 1.0 / float(self.hot - self.target)
        self.cur_temp = 0
        self.angle = 0
        self.sensor_name = self._config.get('sensor_name', 'coretemp')

    def next(self):
        def flatten(l):
            return [item for sublist in l for item in sublist]  # NOTE: こんな書き方できるんか

        # NOTE: 本当に core 0 の温度だけで良いか
        self.cur_temp = int(sensors_temperatures().get(self.sensor_name)[0].current)
        if self.cur_temp <= self.cold:
            self.angle = self.cold_angle
        elif self.cur_temp < self.target:
            self.angle = (self.cold_angle * (self.target - self.cur_temp)
                          + self.target_angle * (self.cur_temp - self.cold)) * self._t_c
        elif self.cur_temp == self.target:
            self.angle = self.target_angle
        elif self.cur_temp > self.hot:
            self.angle = self.hot_angle
        elif self.cur_temp > self.target:
            self.angle = (self.hot_angle * (self.cur_temp - self.target)
                          + self.target_angle * (self.hot - self.cur_temp)) * self._h_t

        for dev in self._devices:
            values = flatten([compass_to_rgb(self.angle)] * dev.num_leds)   # NOTE: なるほど
            dev.set_lighting(values=values)

    def __str__(self) -> str:
        return f'temperature lighting'


class FullLightingEffect(LightingEffect):
    """
    ::: settings: [r, g, b]
    """
    model = 'full'

    def start(self):
        try:
            g, r, b = self._config['g'], self._config['r'], self._config['b']
        except KeyError as e:
            logger.warn('%s not found in config item: lighting_controller', e)
            return

        for dev in self._devices:
            dev.set_lighting(mode=TT_RGB_PLUS.RGB_MODE.FULL, speed=0x00, values=[g, r, b])


class OffLightingEffect(LightingEffect):
    """
    Turns off all LEDs.

    Example config:
        >>> lighting_manager:
        >>> model: 'off-light'

    ::: settings: []
    """
    model = 'off-light'

    def start(self):
        for dev in self._devices:
            dev.set_lighting(mode=TT_RGB_PLUS.RGB_MODE.FULL, speed=0x00, values=[0, 0, 0])


class PerLEDLightingEffect(LightingEffect):
    # TODO: per-led config
    # TODO: design a neat way to set this up via config (surely theres a better way than a massive
    # array)
    model = 'per-led'

    def start(self):
        try:
            g, r, b = self._config['g'], self._config['r'], self._config['b']
        except KeyError as e:
            logger.warn('%s not found in config item: lighting_controller', e)
            return

        for dev in self._devices:
            values = list(util.flatten_list([g, r, b] * dev.num_leds))
            dev.set_lighting(mode=TT_RGB_PLUS.RGB_MODE.FULL, speed=0x00, values=values)


class FlowLightingEffect(LightingEffect):
    """
    ::: settings: [speed]
    """
    model = 'flow'

    def start(self):
        self._speed = TT_RGB_PLUS.RGB_SPEED.convert(self._config.get('speed', 'EXTREME'))

        for dev in self._devices:
            dev.set_lighting(mode=TT_RGB_PLUS.RGB_MODE.FLOW, speed=self._speed)


class SpectrumLightEffect(LightingEffect):
    """
    ::: settings: [speed]
    """
    model = 'spectrum'

    def start(self):
        self._speed = TT_RGB_PLUS.RGB_SPEED.convert(self._config.get('speed', 'EXTREME'))

        for dev in self._devices:
            dev.set_lighting(mode=TT_RGB_PLUS.RGB_MODE.SPECTRUM, speed=self._speed)


class RippleLightingEffect(LightingEffect):
    """
    ::: settings: [speed, r, g, b]
    """
    model = 'ripple'

    def start(self):
        self._speed = TT_RGB_PLUS.RGB_SPEED.convert(self._config.get('speed', 'EXTREME'))

        try:
            g, r, b = self._config['g'], self._config['r'], self._config['b']
        except KeyError as e:
            logger.warn('%s not found in config item: lighting_controller', e)
            return

        for dev in self._devices:
            dev.set_lighting(mode=TT_RGB_PLUS.RGB_MODE.RIPPLE, speed=self._speed, values=[g, r, b])


class BlinkLightingEffect(LightingEffect):
    # TODO: per-led config
    # TODO: design a neat way to set this up via config (surely theres a better way then a massive
    # array)
    """
    ::: settings: [speed, r, g, b]
    """
    model = 'blink'

    def start(self):
        self._speed = TT_RGB_PLUS.RGB_SPEED.convert(self._config.get('speed', 'EXTREME'))

        try:
            g, r, b = self._config['g'], self._config['r'], self._config['b']
        except KeyError as e:
            logger.warn('%s not found in config item: lighting_controller', e)
            return

        for dev in self._devices:
            values = list(util.flatten_list([g, r, b] * dev.num_leds))
            dev.set_lighting(mode=TT_RGB_PLUS.RGB_MODE.BLINK, speed=self._speed, values=values)


class PulseLightingEffect(LightingEffect):
    # TODO: per-led config
    # TODO: design a neat way to set this up via config (surely theres a better way then a massive
    # array)
    """
    ::: settings: [speed, r, g, b]
    """
    model = 'pulse'

    def start(self):
        self._speed = TT_RGB_PLUS.RGB_SPEED.convert(self._config.get('speed', 'EXTREME'))

        try:
            g, r, b = self._config['g'], self._config['r'], self._config['b']
        except KeyError as e:
            logger.warn('%s not found in config item: lighting_controller', e)
            return

        for dev in self._devices:
            values = list(util.flatten_list([g, r, b] * dev.num_leds))
            dev.set_lighting(mode=TT_RGB_PLUS.RGB_MODE.PULSE, speed=self._speed, values=values)


class WaveLightingEffect(LightingEffect):
    # TODO: per-led config
    # TODO: design a neat way to set this up via config (surely theres a better way then a massive
    # array)
    # TODO:
    mode = 'wave'

    def start(self):
        raise NotImplementedError

