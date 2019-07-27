from collections import namedtuple

from linux_thermaltake_rgb_plus import logger
from linux_thermaltake_rgb_plus.classified_object import ClassifiedObject
from linux_thermaltake_rgb_plus.globals \
    import PROTOCOL_SET, PROTOCOL_LIGHT, PROTOCOL_FAN, PROTOCOL_GET

FanSpeed = namedtuple('FanSpeed', ['get_speed', 'rpm'])


class ThermaltakeDevice(ClassifiedObject):
    model = None

    def __init__(self):
        pass

    def set_parent_controller(self, controller, port: int):
        self.controller = controller
        self.port = port

    @classmethod
    def factory(cls, model):
        # NOTE: これがなにをしているのか?
        subclass_dict = {clazz.model.lower(): clazz for clazz in cls.inheritors()
                         if clazz.model is not None}

        try:
            dev = subclass_dict[model.lower()]()
            logger.debug('created {} device'.format(dev.__class__.__name__))
            return dev
        except KeyError:
            logger.warn(f'model {model} not found. controller: {controller} port: {port}')
            raise KeyError


class ThermaltakeRGBDevice(ThermaltakeDevice):
    num_leds = 0
    index_per_led = 0

    def set_lighting(self, values: list = None, mode=0x18, speed=0x00) -> None:
        """
        パフォーマンスのため, 渡されたデータは正しいものとして処理する.
        :param values: [g,r,b,...]
        :param mode: lighting mode(hex)
        :param speed: light update speed(hex)
        """
        # write bytes
        data = [PROTOCOL_SET, PROTOCOL_LIGHT, self.port, mode + speed]
        if values:
            data.extend(values)
        logger.debug('{} set lighting: raw hex: {}'.format(self.__class__.__name__, data))

        # Set RGB Command
        self.controller.driver.write_out(data)


class ThermaltakeFanDevice(ThermaltakeDevice):
    def set_fan_speed(self, speed: int):
        # write bytes
        data = [PROTOCOL_SET, PROTOCOL_FAN, self.port, 0x01, int(speed)]

        # Set Speed Command
        self.controller.driver.write_out(data)

    def get_fan_speed(self):
        # write bytes
        data = [PROTOCOL_GET, PROTOCOL_FAN, self.port]

        # Get Data Command
        self.controller.driver.write_out(data)

        # Read Bytes
        id, unknown, speed, rpm_l, rpm_h = self.controller.driver.read_in()[2:7]

        # RPM is calculated as '(rpm_h << 8) + rpm_l'
        return FanSpeed(speed, (rpm_h << 8) + rpm_l)


from linux_thermaltake_rgb_plus.devices.pumps import *
from linux_thermaltake_rgb_plus.devices.fans import *
from linux_thermaltake_rgb_plus.devices.lights import *
