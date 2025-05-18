#!/opt/ibgateway-venv/bin/python
import os
import time
import subprocess
import pyotp

# Umgebungsvariablen aus os.environ
LOGIN    = os.environ['IBKR_LOGIN']
PASSWORD = os.environ['IBKR_PASSWORD']
SECRET   = os.environ['IBKR_TOTP_SECRET']
GATEWAY  = '/root/Jts/ibgateway/1030/ibgateway'
DISPLAY  = os.environ.get('DISPLAY', ':0')


def start_xvfb():
    subprocess.Popen([
        'Xvfb', DISPLAY, '-ac', '-screen', '0', '1024x768x24'
    ])
    os.environ['DISPLAY'] = DISPLAY
    time.sleep(3)


def launch_gateway():
    return subprocess.Popen([GATEWAY, '-role', 'gateway'])


def send_keystrokes(code):
    subprocess.call(['xdotool', 'search', '--name', 'IB Gateway', 'windowactivate', '--sync'])
    time.sleep(1)
    subprocess.call(['xdotool', 'type', LOGIN])
    time.sleep(0.5)
    subprocess.call(['xdotool', 'key', 'Tab'])
    time.sleep(0.5)
    subprocess.call(['xdotool', 'type', PASSWORD])
    time.sleep(0.5)
    subprocess.call(['xdotool', 'key', 'Tab'])
    time.sleep(0.5)
    subprocess.call(['xdotool', 'type', code])
    time.sleep(0.5)
    subprocess.call(['xdotool', 'key', 'Return'])


def configure_api():
    subprocess.call(['xdotool', 'key', 'Alt_L+c']); time.sleep(1)
    subprocess.call(['xdotool', 'key', 's']); time.sleep(2)
    for _ in range(4): subprocess.call(['xdotool', 'key', 'Tab']); time.sleep(0.3)
    subprocess.call(['xdotool', 'key', 'space']); time.sleep(0.5)
    for _ in range(3): subprocess.call(['xdotool', 'key', 'Tab']); time.sleep(0.3)
    subprocess.call(['xdotool', 'type', '127.0.0.1']); time.sleep(0.5)
    subprocess.call(['xdotool', 'key', 'Return']); time.sleep(1)


def main():
    start_xvfb()
    proc = launch_gateway()
    time.sleep(10)
    totp = pyotp.TOTP(SECRET).now()
    send_keystrokes(totp)
    configure_api()
    proc.wait()


if __name__ == '__main__':
    main()