
# ╔══════════════════════════════════════════════════════════════════╗
# ║   🌾  Price Agent - Integrated Crop Price Advisor                ║
# ║   Fetches live vegetable & fruit prices & predicts next day      ║
# ║   Combines retail scraping + mandi API + ML prediction           ║
# ╚══════════════════════════════════════════════════════════════════╝

import logging
import json
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import numpy as np
import re
import time
import warnings
from typing import Dict, Any, Optional, List, Tuple

warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────────────────────────

API_KEY = "579b464db66ec23bdd0000017a052f2fb00d426858a04c9fc0f0ec86"
API_URL = "https://api.data.gov.in/resource/35985678-0d79-46b4-9ed6-6f13308a1d24"

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"),
    "Accept-Language": "en-IN,en;q=0.9",
}

HISTORY_DAYS = 10
MANDI_STALE_DAYS = 180

# ── Commodity Aliases ─────────────────────────────────────────────

COMMODITY_ALIASES = {
    "apple": ["Apple Washington", "Apple Shimla", "Apple Green", "Apple (Red)", "Apple"],
    "tomato": ["Tomato", "Tomato (Local)", "Tomato (Hybrid)"],
    "onion": ["Onion", "Onion (Big)", "Onion (Small)", "Kanda"],
    "potato": ["Potato", "Potato (Local)"],
    "banana": ["Banana", "Banana (Robusta)", "Banana (Poovan)", "Banana (Nendran)"],
    "orange": ["Orange", "Orange (Nagpur)", "Mosambi", "Sweet Lime"],
    "grapes": ["Grapes", "Grapes (Green)", "Grapes Black"],
    "mango": ["Mango", "Mango (Totapuri)", "Mango Alphonso"],
    "papaya": ["Papaya", "Papaya (Raw)", "Papaya (Ripe)"],
    "pomegranate": ["Pomegranate", "Pomegranate Kabul"],
    "guava": ["Guava"],
    "pineapple": ["Pineapple"],
    "watermelon": ["Water Melon", "Watermelon"],
    "beans": ["Beans", "Cluster Beans", "French Beans", "Broad Beans"],
    "carrot": ["Carrot"],
    "cabbage": ["Cabbage"],
    "brinjal": ["Brinjal", "Brinjal (Round)", "Brinjal (Long)", "Baingan"],
    "ladiesfinger": ["Ladies finger", "Bhindi", "Okra"],
    "ladyfinger": ["Ladies finger", "Bhindi", "Okra"],
    "bhindi": ["Bhindi", "Ladies finger", "Okra"],
    "cauliflower": ["Cauliflower"],
    "bittergourd": ["Bitter Gourd", "Karela"],
    "drumstick": ["Drumstick"],
    "coconut": ["Coconut", "Coconut (Big)"],
    "ginger": ["Ginger", "Ginger (Green)", "Ginger (Dry)"],
    "garlic": ["Garlic", "Garlic (Dry)"],
    "lemon": ["Lemon", "Lemon (Large)"],
    "capsicum": ["Capsicum", "Shimla Mirch"],
    "cucumber": ["Cucumber"],
    "pumpkin": ["Pumpkin"],
    "ashgourd": ["Ash Gourd", "White Pumpkin"],
    "snakegourd": ["Snake Gourd"],
    "ridgegourd": ["Ridge Gourd", "Turai"],
    "yam": ["Yam", "Yam (White)"],
    "tapioca": ["Tapioca"],
    "chilly": ["Chilly (Dry)", "Green Chilly", "Chilli"],
    "chilli": ["Green Chilly", "Chilly (Dry)", "Chilli"],
}

FRUIT_COMMODITIES = {
    "apple", "orange", "mosambi", "mango", "banana", "grapes", "papaya",
    "guava", "pineapple", "watermelon", "pomegranate", "lemon", "sapota",
    "jackfruit", "coconut", "fig", "avocado", "kiwi", "strawberry",
    "plum", "peach", "pear", "apricot", "cherry", "dates", "litchi",
    "custard apple", "sitaphal", "chikoo", "amla", "tamarind",
}

