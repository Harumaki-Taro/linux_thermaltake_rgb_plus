# 最初に目的のusbデバイスをポートに挿した状態でベンダーIDとプロダクトIDを調べる。
# 次に, 目的のusbデバイスをポートから抜いてベンダーIDとプロダクトIDを調べる。
# その差分が, 目的のusbデバイスのIDである。
import sys
import usb.core

# find USB devices
dev = usb.core.find(find_all=True)
#loop through devices, printing vender and product ids in decimal and hex
for cfg in dev:
    sys.stdout.write('Decimal VenderID=' + str(cfg.idVendor))
    sys.stdout.write(' & ProductID=' + str(cfg.idProduct) + '\n')
    sys.stdout.write('Hexadecimal VenderID=' + hex(cfg.idVendor))
    sys.stdout.write(' & ProductID=' + hex(cfg.idProduct) + '\n\n')

