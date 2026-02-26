# ╔══════════════════════════════════════════════════════════════════╗
# ║   🌾  Crop Price Advisor for Farmers                            ║
# ║   Fetches live vegetable & fruit prices — farmer-focused output ║
# ║   Google Colab Compatible                                       ║
# ╚══════════════════════════════════════════════════════════════════╝
#
# HOW IT WORKS:
#   Step 1 → Scrapes today's retail price (min/max/avg) from vegetablemarketprice.com
#   Step 2 → Fetches last 10 days of mandi (wholesale) prices from data.gov.in API
#   Step 3 → Compares mandi price vs retail range to decide what to show:
#              • If mandi price is INSIDE retail range  → show retail range (₹43–₹65)
#              • If mandi price is ABOVE retail max     → show avg(mandi, retail_max)
#              • If mandi price is BELOW retail min     → show avg(mandi, retail_min)
#   Step 4 → Predicts tomorrow's price using Linear Regression + Weighted Moving Average
#   Step 5 → Compares predicted price vs today's price → gives sell/wait advice
#
# RUN (in Google Colab):
#   !pip install requests pandas beautifulsoup4 numpy lxml -q
#   Then run: main()

# ── Imports ───────────────────────────────────────────────────────────────────
import requests                          # for making HTTP requests to websites and APIs
import pandas as pd                      # for handling tabular data (DataFrames)
from bs4 import BeautifulSoup            # for parsing HTML pages (web scraping)
from datetime import datetime, timedelta # for date calculations
import numpy as np                       # for numerical operations (arrays, math)
import os, re, time, warnings            # os=file paths, re=regex, time=delays, warnings=suppress alerts
warnings.filterwarnings("ignore")        # hide pandas/numpy deprecation warnings


# ── Config ────────────────────────────────────────────────────────────────────

# API key for data.gov.in (mandi wholesale price database)
API_KEY = "579b464db66ec23bdd0000017a052f2fb00d426858a04c9fc0f0ec86"

# The specific dataset endpoint for horticultural prices on data.gov.in
API_URL = "https://api.data.gov.in/resource/35985678-0d79-46b4-9ed6-6f13308a1d24"

# Browser-like headers so websites don't block our requests
HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"),
    "Accept-Language": "en-IN,en;q=0.9",
}

HISTORY_DAYS     = 10   # how many past days of mandi prices to use for prediction
MANDI_STALE_DAYS = 180  # if mandi data is older than this many days, ignore it


# ── Commodity Aliases ─────────────────────────────────────────────────────────
# The data.gov.in API uses specific commodity names (e.g. "Ladies finger" not "bhindi")
# This dictionary maps common user inputs → list of API-recognized names to try
COMMODITY_ALIASES = {
    "apple":        ["Apple Washington", "Apple Shimla", "Apple Green", "Apple (Red)", "Apple"],
    "tomato":       ["Tomato", "Tomato (Local)", "Tomato (Hybrid)"],
    "onion":        ["Onion", "Onion (Big)", "Onion (Small)", "Kanda"],
    "potato":       ["Potato", "Potato (Local)"],
    "banana":       ["Banana", "Banana (Robusta)", "Banana (Poovan)", "Banana (Nendran)"],
    "orange":       ["Orange", "Orange (Nagpur)", "Mosambi", "Sweet Lime"],
    "grapes":       ["Grapes", "Grapes (Green)", "Grapes Black"],
    "mango":        ["Mango", "Mango (Totapuri)", "Mango Alphonso"],
    "papaya":       ["Papaya", "Papaya (Raw)", "Papaya (Ripe)"],
    "pomegranate":  ["Pomegranate", "Pomegranate Kabul"],
    "guava":        ["Guava"],
    "pineapple":    ["Pineapple"],
    "watermelon":   ["Water Melon", "Watermelon"],
    "beans":        ["Beans", "Cluster Beans", "French Beans", "Broad Beans"],
    "carrot":       ["Carrot"],
    "cabbage":      ["Cabbage"],
    "brinjal":      ["Brinjal", "Brinjal (Round)", "Brinjal (Long)", "Baingan"],
    "ladiesfinger": ["Ladies finger", "Bhindi", "Okra"],
    "ladyfinger":   ["Ladies finger", "Bhindi", "Okra"],
    "bhindi":       ["Bhindi", "Ladies finger", "Okra"],
    "cauliflower":  ["Cauliflower"],
    "bittergourd":  ["Bitter Gourd", "Karela"],
    "drumstick":    ["Drumstick"],
    "coconut":      ["Coconut", "Coconut (Big)"],
    "ginger":       ["Ginger", "Ginger (Green)", "Ginger (Dry)"],
    "garlic":       ["Garlic", "Garlic (Dry)"],
    "lemon":        ["Lemon", "Lemon (Large)"],
    "capsicum":     ["Capsicum", "Shimla Mirch"],
    "cucumber":     ["Cucumber"],
    "pumpkin":      ["Pumpkin"],
    "ashgourd":     ["Ash Gourd", "White Pumpkin"],
    "snakegourd":   ["Snake Gourd"],
    "ridgegourd":   ["Ridge Gourd", "Turai"],
    "yam":          ["Yam", "Yam (White)"],
    "tapioca":      ["Tapioca"],
    "chilly":       ["Chilly (Dry)", "Green Chilly", "Chilli"],
    "chilli":       ["Green Chilly", "Chilly (Dry)", "Chilli"],
}