STATE_DISTRICTS = {
    "kerala": ["thiruvananthapuram", "kollam", "pathanamthitta", "alappuzha", "kottayam",
               "idukki", "ernakulam", "thrissur", "palakkad", "malappuram", "kozhikode",
               "wayanad", "kannur", "kasaragod"],
    "tamil nadu": ["chennai", "coimbatore", "madurai", "trichy", "salem", "tirunelveli",
                   "vellore", "erode", "tiruppur", "dindigul", "thanjavur", "kancheepuram",
                   "namakkal", "dharmapuri"],
    "karnataka": ["bengaluru", "mysuru", "hubli", "mangaluru", "belgaum", "tumkur",
                  "shimoga", "davanagere", "bellary", "gulbarga"],
    "maharashtra": ["mumbai", "pune", "nagpur", "nashik", "thane", "aurangabad",
                    "solapur", "kolhapur", "akola", "latur"],
    "andhra pradesh": ["vijayawada", "visakhapatnam", "guntur", "nellore", "kurnool",
                       "kadapa", "anantapur", "tirupati", "rajahmundry"],
    "telangana": ["hyderabad", "warangal", "nizamabad", "khammam", "karimnagar",
                  "medchal", "nalgonda", "mahbubnagar"],
    "gujarat": ["ahmedabad", "surat", "vadodara", "rajkot", "bhavnagar", "jamnagar",
                "junagadh", "anand", "mehsana"],
    "west bengal": ["kolkata", "howrah", "hooghly", "burdwan", "nadia", "murshidabad",
                    "malda", "jalpaiguri"],
    "uttar pradesh": ["lucknow", "agra", "kanpur", "allahabad", "varanasi", "meerut",
                      "ghaziabad", "mathura", "bareilly"],
    "delhi": ["delhi", "new delhi", "south delhi", "north delhi"],
    "punjab": ["amritsar", "ludhiana", "jalandhar", "patiala", "bathinda"],
    "rajasthan": ["jaipur", "jodhpur", "udaipur", "kota", "ajmer", "bikaner"],
    "madhya pradesh": ["bhopal", "indore", "gwalior", "jabalpur", "ujjain"],
    "haryana": ["gurugram", "faridabad", "ambala", "hisar", "rohtak", "panipat"],
    "odisha": ["bhubaneswar", "cuttack", "rourkela", "puri", "sambalpur"],
    "bihar": ["patna", "gaya", "muzaffarpur", "bhagalpur", "darbhanga"],
}

# ── Helper Functions ──────────────────────────────────────────────

def get_commodity_variants(commodity: str) -> List[str]:
    """Get API-recognized names for a user-typed crop name"""
    c = commodity.lower().strip()
    for key, variants in COMMODITY_ALIASES.items():
        if c == key or c in key or key in c:
            return variants
    return [commodity.title(), commodity.strip()]

def extract_price_clean(text: str) -> Optional[float]:
    """Extract first valid price number from text"""
    text = text.replace("₹", "")
    nums = re.findall(r"\d+\.?\d*", text)
    nums = [float(n) for n in nums if float(n) > 5]
    return nums[0] if nums else None

def extract_max_price(text: str) -> Optional[float]:
    """Extract last (highest) price number from text"""
    text = text.replace("₹", "")
    nums = re.findall(r"\d+\.?\d*", text)
    nums = [float(n) for n in nums if float(n) > 5]
    return nums[-1] if nums else None

def get_state_slug(s: str) -> str:
    """Convert state/district name to URL-friendly slug"""
    return s.lower().replace(" ", "")

def is_fruit(c: str) -> bool:
    """Check if commodity is a fruit"""
    return c.lower().strip() in FRUIT_COMMODITIES

def name_matches_commodity(name_cell: str, commodity: str, variants: List[str]) -> bool:
    """Check if table row name matches commodity"""
    n = name_cell.lower().strip()
    c = commodity.lower().strip()
    if c in n:
        return True
    for v in variants:
        if v.lower() in n:
            return True
        fw = v.split()[0].lower()
        if fw == c and fw in n:
            return True
    return False

# ── Step 1: Retail Price Scraping ─────────────────────────────────

