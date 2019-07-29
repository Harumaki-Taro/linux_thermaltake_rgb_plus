#!/usr/bin/python3

import os
import logging
import sys

from linux_thermaltake_rgb_plus.daemon.daemon import ThermaltakeDaemon


def main():
    if not os.path.isdir('tmp/linux_thermaltake_rgb_plus'):
        os.mkdir('/tmp/linux_thermaltake_rgb_plus')
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(levelname)s %(name)s %(funcName)s :%(message)s',
                        filename='/tmp/linux_thermaltake_rgb_plus/logger.log')

    # logging.basicConfig(stream=sys.stdout,
                        # level=logging.DEBUG,
                        # format='%(message)s')

    daemon = ThermaltakeDaemon()
    try:
        daemon.run()
    except KeyboardInterrupt:
        daemon.stop()


if __name__ == '__main__':
    main()

