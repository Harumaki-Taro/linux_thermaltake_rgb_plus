## このプログラムについて
このプログラムはthermaltake製の Riing Plus RGB Radiator Fan の点灯色を制御する常駐プログラムです。
wave, pulse, spectrum などの点灯モードやCPU温度依存の点灯色変化をymlファイルから指定できます。
製品ページ：https://jp.thermaltake.com/riing-plus-14-rgb-radiator-fan-tt-premium-edition-5-fan-pack.html
参考にしたプログラムなど：
  https://github.com/chestm007/linux_thermaltake_riing
  https://github.com/MoshiMoshi0/ttrgbplusapi


## How To Use
0. `sudo pip numpy, pyusb, psutil, pyyaml` する.

1. /optにディレクトリごと配置する.
```
sudo cp linux_thermaltake_rgb_plus/ /opt/
```
2. `config.yml`を`/etc`に置く.
```
sudo mkdir /etc/linux_thermaltake_rgb_plus
sudo cp linux_thermaltake_rgb_plus/linux_thermaltake_rgb_plu/assets/config.yml
/etc/linux_thermaltake_rgb_plus
```
3. `linux_thermaltake_rgb_plus.service`を`/stc/systemd/system`に置く.
```
sudo cp
linux_thermaltake_rgb_plus/linux_thermaltake_rgb_plus/assets/linux_thermaltake_rgb_plus.service
/etc/systemd/system/
```
4. daemonを起動する.
```
systemctl enable --now linux_thermaltake_rgb_plus.service
```