def scrape_today_page(url: str, commodity: str, variants: List[str]) -> Optional[Dict]:
    """Fetch and parse vegetablemarketprice.com for today's retail price"""
    try:
        r = requests.get(url, headers=HEADERS, timeout=12)
        if r.status_code != 200:
            return None
        soup = BeautifulSoup(r.text, "lxml")
        for row in soup.select("table tbody tr"):
            cols = row.find_all("td")
            if len(cols) < 3:
                continue
            name_cell = cols[1].text.strip() if len(cols) > 1 else cols[0].text.strip()
            if not name_matches_commodity(name_cell, commodity, variants):
                continue
            min_p = extract_price_clean(cols[2].text) if len(cols) > 2 else None
            max_p = extract_max_price(cols[3].text) if len(cols) > 3 else None
            if not max_p:
                max_p = min_p
            avg_p = round((min_p + max_p) / 2, 2) if (min_p and max_p) else min_p
            if not avg_p:
                continue
            return {
                "name": name_cell,
                "min": min_p,
                "max": max_p,
                "avg": avg_p,
                "date": datetime.now()
            }
    except Exception as e:
        logger.debug(f"Scraping error for {url}: {e}")
    return None


def fetch_agmarknet(state: str, district: str, commodity: str) -> Optional[pd.DataFrame]:
    """Attempt to fetch recent wholesale prices from Agmarknet by scraping.

    This is a best-effort scraper: Agmarknet layout may change, so the function
    tries a few likely pages and extracts a table of arrival dates and modal
    prices, returning a pandas DataFrame similar to `fetch_mandi`.
    """
    try:
        variants = get_commodity_variants(commodity)
        state_slug = get_state_slug(state) if state else ""
        district_slug = get_state_slug(district) if district else ""

        candidates = []
        # Market-level pages
        if district_slug:
            candidates.append(f"https://agmarknet.gov.in/MarketwiseReport/MonthwiseArrival.aspx?MarketName={district_slug}")
        if state_slug:
            candidates.append(f"https://agmarknet.gov.in/MarketwiseReport/MonthwiseArrival.aspx?StateName={state_slug}")
        # Generic commodity search
        candidates.append(f"https://agmarknet.gov.in/SearchCmmResult/AdvanceSearch?Comm={commodity}")

        for url in candidates:
            try:
                r = requests.get(url, headers=HEADERS, timeout=12)
                if r.status_code != 200:
                    continue
                soup = BeautifulSoup(r.text, "lxml")
                # Find tables with prices
                table = soup.find("table")
                if not table:
                    continue
                rows = []
                for tr in table.find_all("tr"):
                    cols = [td.get_text(strip=True) for td in tr.find_all(["td","th"])]
                    if not cols or len(cols) < 2:
                        continue
                    rows.append(cols)
                if not rows:
                    continue
                # Try to infer columns (look for date and price columns)
                # Flatten rows into records where possible
                records = []
                for rrow in rows[1:]:
                    # heuristic: last numeric column is price
                    nums = [re.findall(r"\d+\.?\d*", c) for c in rrow]
                    price = None
                    date = None
                    for idx, c in enumerate(reversed(rrow)):
                        if re.search(r"\d{1,2}[-/ ]\w+[-/ ]\d{2,4}", c) or re.search(r"\d{4}-\d{2}-\d{2}", c):
                            date = c
                            break
                        if re.search(r"\d+", c) and not price:
                            price = extract_price_clean(c)
                    if price is None:
                        continue
                    # If date missing use today
                    try:
                        parsed_date = pd.to_datetime(date, errors="coerce") if date else datetime.now()
                    except Exception:
                        parsed_date = datetime.now()
                    records.append({"Arrival_Date": parsed_date, "Modal_Price": float(price)})
                if not records:
                    continue
                df = pd.DataFrame(records)
                df = df.sort_values("Arrival_Date", ascending=False).head(HISTORY_DAYS).reset_index(drop=True)
                return df
            except Exception:
                continue
    except Exception as e:
        logger.debug(f"Agmarknet fetch error: {e}")
    return None

