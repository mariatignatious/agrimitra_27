# Price Agent Integration Guide

## Overview

Your complete price prediction code from `crop_price_advisor.py` has been fully integrated into the agent system. The system now:

1. **Fetches live retail prices** from `vegetablemarketprice.com` via web scraping
2. **Fetches wholesale (mandi) prices** from `data.gov.in` API (last 10 days)
3. **Predicts tomorrow's price** using an ensemble ML model:
   - 60% weight: Linear Regression (captures long-term trend)
   - 40% weight: Weighted Moving Average (captures recent momentum)
4. **Provides selling advice** (Sell Today vs Wait) based on predicted price
5. **Returns structured JSON** for seamless integration with the agent coordinator

---

## Architecture

### File Structure

```
agent_system/
├── price_agent.py          ← MAIN FILE (now contains full price logic)
├── tools.py                ← Updated with new price_tool
└── reasoner_coordinator.py ← Routes requests to price_agent
```

### Integration Points

#### 1. **PriceAgentNode Class** (price_agent.py)
```python
class PriceAgentNode:
    def process(self, crop: str, state: str, district: str) -> Dict[str, Any]:
        # Returns comprehensive price + advice response
```

**Parameters:**
- `crop` (str): Crop name (e.g., 'tomato', 'apple', 'bhindi')
- `state` (str): State name (e.g., 'Kerala', 'Maharashtra')
- `district` (str): District name (e.g., 'Ernakulam', 'Pune')

**Returns:** Dict with:
```json
{
  "crop": "tomato",
  "state": "Kerala",
  "district": "Ernakulam",
  "timestamp": "2026-02-26T14:30:00",
  "current_price": "₹43 – ₹65/kg",
  "predicted_price": "₹52.50/kg",
  "price_trend": "rising",
  "selling_advice": "Prices expected to RISE by ~5.2%. Consider waiting to sell for a better price.",
  "confidence": "high",
  "historical_data_points": 8,
  "price_range": {
    "min": 40.5,
    "max": 68.2
  },
  "sources": {
    "retail_price": "vegetablemarketprice.com",
    "mandi_price": "data.gov.in",
    "prediction_method": "Ensemble (60% Linear Regression + 40% Weighted Moving Average)"
  },
  "agent": "price_agent"
}
```

#### 2. **price_tool** (tools.py)
```python
@tool
def price_tool(crop_name: str, state: str = "Kerala", district: str = "Ernakulam") -> str:
    """Get current market price + prediction + selling advice"""
```

This tool is called by the agent system and returns a JSON string.

---

## How It Works

### Step-by-Step Flow

```
User Query (e.g., "What's the price of tomato in Kerala?")
         ↓
  Reasoner (routes to price_agent)
         ↓
  PriceAgent.process() {
    1. Scrape vegetablemarketprice.com for TODAY'S RETAIL PRICE
    2. Fetch data.gov.in API for LAST 10 DAYS OF MANDI PRICES
    3. Blend both sources → compute final display price
    4. Build price history list from mandi data
    5. Predict TOMORROW'S PRICE using ensemble model
    6. Compare predicted vs today → generate advice
    7. Return structured JSON response
  }
         ↓
  Coordinator → Format & display to user
```

### Data Sources

| Source | Data | Format | Frequency |
|--------|------|--------|-----------|
| **vegetablemarketprice.com** | Today's retail min/max/avg | Web scraping | Daily |
| **data.gov.in API** | Last 10 days wholesale (mandi) | JSON API | Daily |

### Price Computation Logic

When both retail and mandi data are available:

| Scenario | Action | Example |
|----------|--------|---------|
| Mandi price INSIDE retail range | Show full retail range | Mandi ₹50, Retail ₹43–₹65 → Show ₹43–₹65 |
| Mandi price ABOVE retail max | Blend average | Mandi ₹70, Retail max ₹65 → Show ₹67.50 |
| Mandi price BELOW retail min | Blend average | Mandi ₹40, Retail min ₹43 → Show ₹41.50 |
| Mandi data >7 days old | Use retail only | Old mandi ₹50, New retail ₹43–₹65 → Show ₹43–₹65 |

### Prediction Model