# Set of crops that are fruits — used to pick the correct URL path on VMP site
# vegetablemarketprice.com has separate URLs: /market/ for vegetables, /fruits/ for fruits
FRUIT_COMMODITIES = {
    "apple", "orange", "mosambi", "mango", "banana", "grapes", "papaya",
    "guava", "pineapple", "watermelon", "pomegranate", "lemon", "sapota",
    "jackfruit", "coconut", "fig", "avocado", "kiwi", "strawberry",
    "plum", "peach", "pear", "apricot", "cherry", "dates", "litchi",
    "custard apple", "sitaphal", "chikoo", "amla", "tamarind",
}

# District lists per state — used as fallback if the user's exact district
# is not found on vegetablemarketprice.com (try nearby districts in same state)
STATE_DISTRICTS = {
    "kerala":         ["thiruvananthapuram","kollam","pathanamthitta","alappuzha","kottayam",
                       "idukki","ernakulam","thrissur","palakkad","malappuram","kozhikode",
                       "wayanad","kannur","kasaragod"],
    "tamil nadu":     ["chennai","coimbatore","madurai","trichy","salem","tirunelveli",
                       "vellore","erode","tiruppur","dindigul","thanjavur","kancheepuram",
                       "namakkal","dharmapuri"],
    "karnataka":      ["bengaluru","mysuru","hubli","mangaluru","belgaum","tumkur",
                       "shimoga","davanagere","bellary","gulbarga"],
    "maharashtra":    ["mumbai","pune","nagpur","nashik","thane","aurangabad",
                       "solapur","kolhapur","akola","latur"],
    "andhra pradesh": ["vijayawada","visakhapatnam","guntur","nellore","kurnool",
                       "kadapa","anantapur","tirupati","rajahmundry"],
    "telangana":      ["hyderabad","warangal","nizamabad","khammam","karimnagar",
                       "medchal","nalgonda","mahbubnagar"],
    "gujarat":        ["ahmedabad","surat","vadodara","rajkot","bhavnagar","jamnagar",
                       "junagadh","anand","mehsana"],
    "west bengal":    ["kolkata","howrah","hooghly","burdwan","nadia","murshidabad",
                       "malda","jalpaiguri"],
    "uttar pradesh":  ["lucknow","agra","kanpur","allahabad","varanasi","meerut",
                       "ghaziabad","mathura","bareilly"],
    "delhi":          ["delhi","new delhi","south delhi","north delhi"],
    "punjab":         ["amritsar","ludhiana","jalandhar","patiala","bathinda"],
    "rajasthan":      ["jaipur","jodhpur","udaipur","kota","ajmer","bikaner"],
    "madhya pradesh": ["bhopal","indore","gwalior","jabalpur","ujjain"],
    "haryana":        ["gurugram","faridabad","ambala","hisar","rohtak","panipat"],
    "odisha":         ["bhubaneswar","cuttack","rourkela","puri","sambalpur"],
    "bihar":          ["patna","gaya","muzaffarpur","bhagalpur","darbhanga"],
}