def get_retail_price(state: str, commodity: str, district: Optional[str] = None) -> Optional[Dict]:
    """Try to find today's retail price from vegetablemarketprice.com"""
    state_slug = get_state_slug(state)
    district_slug = get_state_slug(district) if district else None
    variants = get_commodity_variants(commodity)
    fruit = is_fruit(commodity)

    urls = []
    if fruit:
        urls += [f"https://vegetablemarketprice.com/fruits/{state_slug}/today"]
        if district_slug:
            urls += [f"https://vegetablemarketprice.com/fruits/{district_slug}/today"]
    else:
        if district_slug:
            urls += [f"https://vegetablemarketprice.com/market/{district_slug}/today"]
        urls += [f"https://vegetablemarketprice.com/market/{state_slug}/today",
                 f"https://vegetablemarketprice.com/fruits/{state_slug}/today"]

    for url in urls:
        r = scrape_today_page(url, commodity, variants)
        if r:
            return r
        time.sleep(0.2)

    # Fallback to other districts in same state
    if not fruit and district:
        for fb in STATE_DISTRICTS.get(state.lower().strip(), []):
            fb_slug = fb.replace(" ", "")
            if fb_slug == district_slug:
                continue
            for u in [f"https://vegetablemarketprice.com/market/{fb_slug}/today",
                      f"https://vegetablemarketprice.com/fruits/{fb_slug}/today"]:
                r = scrape_today_page(u, commodity, variants)
                if r:
                    r["fallback_district"] = fb.title()
                    return r
            time.sleep(0.2)

    return None

# ── Step 2: Mandi API ─────────────────────────────────────────────

def fetch_mandi(state: str, district: str, commodity: str) -> Optional[pd.DataFrame]:
    """Fetch last 10 days of mandi prices from data.gov.in API"""
    variants = get_commodity_variants(commodity)
    cutoff = datetime.now() - timedelta(days=MANDI_STALE_DAYS)
    filter_sets = []

    for v in variants:
        filter_sets.append({
            "filters[State]": state.title(),
            "filters[District]": district.title(),
            "filters[Commodity]": v
        })
    for v in variants:
        filter_sets.append({
            "filters[State]": state.title(),
            "filters[Commodity]": v
        })

    for filters in filter_sets:
        params = {
            "api-key": API_KEY,
            "format": "json",
            "limit": 5000,
            "sort[Arrival_Date]": "desc"
        }
        params.update(filters)

        try:
            r = requests.get(API_URL, params=params, timeout=15, headers=HEADERS)
            if r.status_code != 200:
                continue
            records = r.json().get("records", [])
            if not records:
                continue

            df = pd.DataFrame(records)
            col_map = {}
            for c in df.columns:
                cl = c.lower()
                if cl == "arrival_date":
                    col_map[c] = "Arrival_Date"
                elif cl == "modal_price":
                    col_map[c] = "Modal_Price"
                elif cl == "min_price":
                    col_map[c] = "Min_Price"
                elif cl == "max_price":
                    col_map[c] = "Max_Price"
            df = df.rename(columns=col_map)

            if "Arrival_Date" not in df.columns or "Modal_Price" not in df.columns:
                continue

            df["Arrival_Date"] = pd.to_datetime(df["Arrival_Date"], errors="coerce", dayfirst=True)
            df["Modal_Price"] = pd.to_numeric(df["Modal_Price"], errors="coerce")
            if "Min_Price" in df.columns:
                df["Min_Price"] = pd.to_numeric(df["Min_Price"], errors="coerce")
            if "Max_Price" in df.columns:
                df["Max_Price"] = pd.to_numeric(df["Max_Price"], errors="coerce")

            df = df.dropna(subset=["Arrival_Date", "Modal_Price"])
            if df.empty:
                continue

            latest_date = df["Arrival_Date"].max()
            if latest_date < cutoff:
                continue

            df = df[df["Arrival_Date"] >= cutoff]
            grouped = (df.groupby("Arrival_Date")
                         .agg(
                             Modal_Price=("Modal_Price", "mean"),
                             Min_Price=("Min_Price", "mean") if "Min_Price" in df.columns else ("Modal_Price", "mean"),
                             Max_Price=("Max_Price", "mean") if "Max_Price" in df.columns else ("Modal_Price", "mean")
                         )
                         .reset_index()
                         .sort_values("Arrival_Date", ascending=False))

            return grouped.head(HISTORY_DAYS).reset_index(drop=True)

        except Exception as e:
            logger.debug(f"Mandi API error: {e}")
            continue

    return None

# ── Step 3: Compute Final Price ───────────────────────────────────

