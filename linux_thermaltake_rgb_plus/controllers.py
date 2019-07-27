from linux_thermaltake_rgb_plus import drivers, logger
from linux_thermaltake_rgb_plus import ClassifiedObject


class ThermaltakeController(ClassifiedObject):
    def __init__(self, unit=1):
        self.devices = {}
        self.driver = None
        self.unit = unit
        self.ports = 0
        self.init()

        if self.driver is None:
            raise RuntimeError('driver not set')
        if self.ports == 0:
            raise RuntimeError('ports not set')

    @classmethod
    def factory(cls, unit_type, unit_identifier=None):
        subclass_dict = {clazz.model: clazz for clazz in cls.inheritors()}
        try:
            if unit_identifier is not None:
                return subclass_dict.get(unit_type.lower())(unit=unit_identifier)
            else:
                return subclass_dict.get(unit_type.lower())()
        except KeyError as e:
            logger.warn('%s not a valid controller type', e)

    def init(self):
        raise NotImplementedError

    def attach_device(self, port=None, dev=None):
        dev.set_parent_controller(controller=self, port=port)
        self.devices[port] = dev

        return self.devices[port]

    def save_profile(self):
        self.driver.save_profile()


class ThermaltakeG3Controller(ThermaltakeController):
    model = 'g3'

    def init(self):
        self.driver = drivers.ThermaltakeG3ControllerDriver(self.unit)
        self.ports = 5


class ThermaltakeTTSync5Controller(ThermaltakeController):
    model = 'ttsync5'

    def init(self):
        self.driver = drivers.ThermaltakeTTSync5ControllerDriver(self.unit)
        self.ports = 5


class ThermaltakeRiingTrioController(ThermaltakeController):
    model = 'riingtrio'

    def init(self):
        self.driver = drivers.ThermaltakeRiingTrioControllerDriver(self.unit)
        self.ports = 5


def controller_factory(unit_type=None, unit=1, **kwargs) -> ThermaltakeController:
    if unit_type.lower() == 'g3':
        return ThermaltakeG3Controller(unit)

    elif unit_type.lower() == 'ttsync5':
        return ThermaltakeTTSync5Controller(unit)

    elif unit_type.lower() == 'riingtrio':
        return ThermaltakeRiingTrioController(unit)