# ── Utility / Helper Functions ────────────────────────────────────────────────

def get_commodity_variants(commodity):
    """
    Given a user-typed crop name (e.g. 'bhindi'), return the list of
    official API names to try (e.g. ['Bhindi', 'Ladies finger', 'Okra']).
    If no alias found, return the crop name as-is.
    """
    c = commodity.lower().strip()                   # normalise input to lowercase
    for key, variants in COMMODITY_ALIASES.items(): # loop through alias dictionary
        if c == key or c in key or key in c:        # flexible match (handles partial names)
            return variants                         # return the official name list
    return [commodity.title(), commodity.strip()]   # fallback: use user's input as-is


def extract_price_clean(text):
    """
    Extract the FIRST valid price number from a text cell.
    Used for the minimum/base price column on vegetablemarketprice.com.
    e.g. '₹38 - 65' → 38.0
    """
    text = text.replace("₹", "")                           # remove rupee symbol
    nums = re.findall(r"\d+\.?\d*", text)                  # find all numbers in string
    nums = [float(n) for n in nums if float(n) > 5]        # filter out tiny noise values
    return nums[0] if nums else None                        # return first valid number


def extract_max_price(text):
    """
    Extract the LAST (highest) price number from a text cell.
    Used for the maximum price column on vegetablemarketprice.com.
    e.g. '₹38 - 65' → 65.0
    """
    text = text.replace("₹", "")                           # remove rupee symbol
    nums = re.findall(r"\d+\.?\d*", text)                  # find all numbers in string
    nums = [float(n) for n in nums if float(n) > 5]        # filter out noise
    return nums[-1] if nums else None                       # return LAST number (the max)


def get_state_slug(s):
    """Convert state/district name to URL-friendly slug. e.g. 'Tamil Nadu' → 'tamilnadu'"""
    return s.lower().replace(" ", "")


def is_fruit(c):
    """Return True if the commodity is a fruit (affects which URL we scrape)."""
    return c.lower().strip() in FRUIT_COMMODITIES


def fuzzy_in(a, b):
    """Return True if string a is found inside string b (case-insensitive)."""
    return a.lower().strip() in b.lower().strip()


def name_matches_commodity(name_cell, commodity, variants):
    """
    Check if a table row's crop name matches what the user asked for.
    Uses strict matching to avoid wrong matches like 'Sweet Lime' matching 'Sweet Potato'.
    Returns True if the row belongs to our target commodity.
    """
    n = name_cell.lower().strip()   # row name from website, lowercased
    c = commodity.lower().strip()   # user's input, lowercased
    if c in n:                      # direct match: 'tomato' in 'Tomato (Local)'
        return True
    for v in variants:              # try each alias name
        if v.lower() in n:          # full alias match
            return True
        fw = v.split()[0].lower()   # first word of alias (e.g. 'Ladies' from 'Ladies finger')
        if fw == c and fw in n:     # first-word match only when it equals user's input
            return True
    return False                    # no match found


# ── Step 1: Retail Price Scraping — vegetablemarketprice.com ─────────────────

def scrape_today_page(url, commodity, variants):
    """
    Fetch and parse one URL from vegetablemarketprice.com.
    Looks for the row matching our commodity in the price table.
    Returns dict with min, max, avg price or None if not found.
    """
    try:
        r = requests.get(url, headers=HEADERS, timeout=12)  # fetch the webpage
        if r.status_code != 200:                             # if page didn't load OK
            return None
        soup = BeautifulSoup(r.text, "lxml")                 # parse HTML into searchable tree
        for row in soup.select("table tbody tr"):            # loop through every table row
            cols = row.find_all("td")                        # get all columns in this row
            if len(cols) < 3:                                # skip rows with too few columns
                continue
            # Column layout on VMP site: [index, name, min_price, max_price, ...]
            name_cell = cols[1].text.strip() if len(cols) > 1 else cols[0].text.strip()
            if not name_matches_commodity(name_cell, commodity, variants):
                continue                                     # skip rows for other crops
            min_p = extract_price_clean(cols[2].text) if len(cols) > 2 else None  # min price
            max_p = extract_max_price(cols[3].text)   if len(cols) > 3 else None  # max price
            if not max_p:
                max_p = min_p                                # if no max, use min as max
            avg_p = round((min_p + max_p) / 2, 2) if (min_p and max_p) else min_p  # average
            if not avg_p:
                continue                                     # skip if still no price found
            return {
                "name": name_cell,   # exact name as shown on website
                "min":  min_p,       # minimum market price (₹/kg)
                "max":  max_p,       # maximum market price (₹/kg)
                "avg":  avg_p,       # average of min and max
                "date": datetime.now()  # today's date (website shows today's prices)
            }
    except Exception:
        pass    # silently ignore network errors, timeouts, parse errors
    return None # return None if nothing found


