from linux_thermaltake_rgb_plus.devices import ThermaltakeRGBDevice


class ThermaltakeRiingPlusFloeRGB(ThermaltakeRGBDevice):
    model = 'Floe Riing RGB'
    num_leds = 12
    index_per_led = 3

