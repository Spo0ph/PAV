#!/usr/bin/env python3
from ibind import IbkrClient

def main():
    # Client verbindet sich standardmäßig mit http://localhost:5000
    client = IbkrClient()

    # Health-Check
    print("Gateway Health:", client.check_health().data)

    # Auth-Status („tickle“ hält Session lebendig)
    status = client.tickle().data
    print("Auth Status:", status)

    # Accounts auslesen
    accounts = client.portfolio_accounts().data.get("accounts", [])
    print("Accounts:", accounts)

    # Beispiel: Daten zu deinem ersten Account holen
    if accounts:
        acct_id = accounts[0]
        summary = client.account_summary(acct_id).data
        print(f"Account Summary for {acct_id}:", summary)
    else:
        print("Keine Accounts gefunden.")

if __name__ == "__main__":
    main()