def get_retail_price(state, commodity, district=None):
    """
    Try multiple URLs on vegetablemarketprice.com to find today's retail price.
    Priority order:
      1. District-level page (most specific)
      2. State-level page
      3. Fallback: other districts in same state
    Returns price dict or None if not found anywhere.
    """
    state_slug    = get_state_slug(state)              # e.g. 'kerala'
    district_slug = get_state_slug(district) if district else None  # e.g. 'ernakulam'
    variants      = get_commodity_variants(commodity)  # API name list for this crop
    fruit         = is_fruit(commodity)                # True if it's a fruit

    urls = []  # list of URLs to try, in priority order

    if fruit:
        # Fruits use /fruits/ path instead of /market/
        urls += [f"https://vegetablemarketprice.com/fruits/{state_slug}/today"]
        if district_slug:
            urls += [f"https://vegetablemarketprice.com/fruits/{district_slug}/today"]
    else:
        # Vegetables: try district first, then state
        if district_slug:
            urls += [f"https://vegetablemarketprice.com/market/{district_slug}/today"]
        urls += [f"https://vegetablemarketprice.com/market/{state_slug}/today",
                 f"https://vegetablemarketprice.com/fruits/{state_slug}/today"]  # some veg appear in fruits section

    # Try each URL in order
    for url in urls:
        r = scrape_today_page(url, commodity, variants)
        if r:                    # found price data
            return r
        time.sleep(0.2)         # small delay to be polite to the server

    # If still not found, try other districts in the same state as fallback
    if not fruit and district:
        for fb in STATE_DISTRICTS.get(state.lower().strip(), []):  # loop state's districts
            fb_slug = fb.replace(" ", "")
            if fb_slug == district_slug:
                continue                         # skip the district we already tried
            for u in [f"https://vegetablemarketprice.com/market/{fb_slug}/today",
                      f"https://vegetablemarketprice.com/fruits/{fb_slug}/today"]:
                r = scrape_today_page(u, commodity, variants)
                if r:
                    r["fallback_district"] = fb.title()  # note which district we fell back to
                    return r
            time.sleep(0.2)

    return None  # couldn't find price anywhere


# ── Step 2: Mandi API — data.gov.in ──────────────────────────────────────────

