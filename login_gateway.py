import time
import subprocess
import pyotp
import xml.etree.ElementTree as ET
import os

# --- Konfiguration ---
IBG_ROOT    = r"C:\Jts\ibgateway\1030"
SETTINGS    = os.path.join(IBG_ROOT, "config", "ibgsettings.xml")
GATEWAY_EXE = os.path.join(IBG_ROOT, "ibgateway.exe")

USERNAME = "conradfritsche"
PASSWORD = "hofdyx-vemtis-1rYsmo"
SECRET   = "D7L4QKHUXPT50ESK2MAHAQ0655EZE3JK"  # Base32-Secret aus deinem IBKR-Konto

# 1) TOTP-Code generieren
totp     = pyotp.TOTP(SECRET)
otp_code = totp.now()
print(f"Generierter TOTP: {otp_code}")

# 2) ibgsettings.xml updaten
tree = ET.parse(SETTINGS)
root = tree.getroot()

# Im XML gibt es Tags <username>, <password> und <otp>
for tag, value in [("username", USERNAME), ("password", PASSWORD), ("otp", otp_code)]:
    elem = root.find(f".//{tag}")
    if elem is not None:
        elem.text = value
    else:
        # Falls der Tag fehlt, neu anlegen
        new = ET.SubElement(root, tag)
        new.text = value

tree.write(SETTINGS, encoding="utf-8", xml_declaration=True)
print("Einstellungen in ibgsettings.xml aktualisiert.")

# 3) Gateway starten
subprocess.Popen([GATEWAY_EXE])
print("IB Gateway wird gestartet…")
