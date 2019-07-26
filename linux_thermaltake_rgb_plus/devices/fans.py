from linux_thermaltake_rgb_plus.devices import ThermaltakeRGBDevice, ThermaltakeFanDevice


class ThermaltakeRiingPlusFan(ThermaltakeRGBDevice, ThermaltakeFanDevice):
    model = 'Riing Plus'
    num_leds = 12
    index_per_led = 3