def fetch_mandi(state, district, commodity):
    """
    Fetch last 10 days of mandi (wholesale market) prices from data.gov.in API.
    The API stores prices in ₹/quintal (1 quintal = 100 kg).
    We keep the raw quintal values in the DataFrame; conversion to kg happens later.

    Returns DataFrame with columns: Arrival_Date, Modal_Price, Min_Price, Max_Price
    or None if no data found or all data is too old.
    """
    variants    = get_commodity_variants(commodity)                      # names to search for
    cutoff      = datetime.now() - timedelta(days=MANDI_STALE_DAYS)     # reject data older than 180 days
    filter_sets = []  # list of API filter combinations to try

    # First priority: district + state + each commodity variant name
    for v in variants:
        filter_sets.append({
            "filters[State]":     state.title(),
            "filters[District]":  district.title(),
            "filters[Commodity]": v
        })
    # Second priority: state only (no district filter) — broader search
    for v in variants:
        filter_sets.append({
            "filters[State]":     state.title(),
            "filters[Commodity]": v
        })

    for filters in filter_sets:  # try each filter combination
        params = {
            "api-key":            API_KEY,     # authentication
            "format":             "json",       # response format
            "limit":              5000,          # max records to fetch
            "sort[Arrival_Date]": "desc"         # most recent first
        }
        params.update(filters)  # add the commodity/state/district filters

        try:
            r = requests.get(API_URL, params=params, timeout=15, headers=HEADERS)
            if r.status_code != 200:
                continue                         # skip if API call failed
            records = r.json().get("records", [])
            if not records:
                continue                         # skip if no data returned

            df = pd.DataFrame(records)           # convert list of dicts → DataFrame

            # Normalise column names (API sometimes returns lowercase, sometimes mixed case)
            col_map = {}
            for c in df.columns:
                cl = c.lower()
                if cl == "arrival_date":   col_map[c] = "Arrival_Date"
                elif cl == "modal_price":  col_map[c] = "Modal_Price"   # most common/average price
                elif cl == "min_price":    col_map[c] = "Min_Price"
                elif cl == "max_price":    col_map[c] = "Max_Price"
            df = df.rename(columns=col_map)

            # Validate required columns exist
            if "Arrival_Date" not in df.columns or "Modal_Price" not in df.columns:
                continue

            # Convert columns to correct data types
            df["Arrival_Date"] = pd.to_datetime(df["Arrival_Date"], errors="coerce", dayfirst=True)
            df["Modal_Price"]  = pd.to_numeric(df["Modal_Price"],  errors="coerce")
            if "Min_Price" in df.columns:
                df["Min_Price"] = pd.to_numeric(df["Min_Price"], errors="coerce")
            if "Max_Price" in df.columns:
                df["Max_Price"] = pd.to_numeric(df["Max_Price"], errors="coerce")

            df = df.dropna(subset=["Arrival_Date", "Modal_Price"])  # remove rows with missing key data
            if df.empty:
                continue

            latest_date = df["Arrival_Date"].max()          # most recent date in data
            if latest_date < cutoff:
                continue                                     # data is too old, skip silently

            df = df[df["Arrival_Date"] >= cutoff]           # keep only recent data

            # Group by date (multiple markets may report same date) → average the prices
            grouped = (df.groupby("Arrival_Date")
                         .agg(
                             Modal_Price=("Modal_Price", "mean"),  # avg modal price across markets
                             Min_Price  =("Min_Price",   "mean") if "Min_Price" in df.columns else ("Modal_Price","mean"),
                             Max_Price  =("Max_Price",   "mean") if "Max_Price" in df.columns else ("Modal_Price","mean")
                         )
                         .reset_index()
                         .sort_values("Arrival_Date", ascending=False))  # most recent first

            return grouped.head(HISTORY_DAYS).reset_index(drop=True)  # return last 10 days

        except Exception:
            continue  # silently skip any error (network, JSON parse, etc.)

    return None  # nothing found after trying all filter combinations


# ── Step 3: Compute What Price to Show the Farmer ────────────────────────────

