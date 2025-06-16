import pyotp
import base64
import sys

# ⛔ WICHTIG: Ersetze den folgenden Secret-String durch deinen 32-stelligen Base32-TOTP-Secret
secret = "XUWCU7OB43FXJRFZQ3FN73AKELW4ITLS"  # Beispielwert (gültig, 32 Base32-Zeichen)

def is_valid_base32(s):
    try:
        base64.b32decode(s, casefold=True)
        return True
    except Exception as e:
        print("❌ Ungültiger Base32-String:", e)
        return False

def generate_otp(s):
    try:
        totp = pyotp.TOTP(s)
        return totp.now()
    except Exception as e:
        print("❌ Fehler beim Erzeugen des TOTP-Codes:", e)
        return None

def main():
    print("🔐 TOTP-Generator für IBKR / pyotp\n")

    print(f"📦 Secret: {secret}\n")

    if not is_valid_base32(secret):
        print("🚫 Abbruch: Secret ist kein gültiger Base32-String.")
        sys.exit(1)

    otp = generate_otp(secret)

    if otp:
        print(f"✅ Aktueller OTP-Code: {otp}")
    else:
        print("🚫 OTP konnte nicht generiert werden.")

if __name__ == "__main__":
    main()
