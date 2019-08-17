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

