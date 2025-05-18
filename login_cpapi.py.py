#!/opt/ibgateway-venv/bin/python
import os, requests, pyotp, urllib3
urllib3.disable_warnings()  # für self-signed cert

BASE = "https://localhost:5000/v1/api"
USER = os.environ["IBKR_LOGIN"]
PWD  = os.environ["IBKR_PASSWORD"]
SEC  = os.environ["IBKR_TOTP_SECRET"]

s = requests.Session()
# 1) Status prüfen
r = s.get(f"{BASE}/iserver/auth/status", verify=False)
if r.json().get("isAuthenticated"):
    print("Schon eingeloggt.")
    exit(0)

# 2) Login
r = s.post(f"{BASE}/iserver/auth/login", json={"user":USER,"password":PWD}, verify=False)
r.raise_for_status()

# 3) 2FA mit TOTP
code = pyotp.TOTP(SEC).now()
r = s.post(f"{BASE}/iserver/auth/2fa", json={"code": code}, verify=False)
r.raise_for_status()

print("Login via CPAPI+TOTP erfolgreich.")