**Ensemble approach:**
```
Predicted_Price = 0.60 × LinearRegression_Prediction + 0.40 × WMA_Prediction

LinearRegression:
  - Fits a trend line through last 10 days
  - Projects one step forward for tomorrow
  - Good at capturing long-term direction

WeightedMovingAverage:
  - Weights: [1, 2, 4, 8, ..., 2^(N-1)] (exponential)
  - Adds momentum adjustment: (last - first) / N
  - Good at capturing recent price movement
```

### Selling Advice Logic

```
Price_Change_Percent = ((Tomorrow - Today) / Today) × 100

If change > +2%  → "RISE" → Advice: "Wait to sell for better price"
If change < -2%  → "FALL" → Advice: "Sell TODAY before price drops"
If change ±2%    → "STABLE" → Advice: "Either is fine"
```

---

## Usage Examples

### Example 1: Query via Agent System

```python
from agent_system.price_agent import PriceAgentNode

agent = PriceAgentNode()
result = agent.process(
    crop="tomato",
    state="Kerala",
    district="Ernakulam"
)

print(result["current_price"])      # ₹43 – ₹65/kg
print(result["predicted_price"])    # ₹52.50/kg
print(result["selling_advice"])     # "Prices expected to RISE by ~5.2%..."
```

### Example 2: Via Reasoner Coordinator

```python
from agent_system.reasoner_coordinator import ReasonerNode

reasoner = ReasonerNode()
reasoner_output = reasoner.process("What's the price of tomato in Kerala, Ernakulam?")

# This will automatically route to price_agent and get the full response
```

### Example 3: Using the price_tool Directly

```python
from agent_system.tools import price_tool

result_json = price_tool(
    crop_name="apple",
    state="Karnataka",
    district="Bengaluru"
)

# result_json is a JSON string, parse it:
import json
result = json.loads(result_json)
print(result["selling_advice"])
```

---

## Supported Crops

The system recognizes these commodities (with automatic aliases):

**Fruits:** apple, orange, mosambi, mango, banana, grapes, papaya, guava, pineapple, watermelon, pomegranate, lemon, coconut, chikoo, litchi, custard apple, amla, tamarind

**Vegetables:** tomato, onion, potato, beans, carrot, cabbage, brinjal, bhindi/ladiesfinger, cauliflower, bitter gourd, drumstick, ginger, garlic, capsicum, cucumber, pumpkin, yam

**Aliases:** The system automatically handles variant names (e.g., "bhindi" → "Ladies finger" → "Okra")

---

## Supported States & Districts

### Included States
Kerala, Tamil Nadu, Karnataka, Maharashtra, Andhra Pradesh, Telangana, Gujarat, West Bengal, Uttar Pradesh, Delhi, Punjab, Rajasthan, Madhya Pradesh, Haryana, Odisha, Bihar

Each state has 10-15 districts. If a specific district isn't found on the website, the system falls back to nearby districts in the same state.

---

## API Configuration

### data.gov.in API

- **Endpoint:** `https://api.data.gov.in/resource/35985678-0d79-46b4-9ed6-6f13308a1d24`
- **API Key:** `579b464db66ec23bdd0000017a052f2fb00d426858a04c9fc0f0ec86` (included)
- **Rate Limits:** Usually 100 requests/hour (free tier)
- **Fields:** Arrival_Date, Modal_Price (₹/quintal), Min_Price, Max_Price

### Website Scraping

- **vegetablemarketprice.com** - Uses BeautifulSoup + requests
- **Headers:** User-Agent spoofing to avoid blocking
- **Delay:** 0.2 seconds between requests (polite scraping)

---

## Error Handling

The system handles various failure scenarios gracefully:

| Scenario | Behavior |
|----------|----------|
| Website down | Falls back to mandi API data only |
| API quota exceeded | Uses cached data or falls back to mock |
| No price found for crop | Returns error with helpful message |
| Insufficient history (<2 days) | Returns ±8% estimate + "monitor" advice |
| Invalid state/district | Tries fallback districts automatically |

---

## Configuration Options

To customize behavior, modify these constants in `agent_system/price_agent.py`:

```python
HISTORY_DAYS = 10              # Days of mandi price history to use for prediction
MANDI_STALE_DAYS = 180         # Max age of mandi data before ignoring it
```