def compute_final_price(retail, mandi_df):
    """
    Decide what price (or range) to display to the farmer today.

    LOGIC:
    ──────
    Case A — Both retail (scraped) AND mandi (API) prices available:

      The mandi API price is in ₹/quintal. We convert to ₹/kg (divide by 100).
      Then we compare mandi price vs the retail range [min, max]:

      A1: mandi price is INSIDE retail range (min ≤ mandi ≤ max)
          → The two sources AGREE. Show the full retail range (₹min – ₹max).
            This is the most trustworthy situation.

      A2: mandi price is ABOVE retail max
          → Mandi is reporting a higher price than the retail ceiling.
            Blended price = avg(mandi, retail_max).
            Show as a single blended value.

      A3: mandi price is BELOW retail min
          → Mandi is cheaper than retail floor.
            Blended price = avg(mandi, retail_min).
            Show as a single blended value.

      Special: if mandi data is more than 7 days older than retail → ignore mandi,
               just show retail range.

    Case B — Only retail available (mandi returned nothing):
      → Show retail range as-is: ₹min – ₹max.

    Case C — Only mandi available (scraping failed):
      → Convert mandi modal price to kg, show as single value.

    Returns:
      final_display dict:
        {"type": "range", "low": float, "high": float, "avg": float}
        OR
        {"type": "exact", "value": float}
      mandi_latest_kg   — mandi modal price in ₹/kg (or None)
      mandi_latest_date — date of latest mandi record (or None)
    """
    mandi_latest_kg   = None  # will hold mandi price in ₹/kg
    mandi_latest_date = None  # will hold the date of latest mandi record

    # Extract latest mandi price if we have mandi data
    if mandi_df is not None and not mandi_df.empty:
        row               = mandi_df.iloc[0]                                             # most recent row (sorted desc)
        mandi_latest_date = row["Arrival_Date"]                                           # date of this mandi record
        mandi_modal_kg    = round(float(row["Modal_Price"]) / 100, 2)                    # ₹/quintal → ₹/kg
        mandi_latest_kg   = mandi_modal_kg                                                # store for later use

    # ── Case A: Both sources available ────────────────────────────────────────
    if retail and mandi_latest_kg:
        r_min     = retail["min"]                                                         # retail minimum price
        r_max     = retail["max"]                                                         # retail maximum price
        days_diff = abs((retail["date"] - mandi_latest_date).days)                       # age gap between the two sources

        if days_diff > 7:
            # Mandi data is stale compared to retail — don't mix them, use retail only
            return (
                {"type": "range", "low": r_min, "high": r_max,
                 "avg": round((r_min + r_max) / 2, 2)},
                mandi_latest_kg, mandi_latest_date
            )

        if r_min <= mandi_latest_kg <= r_max:
            # ── Case A1: mandi INSIDE retail range → show full retail range ──
            return (
                {"type": "range", "low": r_min, "high": r_max,
                 "avg": round((r_min + r_max) / 2, 2)},
                mandi_latest_kg, mandi_latest_date
            )

        elif mandi_latest_kg > r_max:
            # ── Case A2: mandi ABOVE retail max → blend with retail max ──────
            blended = round((mandi_latest_kg + r_max) / 2, 2)                            # midpoint of mandi and retail ceiling
            return (
                {"type": "exact", "value": blended},
                mandi_latest_kg, mandi_latest_date
            )

        else:
            # ── Case A3: mandi BELOW retail min → blend with retail min ──────
            blended = round((mandi_latest_kg + r_min) / 2, 2)                            # midpoint of mandi and retail floor
            return (
                {"type": "exact", "value": blended},
                mandi_latest_kg, mandi_latest_date
            )

    # ── Case B: Only retail available ─────────────────────────────────────────
    elif retail:
        r_min = retail["min"]
        r_max = retail["max"]
        return (
            {"type": "range", "low": r_min, "high": r_max,
             "avg": round((r_min + r_max) / 2, 2)},
            None, None
        )

    # ── Case C: Only mandi available ──────────────────────────────────────────
    elif mandi_latest_kg:
        return (
            {"type": "exact", "value": mandi_latest_kg},
            mandi_latest_kg, mandi_latest_date
        )

    # ── No data at all ────────────────────────────────────────────────────────
    return None, None, None


# ── Step 4: Predict Tomorrow's Price ─────────────────────────────────────────

