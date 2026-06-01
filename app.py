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

    credentials = f"{client_id}:{client_secret}"
    encoded = base64.b64encode(credentials.encode()).decode()

    # ✅ PRODUCTION URL
    url = "https://api.ebay.com/identity/v1/oauth2/token"

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {encoded}"
    }

    data = {
        "grant_type": "client_credentials",
        "scope": "https://api.ebay.com/oauth/api_scope"
    }

    response = requests.post(url, headers=headers, data=data)

    try:
        return response.json()
    except:
        return {
            "error": "invalid_response",
            "raw": response.text
        }


# ================= EBAY SEARCH =================
def search_ebay(keyword, token):
    # ✅ PRODUCTION URL
    url = "https://api.ebay.com/buy/browse/v1/item_summary/search"

    headers = {
        "Authorization": f"Bearer {token}"
    }

    params = {
        "q": keyword,
        "limit": 20
    }

    response = requests.get(url, headers=headers, params=params)
    return response.json()


# ================= ALIEXPRESS MATCH (SIMULATION) =================
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


# ================= MAIN PIPELINE =================
@app.post("/search")
def search(data: dict):

    keyword = data.get("keyword")

    # ================= TOKEN =================
    token_data = get_app_token()
    token = token_data.get("access_token")

    if not token:
        return {
            "error": "token_failed",
            "debug": token_data
        }

    # ================= EBAY DATA =================
    ebay_data = search_ebay(keyword, token)

    items = []

    for item in ebay_data.get("itemSummaries", []):

        title = item.get("title", "")
        price = item.get("price", {}).get("value")

        if not price:
            continue

        ebay_price = float(price)

        # ================= SIMULATED SALES =================
        sold_count = random.randint(80, 2000)

        # ================= ALI MATCH =================
        ali_price = ali_match(title, ebay_price)

        # ================= FEES =================
        ebay_fee = ebay_price * 0.12
        payment_fee = ebay_price * 0.03
        total_fees = ebay_fee + payment_fee

        # ================= PROFIT =================
        profit = ebay_price - ali_price - total_fees
        roi = (profit / ali_price) * 100 if ali_price > 0 else 0

        profit = round(profit, 2)
        roi = round(roi, 2)

        # ================= FILTER =================
        if sold_count < 100:
            continue
        if profit < 3:
            continue
        if roi < 15:
            continue

        # ================= OUTPUT =================
        items.append({
            "title": title,
            "sold_count": sold_count,
            "ebay_price": ebay_price,
            "aliexpress_price": ali_price,
            "fees": round(total_fees, 2),
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