---

## Response Format

### Success Response

```json
{
  "crop": "tomato",
  "state": "Kerala",
  "district": "Ernakulam",
  "timestamp": "2026-02-26T14:30:00.123456",
  "current_price": "₹43 – ₹65/kg",
  "predicted_price": "₹52.50/kg",
  "price_trend": "rising",
  "selling_advice": "Prices expected to RISE by ~5.2%. Consider waiting to sell for a better price.",
  "confidence": "high",
  "historical_data_points": 8,
  "price_range": {
    "min": 40.5,
    "max": 68.2
  },
  "sources": {
    "retail_price": "vegetablemarketprice.com",
    "mandi_price": "data.gov.in",
    "prediction_method": "Ensemble (60% Linear Regression + 40% Weighted Moving Average)"
  },
  "agent": "price_agent"
}
```

### Error Response

```json
{
  "crop": "unknown_crop",
  "error": "Commodity 'unknown_crop' not found in API",
  "selling_advice": "Unable to fetch price data: Commodity 'unknown_crop' not found in API",
  "agent": "price_agent"
}
```

---

## Performance & Caching

**Current Implementation (Direct Calls):**
- Web scraping: 1-2 seconds
- API call: 1-2 seconds
- Prediction: <100ms
- **Total:** ~2-4 seconds per request

**For Production:**
Consider adding:
1. **Redis caching** - Cache prices for 1 hour
2. **Background updates** - Refresh prices every hour
3. **Async calls** - Fetch retail + API in parallel
4. **Rate limiting** - Queue requests if API quota hit

---

## Testing the Integration

### Test 1: Direct Agent Usage

```python
from agent_system.price_agent import PriceAgentNode

agent = PriceAgentNode()
result = agent.process("tomato", "Kerala", "Ernakulam")
assert result["agent"] == "price_agent"
assert "selling_advice" in result
assert result["confidence"] in ["low", "medium", "high", "very_low"]
print("✅ Test 1 passed")
```

### Test 2: Via Tool

```python
from agent_system.tools import price_tool
import json

result_json = price_tool("apple", "Karnataka", "Bengaluru")
result = json.loads(result_json)
assert "current_price" in result
assert "predicted_price" in result
print("✅ Test 2 passed")
```

### Test 3: Error Handling

```python
from agent_system.price_agent import PriceAgentNode

agent = PriceAgentNode()
result = agent.process("xyz_unknown_crop", "Kerala", "Ernakulam")
assert "error" in result
print("✅ Test 3 passed")
```

---

## Advantages of This Integration

✅ **Real-time data** - Fetches live prices from two authoritative sources  
✅ **Smart prediction** - ML ensemble for accurate next-day forecasting  
✅ **Actionable advice** - Clear "sell today" vs "wait" recommendations  
✅ **Fallback logic** - Gracefully handles missing data from either source  
✅ **Farmer-friendly** - Simple language, percentage-based confidence  
✅ **Scalable** - Easy to add caching, async calls, or additional data sources  
✅ **Well-structured** - Follows agent system architecture  

---

## Next Steps

1. **Test with real farmers** - Get feedback on advice accuracy
2. **Add caching layer** - Speed up repeated queries
3. **Integrate with frontend** - Show prices on web/mobile UI
4. **Monitor API usage** - Track quotas and costs
5. **A/B test prediction model** - Compare with alternative ML models
6. **Add historical trending** - Show weekly/monthly price patterns

---

## Troubleshooting

### Q: Getting "timeout" errors
**A:** Website might be slow. Check internet connection, or add delays in `scrape_today_page()`.

### Q: API returning "no records"
**A:** Commodity name might not be in API. Check `COMMODITY_ALIASES` dict and add variant if needed.

### Q: Prediction marked as "very_low" confidence
**A:** Less than 2 days of price history. System will accumulate more data over time.

### Q: Price seems wrong
**A:** Check if you're comparing ₹/kg (retail) vs ₹/quintal (mandi). System automatically converts.

---

## Questions?

Refer to `crop_price_advisor.py` for original implementation details, or check the inline comments in `agent_system/price_agent.py` for the integration logic.
