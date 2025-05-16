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
    # Starte Xvfb auf dem angegebenen DISPLAY
    subprocess.Popen([
        'Xvfb', DISPLAY, '-ac', '-screen', '0', '1024x768x24'
    ])
    os.environ['DISPLAY'] = DISPLAY
    time.sleep(3)


def launch_gateway():
    # Starte das IBKR Gateway im headless-Modus
    return subprocess.Popen([GATEWAY, '-role', 'gateway'])


def send_keystrokes(code):
    # Fokussiere das Login-Fenster und tippe Benutzer, Passwort, 2FA-Code ein
    subprocess.call(['xdotool', 'search', '--name', 'IB Gateway', 'windowactivate', '--sync'])
    time.sleep(1)

    # Benutzername
    subprocess.call(['xdotool', 'type', LOGIN])
    time.sleep(0.5)
    subprocess.call(['xdotool', 'key', 'Tab'])
    time.sleep(0.5)
    # Passwort
    subprocess.call(['xdotool', 'type', PASSWORD])
    time.sleep(0.5)
    subprocess.call(['xdotool', 'key', 'Tab'])
    time.sleep(0.5)
    # TOTP-Code
    subprocess.call(['xdotool', 'type', code])
    time.sleep(0.5)
    subprocess.call(['xdotool', 'key', 'Return'])


def configure_api():
    # Öffne Configure -> Settings -> API und aktiviere Socket-Clients
    # Alt+C, S öffnet das Settings-Menü
    subprocess.call(['xdotool', 'key', 'Alt_L+c']); time.sleep(1)
    subprocess.call(['xdotool', 'key', 's']); time.sleep(2)

    # Tab zur API-Seite
    for _ in range(4):
        subprocess.call(['xdotool', 'key', 'Tab']); time.sleep(0.3)

    # Haken setzen bei "Enable ActiveX and Socket Clients"
    subprocess.call(['xdotool', 'key', 'space']); time.sleep(0.5)

    # Tab zum Trusted IP-Feld
    for _ in range(3):
        subprocess.call(['xdotool', 'key', 'Tab']); time.sleep(0.3)

    # Trusted IP eintragen
    subprocess.call(['xdotool', 'type', '127.0.0.1']); time.sleep(0.5)

    # OK klicken
    subprocess.call(['xdotool', 'key', 'Return']); time.sleep(1)


def main():
    start_xvfb()
    proc = launch_gateway()

    # Warte bis Login-Fenster erscheint
    time.sleep(10)
    totp = pyotp.TOTP(SECRET).now()
    send_keystrokes(totp)

    # API-Konfiguration durchführen
    configure_api()

    # Warte, bis Gateway weiterläuft
    proc.wait()


if __name__ == '__main__':
    main()