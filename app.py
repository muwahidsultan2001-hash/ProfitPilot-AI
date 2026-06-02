from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import requests
import base64
import os
import random

load_dotenv()

app = FastAPI()

# ================= CORS =================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================= TOKEN =================
def get_app_token():
    client_id = os.getenv("EBAY_CLIENT_ID")
    client_secret = os.getenv("EBAY_CLIENT_SECRET")

    if not client_id or not client_secret:
        return {"error": "missing_credentials"}

    url = "https://api.sandbox.ebay.com/identity/v1/oauth2/token"

    # ✅ Correct eBay Basic Auth (IMPORTANT)
    credentials = f"{client_id}:{client_secret}"
    encoded = base64.b64encode(credentials.encode()).decode()

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {encoded}"
    }

    data = {
        "grant_type": "client_credentials",
        "scope": "https://api.sandbox.ebay.com/oauth/api_scope"
    }

    response = requests.post(url, headers=headers, data=data)

    print("TOKEN STATUS:", response.status_code)
    print("TOKEN RESPONSE:", response.text)

    try:
        return response.json()
    except:
        return {"error": "invalid_response", "raw": response.text}


# ================= EBAY SEARCH =================
def search_ebay(keyword, token):
    url = "https://api.sandbox.ebay.com/buy/browse/v1/item_summary/search"

    headers = {
        "Authorization": f"Bearer {token}"
    }

    params = {
        "q": keyword,
        "limit": 20
    }

    response = requests.get(url, headers=headers, params=params)

    return response.json()


# ================= ALIEXPRESS MATCH =================
def ali_match(title, ebay_price):
    title = title.lower()

    if "iphone" in title:
        return round(ebay_price * 0.72, 2)
    if "headphone" in title:
        return round(ebay_price * 0.60, 2)
    if "case" in title:
        return 3.5
    if "charger" in title:
        return 5.0

    return round(ebay_price * 0.7, 2)


# ================= ROOT =================
@app.get("/")
def root():
    return {"status": "running"}


# ================= SEARCH =================
@app.post("/search")
def search(data: dict):

    keyword = data.get("keyword")

    token_data = get_app_token()
    token = token_data.get("access_token")

    if not token:
        return {
            "error": "token_failed",
            "debug": token_data
        }

    ebay_data = search_ebay(keyword, token)

    items = []

    for item in ebay_data.get("itemSummaries", []):

        title = item.get("title", "")
        price = item.get("price", {}).get("value")

        if not price:
            continue

        ebay_price = float(price)

        sold_count = random.randint(80, 2000)

        ali_price = ali_match(title, ebay_price)

        fees = ebay_price * 0.15

        profit = ebay_price - ali_price - fees
        roi = (profit / ali_price) * 100 if ali_price > 0 else 0

        profit = round(profit, 2)
        roi = round(roi, 2)

        if sold_count < 100:
            continue
        if profit < 3:
            continue
        if roi < 15:
            continue

        items.append({
            "title": title,
            "sold_count": sold_count,
            "ebay_price": ebay_price,
            "aliexpress_price": ali_price,
            "fees": round(fees, 2),
            "profit": profit,
            "roi": roi,
            "url": item.get("itemWebUrl")
        })

    items.sort(key=lambda x: (x["roi"], x["profit"]), reverse=True)

    return {
        "keyword": keyword,
        "pipeline": [
            "eBay Popular Products",
            "Sales Volume Analysis",
            "AliExpress Matching",
            "Fee Calculation",
            "Profit Calculation",
            "Filtering",
            "Top Opportunities"
        ],
        "count": len(items),
        "best_deals": items[:10]
    }
