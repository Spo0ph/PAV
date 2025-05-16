#!/usr/bin/env python3
import os, time, subprocess
import pyotp

# Umgebungsvariablen
LOGIN     = os.environ["IBKR_LOGIN"]
PASSWORD  = os.environ["IBKR_PASSWORD"]
SECRET    = os.environ["IBKR_TOTP_SECRET"]
GATEWAY   = "/root/Jts/ibgateway/1030/ibgateway"
XVFB_DISP = os.environ.get("DISPLAY", ":0")

def start_xvfb():
    # Starte Xvfb, falls noch nicht da
    subprocess.Popen([
        "Xvfb", XVFB_DISP, "-ac", "-screen", "0", "1024x768x24"
    ])
    os.environ["DISPLAY"] = XVFB_DISP
    time.sleep(3)

def launch_gateway():
    # Starte IB Gateway GUI
    return subprocess.Popen([GATEWAY, "-role", "gateway"])

def send_keystrokes(code):
    # Fokussiere das Fenster und tippe Daten ein
    # Wir geben jeweils ein kleines Sleep dazwischen, damit das Fenster reagiert.
    subprocess.call(["xdotool", "search", "--name", "IB Gateway", "windowactivate", "--sync"])
    time.sleep(1)
    subprocess.call(["xdotool", "type", LOGIN]);      time.sleep(0.5)
    subprocess.call(["xdotool", "key", "Tab"]);       time.sleep(0.5)
    subprocess.call(["xdotool", "type", PASSWORD]);   time.sleep(0.5)
    subprocess.call(["xdotool", "key", "Tab"]);       time.sleep(0.5)
    subprocess.call(["xdotool", "type", code]);       time.sleep(0.5)
    subprocess.call(["xdotool", "key", "Return"])

def main():
    start_xvfb()
    proc = launch_gateway()
    # Warte bis das Login-Fenster erschienen ist
    time.sleep(10)
    # Code erzeugen und eintippen
    totp = pyotp.TOTP(SECRET).now()
    send_keystrokes(totp)
    # Optional: warte bis Login durch ist
    proc.wait()

if __name__ == "__main__":
    main()