import os
import requests
from requests_oauthlib import OAuth1

# Secrets aus Umgebungsvariablen
CK = os.environ['CONSUMER_KEY']
AT = os.environ['ACCESS_TOKEN']
AS = os.environ['ACCESS_TOKEN_SECRET']

# Step 1: Live Session Token holen (LST)
lst_auth = OAuth1(
    CK,
    resource_owner_key=AT,
    resource_owner_secret=AS,
    signature_method='HMAC-SHA1'
)

res = requests.post("https://api.ibkr.com/v1/api/oauth/live_session_token", auth=lst_auth)
lst = res.json()
SESSION_SECRET = lst['live_session_token_signature']

# Step 2: API-Zugriff mit LST
auth = OAuth1(
    CK,
    resource_owner_key=AT,
    resource_owner_secret=SESSION_SECRET,
    signature_method='HMAC-SHA1'
)

# Konto-ID abrufen
acc_req = requests.get("https://api.ibkr.com/v1/api/portfolio/accounts", auth=auth)
account_id = acc_req.json()[0]['accountId']

# Kontosaldo abrufen
summary = requests.get(f"https://api.ibkr.com/v1/api/portfolio/{account_id}/summary", auth=auth).json()
equity = next((item['value'] for item in summary if item['tag'] == 'NetLiquidation'), None)

print(f"Account ID: {account_id}")
print(f"Geldwert im Konto (NetLiquidation): {equity} USD")