from linux_thermaltake_rgb_plus.devices import ThermaltakeRGBDevice


class ThermaltakePR22D5Res(ThermaltakeRGBDevice):
    model = 'Pacific PR22-D5 Plus'
    num_leds = 12
    index_per_led = 3       # NOTE: これ何やろか？


class ThermaltakeW4PlusWB(ThermaltakeRGBDevice):
    model = 'Pacific W4 Plus CPU Waterblock'
    num_leds = 12
    index_per_led = 3


class ThermaltakeVGTX1080PlusWB(ThermaltakeRGBDevice):
    model = 'Pacific V-GTX 1080Ti Plus GPU Waterblock'
    num_leds = 12
    index_per_led = 3


class ThermaltakeRadPlusLED(ThermaltakeRGBDevice):
    model = 'Pacific Rad Plus LED Panel'
    num_leds = 12
    index_per_led = 3


class ThermaltakeLumiPlusLEDH(ThermaltakeRGBDevice):
    model = 'Pacific Plus LED Strip'
    num_leds = 12
    index_per_led = 3