def compute_final_price(retail: Optional[Dict], mandi_df: Optional[pd.DataFrame]) -> Tuple[Optional[Dict], Optional[float], Optional[datetime]]:
    """Decide what price to show based on retail + mandi data"""
    mandi_latest_kg = None
    mandi_latest_date = None

    if mandi_df is not None and not mandi_df.empty:
        row = mandi_df.iloc[0]
        mandi_latest_date = row["Arrival_Date"]
        mandi_modal_kg = round(float(row["Modal_Price"]) / 100, 2)
        mandi_latest_kg = mandi_modal_kg

    if retail and mandi_latest_kg:
        r_min = retail["min"]
        r_max = retail["max"]
        days_diff = abs((retail["date"] - mandi_latest_date).days)

        if days_diff > 7:
            return (
                {"type": "range", "low": r_min, "high": r_max,
                 "avg": round((r_min + r_max) / 2, 2)},
                mandi_latest_kg, mandi_latest_date
            )

        if r_min <= mandi_latest_kg <= r_max:
            return (
                {"type": "range", "low": r_min, "high": r_max,
                 "avg": round((r_min + r_max) / 2, 2)},
                mandi_latest_kg, mandi_latest_date
            )

        elif mandi_latest_kg > r_max:
            blended = round((mandi_latest_kg + r_max) / 2, 2)
            return (
                {"type": "exact", "value": blended},
                mandi_latest_kg, mandi_latest_date
            )

        else:
            blended = round((mandi_latest_kg + r_min) / 2, 2)
            return (
                {"type": "exact", "value": blended},
                mandi_latest_kg, mandi_latest_date
            )

    elif retail:
        r_min = retail["min"]
        r_max = retail["max"]
        return (
            {"type": "range", "low": r_min, "high": r_max,
             "avg": round((r_min + r_max) / 2, 2)},
            None, None
        )

    elif mandi_latest_kg:
        return (
            {"type": "exact", "value": mandi_latest_kg},
            mandi_latest_kg, mandi_latest_date
        )

    return None, None, None

# ── Step 4: Predict Next Day ──────────────────────────────────────

def predict_next_day(prices: List[float]) -> Dict[str, Any]:
    """Predict tomorrow's price using Linear Regression + Weighted Moving Average"""
    clean = [p for p in prices if p is not None and not np.isnan(p)]

    if len(clean) < 2:
        return {
            "prediction": None,
            "valid": len(clean),
            "trend": None,
            "slope": 0,
            "price_min": None,
            "price_max": None
        }

    y = np.array(clean, dtype=float)
    x = np.arange(len(y), dtype=float)
    n = len(y)

    slope = (n * np.dot(x, y) - x.sum() * y.sum()) / (n * np.dot(x, x) - x.sum() ** 2)
    intercept = (y.sum() - slope * x.sum()) / n
    lr_pred = slope * n + intercept

    w = np.array([2 ** i for i in range(n)])
    wma_pred = np.dot(w, y) / w.sum()
    wma_pred += (y[-1] - y[0]) / n

    final = max(0.0, round(0.6 * lr_pred + 0.4 * wma_pred, 2))
    trend = "rising" if slope > 0.3 else ("falling" if slope < -0.3 else "stable")

    return {
        "prediction": final,
        "trend": trend,
        "slope": round(slope, 4),
        "valid": n,
        "price_min": round(float(np.min(y)), 2),
        "price_max": round(float(np.max(y)), 2),
    }

# ── Step 5: Generate Advice ───────────────────────────────────────