def predict_next_day(prices):
    """
    Predict tomorrow's price using an ensemble of two methods:

    Method 1 — Linear Regression (60% weight):
      Fits a straight trend line through the last N price points.
      Projects that line one step forward to get tomorrow's estimate.
      Good at capturing long-term direction.

    Method 2 — Weighted Moving Average (40% weight):
      Takes a weighted average where recent prices count more.
      Weights are exponential: latest day gets 2^(N-1), oldest gets 2^0.
      Adds a simple momentum adjustment (last - first) / N.
      Good at capturing recent momentum.

    Final prediction = 60% LR + 40% WMA

    Returns dict with prediction, valid (number of data points used),
    slope (price change per day), price_min, price_max.
    """
    # Remove any None or NaN values from the price list
    clean = [p for p in prices if p is not None and not np.isnan(p)]

    # Need at least 2 data points to fit a line
    if len(clean) < 2:
        return {
            "prediction": None,   # can't predict
            "valid":      len(clean),
            "trend":      None,
            "slope":      0,
            "price_min":  None,
            "price_max":  None
        }

    y = np.array(clean, dtype=float)            # price values as numpy array
    x = np.arange(len(y), dtype=float)          # day indices: 0, 1, 2, ..., N-1
    n = len(y)

    # ── Linear Regression: compute slope and intercept analytically ──────────
    # Formula: slope = (N·Σxy - Σx·Σy) / (N·Σx² - (Σx)²)
    slope     = (n * np.dot(x, y) - x.sum() * y.sum()) / (n * np.dot(x, x) - x.sum() ** 2)
    intercept = (y.sum() - slope * x.sum()) / n     # intercept = (Σy - slope·Σx) / N
    lr_pred   = slope * n + intercept               # predict at day N (the next day)

    # ── Weighted Moving Average ───────────────────────────────────────────────
    w        = np.array([2 ** i for i in range(n)])             # weights: 1, 2, 4, 8, ... 2^(N-1)
    wma_pred = np.dot(w, y) / w.sum()                           # weighted average of past prices
    wma_pred += (y[-1] - y[0]) / n                              # add momentum: avg daily change

    # ── Ensemble: combine both predictions ────────────────────────────────────
    final = max(0.0, round(0.6 * lr_pred + 0.4 * wma_pred, 2)) # can't be negative

    # Note: we still compute slope-based trend here for storage, but the
    # DISPLAY trend (used for advice) is computed separately in show_price_and_forecast
    # by comparing predicted price vs today's actual price.
    trend = "rising" if slope > 0.3 else ("falling" if slope < -0.3 else "stable")

    return {
        "prediction": final,               # tomorrow's predicted price (₹/kg)
        "trend":      trend,               # slope-based direction (not used for advice)
        "slope":      round(slope, 4),     # price change per day (₹/day)
        "valid":      n,                   # number of data points used
        "price_min":  round(float(np.min(y)), 2),   # lowest price in history window
        "price_max":  round(float(np.max(y)), 2),   # highest price in history window
    }


# ── Step 5: Display Output ────────────────────────────────────────────────────

def show_price_and_forecast(commodity, final_display, pred, today_avg):
    """
    Print the clean, farmer-friendly price report.

    Shows:
      - Commodity name and today's date
      - Today's price (as range or single value)
      - Tomorrow's predicted price
      - Simple advice: sell today or wait

    The trend for advice is determined by comparing the PREDICTED PRICE
    to TODAY'S REFERENCE PRICE — not by the historical slope.

    Why? Because slope tells you how prices moved in the past 10 days,
    but what matters to the farmer is: will tomorrow's price be higher
    or lower than what I can sell for TODAY?

    Example of why slope alone is wrong:
      Prices were ₹80→₹61 (falling slope) then spiked to ₹69.
      Slope says "falling", but prediction ₹69 > today ₹54 → farmer should WAIT.
    """
    today_str = datetime.now().strftime("%d %b %Y (%A)")        # e.g. "26 Feb 2026 (Thursday)"
    next_date = datetime.now().date() + timedelta(days=1)       # tomorrow's date

    # ── Print header ──────────────────────────────────────────────────────────
    print()
    print("─" * 52)
    print(f"  {commodity.title()}")    # crop name, title-cased
    print(f"  {today_str}")            # today's date
    print("─" * 52)

    # ── Handle case where no price data is available at all ───────────────────
    if final_display is None:
        print("  Price data not available.")
        print("─" * 52)
        return

    # ── Print today's price ───────────────────────────────────────────────────
    if final_display["type"] == "range":
        # Show min–max range with average (Case A1 or B)
        lo  = final_display["low"]
        hi  = final_display["high"]
        avg = final_display["avg"]
        print(f"  Today's Price  :  ₹{lo:.0f} – ₹{hi:.0f} / kg")  # e.g. ₹43 – ₹65 / kg
        print(f"  Average        :  ₹{avg:.1f} / kg")               # e.g. ₹54.0 / kg
    else:
        # Show single blended price (Case A2, A3, or C)
        val = final_display["value"]
        print(f"  Today's Price  :  ₹{val:.2f} / kg")               # e.g. ₹45.00 / kg

    # ── Print tomorrow's forecast ─────────────────────────────────────────────
    print("─" * 52)

    if pred["prediction"] is None or pred["valid"] < 2:
        # Not enough price history to predict — give a rough ±8% estimate instead
        base = today_avg or (final_display.get("avg") or final_display.get("value") or 0)
        if base:
            lo8 = round(base * 0.92, 1)   # 8% below today
            hi8 = round(base * 1.08, 1)   # 8% above today
            print(f"  Tomorrow ({next_date.strftime('%d %b')})  :  ₹{lo8} – ₹{hi8} / kg  (estimated ±8%)")
        print()
        print("  📢  No clear price trend yet.")
        print("       Monitor for a few more days before selling.")

    else:
        pred_p = pred["prediction"]   # predicted price for tomorrow (₹/kg)

        # ── KEY FIX: derive trend from predicted vs today, not historical slope ──
        # ref_today = the price the farmer can sell at TODAY
        ref_today  = today_avg or (final_display.get("avg") or final_display.get("value") or pred_p)
        pct_change = ((pred_p - ref_today) / ref_today * 100) if ref_today else 0
        #   pct_change > +2%  → price going UP   → farmer should wait
        #   pct_change < -2%  → price going DOWN  → farmer should sell today
        #   within ±2%        → price stable      → either is fine

        if pct_change > 2:
            trend = "rising"
        elif pct_change < -2:
            trend = "falling"
        else:
            trend = "stable"

        # Emoji icons for each trend
        icons = {"rising": "📈", "falling": "📉", "stable": "➡ "}

        # Print tomorrow's predicted price with trend icon
        print(f"  Tomorrow ({next_date.strftime('%d %b')})  :  ₹{pred_p:.2f} / kg  {icons.get(trend,'')} {trend.title()}")
        print()

        # ── Print advice based on the CORRECT trend ───────────────────────────
        if trend == "rising":
            # Predicted price > today → farmer benefits from waiting
            print("  📢  Prices expected to RISE tomorrow.")
            print(f"       Consider waiting to sell — you may get a better")
            print(f"       price than today's ₹{ref_today:.1f}/kg.")

        elif trend == "falling":
            # Predicted price < today → farmer should sell now before price drops
            print("  📢  Prices expected to FALL tomorrow.")
            print(f"       Better to sell TODAY at ₹{ref_today:.1f}/kg")
            print(f"       rather than waiting.")

        else:
            # Predicted price ≈ today → no urgency either way
            print("  📢  Price is STABLE.")
            print("       Sell today or wait — little change expected.")

    print("─" * 52)  # closing separator


