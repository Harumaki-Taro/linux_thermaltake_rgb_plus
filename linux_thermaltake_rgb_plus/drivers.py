import usb
from linux_thermaltake_rgb_plus import logger


class ThermaltakeControllerDriver:
    """
    Thermaltake controller 抽象クラス
    抽象クラスのため, product_id は None としておく.
    """
    VENDOR_ID = 0x264a

    def __init__(self, *args, **kwargs):
        self.vendor_id = self.VENDOR_ID
        self.product_id = None
        self.init(*args, **kwargs)

        self._initialize_device()

    def init(self, *args, **kwargs):
        raise NotImplementedError

    def _initialize_device(self):
        self.device = usb.core.find(idVendor=self.vendor_id,
                                    idProduct=self.product_id)
        # 最後のデバイスの利用の仕方が汚いと安全性が損なわれるので, 一度resetする.
        try:
            self.device.reset()
        except usb.core.USBerror as e:
            logger.error('usb device access denied (insufficient permissions)')
            raise e

        if self.device is None:
            raise ValueError('Device not found')

        # linux kernel はUSBデバイスがポートに挿入されたとき, 自動的にデバイスに対してデバイスドライ
        # バを関連付けてくれる. しかし, そのせいで他のデバイスドライバがUSBデバイスに対してアクセス
        # できなくなってしまう. そこで, 一度 detach する.
        try:
            self.device.detach_kernel_driver(0)
        except Exception:
            logger.warning('kernel driver already detached')

        # 使うためのconfigurationをアクティブにする. (引数なしはfirst configurationを選ぶことになる)
        self.device.set_configuration()

        # usbデバイスのinterfaceの所有権を取得したいことをlinux kernelに宣言するために, interface を
        # 要求する.
        try:
            usb.util.claim_interface(self.device, 0)
        except usb.core.USBerror as e:
            logger.error('{} while claiming interface for device'.format(e))
            raise e

        # たぶん, configurationディスクリプタの取得要求. configurationディスクリプタの取得要求に対し
        # て, interfaceディスクリプタとendpointディスクリプタも合わせて戻す使用になっていることが一
        # 般的なので, 次の行でinterfaceディスクリプタが戻されていると思われる.
        self.cfg = self.device.get_active_configuration()
        self.interface = self.cfg[(0, 0)]

        # 出力方向のエンドポイントを取得.
        self.endpoint_out = usb.util.find_descriptor(
                self.interface,
                custom_match=lambda e:
                    usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT)
        assert self.endpoint_out is not None

        # 入力方向のエンドポイントを取得.
        self.endpoint_in = usb.util.find_descriptor(
                self.interface,
                custom_match=lambda e:
                    usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN)
        assert self.endpoint_in is not None

        # usbデバイスを初期化, リセットする.
        self.init_controller()

    def init_controller(self):
        raise NotImplementedError()

    @staticmethod
    def _generate_data_array(length: int = 64, value: int = 0x00) -> list:
        """
        lengthサイズのゼロ化された配列を生成する
        """
        return [value for _ in range(length)]

    def _populate_partial_data_array(self, in_array: list, length=64) -> list:
        """
        要求された長さに到達するまで, 0x00で配列の後ろを埋める
        ****なんでこんなの必要なんだ？****
        """
        array = list(in_array)
        array.extend(self._generate_data_array(length=len(in_array)))

        return array

    def write_out(self, data: list, length: int = 64) -> None:
        try:
            self.endpoint_out.write(self._populate_partial_data_array(data, length))
        except OverflowError:
            return

    def read_out(self, length: int = 64) -> bytearray:
        """****これいるの?****"""
        return self.endpoint_out.read(length)

    def write_in(self, data: list, length: int = 64) -> None:
        """****これいるの?****"""
        self.endpoint_in.write(self._populate_partial_data_array(data, length))

    def read_in(self, length: int = 64) -> bytearray:
        return self.endpoint_in.read(length)

    def save_profile(self):
        """****これは何?****"""
        self.write_out([0x32, 0x53])


class ThermaltakeG3ControllerDriver(ThermaltakeControllerDriver):
    PRODUCT_ID_BASE = 0x1fa5

    def init(self, unit=1):
        self.product_id = self.PRODUCT_ID_BASE + (unit - 1)

    def init_controller(self):
        self.write_out([0xfe, 0x33])


class ThermaltakeRiingTrioControllerDriver(ThermaltakeG3ControllerDriver):
    PRODUCT_ID_BASE = 0x2135