def generate_advice(final_display: Optional[Dict], pred: Dict, today_avg: Optional[float]) -> Dict[str, Any]:
    """Generate sell/wait advice based on price prediction"""
    advice = {
        "today_price": None,
        "tomorrow_price": None,
        "advice": None,
        "confidence": "low"
    }

    if final_display is None:
        advice["advice"] = "No price data available. Monitor for a few more days."
        return advice

    if final_display["type"] == "range":
        advice["today_price"] = f"₹{final_display['low']:.0f} – ₹{final_display['high']:.0f}/kg"
    else:
        advice["today_price"] = f"₹{final_display['value']:.2f}/kg"

    if pred["prediction"] is None or pred["valid"] < 2:
        advice["tomorrow_price"] = "Unable to predict"
        advice["advice"] = "Not enough historical data. Monitor for a few more days before selling."
        advice["confidence"] = "very_low"
        return advice

    pred_p = pred["prediction"]
    ref_today = today_avg or (final_display.get("avg") or final_display.get("value") or pred_p)
    pct_change = ((pred_p - ref_today) / ref_today * 100) if ref_today else 0

    advice["tomorrow_price"] = f"₹{pred_p:.2f}/kg"

    if pct_change > 2:
        trend = "rising"
        advice["advice"] = f"Prices expected to RISE by ~{pct_change:.1f}%. Consider waiting to sell for a better price."
        advice["confidence"] = "high"
    elif pct_change < -2:
        trend = "falling"
        advice["advice"] = f"Prices expected to FALL by ~{abs(pct_change):.1f}%. Better to sell TODAY at ₹{ref_today:.1f}/kg."
        advice["confidence"] = "high"
    else:
        trend = "stable"
        advice["advice"] = "Price is STABLE. Sell today or wait — little change expected."
        advice["confidence"] = "medium"

    return advice

# ── Main Price Agent Class ────────────────────────────────────────

class PriceAgentNode:
    """Price Agent - Provides market price information and selling advice"""
    
    def __init__(self):
        logger.info("PriceAgentNode initialized")
    
    def process(self, crop: str, state: str = "", district: str = "") -> Dict[str, Any]:
        """
        Process price information request
        
        Args:
            crop: Crop name (e.g., 'tomato')
            state: State name (optional, e.g., 'Kerala')
            district: District name (optional, e.g., 'Ernakulam')
            
        Returns:
            Dict with price info, prediction, and selling advice
        """
        logger.info(f"PriceAgent processing: crop={crop}, state={state}, district={district}")
        
        try:
            # Step 1: Fetch retail price (web scraping)
            retail = get_retail_price(state, crop, district) if (state and district) else None
            # capture display name / variety if available
            display_name = None
            if retail and isinstance(retail, dict):
                display_name = retail.get("name")
            
            # Step 2: Fetch mandi/wholesale price history (prefer Agmarknet, then data.gov.in)
            mandi_df = None
            if state and district:
                agm = fetch_agmarknet(state, district, crop)
                if agm is not None and not agm.empty:
                    mandi_df = agm
                else:
                    mandi_df = fetch_mandi(state, district, crop)
            
            # Step 3: Compute final display price
            final_display, mandi_latest_kg, mandi_latest_date = compute_final_price(retail, mandi_df)
            
            # Step 4: Build price history for prediction
            history_prices = []
            if mandi_df is not None and not mandi_df.empty:
                df_asc = mandi_df.sort_values("Arrival_Date")
                history_prices = [round(p / 100, 2) for p in df_asc["Modal_Price"].tolist()]
            
            # Step 5: Make prediction
            pred = predict_next_day(history_prices)
            
            # Step 6: Get today's reference price
            today_avg = None
            if final_display:
                today_avg = (final_display.get("avg") if final_display["type"] == "range" 
                           else final_display.get("value"))
            
            # Step 7: Generate advice
            advice = generate_advice(final_display, pred, today_avg)
            
            result = {
                "crop": crop,
                "commodity_display": display_name or crop,
                "state": state,
                "district": district,
                "timestamp": datetime.now().isoformat(),
                "current_price": advice["today_price"],
                "predicted_price": advice["tomorrow_price"],
                "price_trend": "rising" if pred.get("slope", 0) > 0.3 else ("falling" if pred.get("slope", 0) < -0.3 else "stable"),
                "selling_advice": advice["advice"],
                "confidence": advice["confidence"],
                "historical_data_points": pred.get("valid", 0),
                "price_range": {
                    "min": pred.get("price_min"),
                    "max": pred.get("price_max")
                },
                "sources": {
                    "retail_price": "vegetablemarketprice.com",
                    "mandi_price": "data.gov.in",
                    "prediction_method": "Ensemble (60% Linear Regression + 40% Weighted Moving Average)"
                },
                "agent": "price_agent"
            }
            
            logger.info(f"PriceAgent output: {result}")
            return result
            
        except Exception as e:
            logger.error(f"PriceAgent error: {e}")
            return {
                "crop": crop,
                "error": str(e),
                "selling_advice": f"Unable to fetch price data: {str(e)}",
                "agent": "price_agent"
            }
