PROTOCOL_GET = 0x33
PROTOCOL_SET = 0x32

PROTOCOL_FAN = 0x51
PROTOCOL_LIGHT = 0x52


class TT_RGB_PLUS:
    # https://github.com/MoshiMoshi0/ttrgbplusapi
    class ID:
        VID = 0x264a
        PID_start = 0x1fa5
        PID_end = 0xafb5

    class RGB_SPEED:
        EXTREME = 0x00
        FAST = 0x01
        NORMAL = 0x02
        SLOW = 0x03

        @classmethod
        def convert(cls, speed: str):
            if speed.lower() == 'extreme':
                return cls.EXTREME
            elif speed.lower() == 'fast':
                return cls.FAST
            elif speed.lower() == 'normal':
                return cls.NORMAL
            elif speed.lower() == 'slow':
                return cls.SLOW
            else:
                raise KeyError

    class RGB_MODE:
        FLOW = 0x00         # 0x00 + RGB_SPEED  COLORS not used
        SPECTRUM = 0x04     # 0x04 + RGB_SPEED  COLORS not used
        RIPPLE = 0x08       # 0x08 + RGB_SPEED  requires 1 COLOR
        BLINK = 0x0c        # 0x0c + RGB_SPEED  requires COLORS list with LED_COUNT colors
        PULSE = 0x10        # 0x10 + RGB_SPEED  requires COLORS list with LED_COUNT colors
        WAVE = 0x14         # 0x14 + RGB_SPEED  requires COLORS list with LED_COUNT colors
        PER_LED = 0x18      # requires COLORS list with LED_COUNT colors
        FULL = 0x19         # requires 1 COLORS

    class COMMAND:
        INIT = [0xfe, 0x33]                 # -> STATUS_BYTE  initilizes the controller
        GET_FIRMWARE_VERSION = [0x33, 0x50] # -> [MAJOR, MINOR, PATCH]
        SAVE_PROFILE = [0x32, 0x53]         # -> STATUS_BYTE Saves the RGB_MODE and SPEED
        SET_SPEED = [0x32, 0x52]            # -> STATUS_BYTE
        SET_RGB = [0x32, 0x52]              # -> STATUS_BYTE
        GET_DATA = [0x33, 0x51]             # -> [PORT, UNKNOEN, DPEED, RPM_L, RPM_H]