# ── Main Function ─────────────────────────────────────────────────────────────

def main():
    """
    Entry point. Asks the farmer for state, district, and crop name,
    then runs all steps (fetch → compute → predict → display).
    """
    print("\n🌾  Crop Price Advisor")
    print("─" * 40)

    # Get inputs from the user
    state     = input("  State    (e.g. Kerala)     : ").strip()
    district  = input("  District (e.g. Ernakulam)  : ").strip()
    commodity = input("  Crop     (e.g. Tomato)      : ").strip()
    print()

    # Validate that all three fields were filled in
    if not all([state, district, commodity]):
        print("  All fields are required.")
        return

    # ── Step 1: Fetch today's retail price (silent — no status prints) ────────
    retail   = get_retail_price(state, commodity, district)

    # ── Step 2: Fetch mandi price history from API (silent) ───────────────────
    mandi_df = fetch_mandi(state, district, commodity)

    # ── Step 3: Decide what price range/value to show ─────────────────────────
    final_display, mandi_latest_kg, mandi_latest_date = compute_final_price(retail, mandi_df)

    # ── Step 4: Build price history list for prediction ───────────────────────
    history_prices = []   # will hold last 10 days of mandi prices in ₹/kg
    if mandi_df is not None and not mandi_df.empty:
        df_asc         = mandi_df.sort_values("Arrival_Date")              # oldest first for regression
        history_prices = [round(p / 100, 2)                                # convert quintal → kg
                          for p in df_asc["Modal_Price"].tolist()]

    # Run the prediction model on the price history
    pred = predict_next_day(history_prices)

    # Extract today's reference price (used for comparison with tomorrow's prediction)
    today_avg = None
    if final_display:
        today_avg = (final_display.get("avg")       # use avg if showing a range
                     if final_display["type"] == "range"
                     else final_display.get("value"))  # or the single value

    # ── Step 5: Show the output to the farmer ─────────────────────────────────
    show_price_and_forecast(commodity, final_display, pred, today_avg)

    # Handle case where no data was found at all
    if final_display is None:
        print("  No price data found for this crop/location.")


# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()   # only runs when this file is executed directly (not when imported)
