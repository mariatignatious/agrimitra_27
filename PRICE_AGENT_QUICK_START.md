# Quick Start: Price Agent Integration

## TL;DR - How to Use

### 1. **Direct Usage in Python**

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
print(result["selling_advice"])     # Buy/Sell recommendation
print(result["confidence"])         # "high", "medium", "low", "very_low"
```

### 2. **Via Agent System (Automatic)**

```python
from agent_system.reasoner_coordinator import ReasonerNode

reasoner = ReasonerNode()
response = reasoner.process("What's tomato price in Kerala?")

# Reasoner automatically:
# - Detects "price" intent
# - Extracts crop = "tomato", state = "Kerala"
# - Routes to price_agent
# - Returns complete response
```

### 3. **Using the Tool**

```python
from agent_system.tools import price_tool
import json

result_json = price_tool(
    crop_name="apple",
    state="Maharashtra",
    district="Pune"
)

result = json.loads(result_json)
print(result["selling_advice"])
```

---

## What You Get

```
Current Price  → ₹43 – ₹65/kg (or single value)
Tomorrow Price → ₹52.50/kg (predicted using ML)
Advice         → "RISE" / "FALL" / "STABLE"
Confidence     → "high" / "medium" / "low" / "very_low"
Reason         → Why you should sell today or wait
```

---

## Key Features

| Feature | Details |
|---------|---------|
| 📍 **Data Sources** | Retail (vegetablemarketprice.com) + Wholesale API (data.gov.in) |
| 🤖 **Prediction** | Ensemble model (60% Linear Regression + 40% Weighted Moving Average) |
| 📊 **History** | Uses last 10 days of prices |
| ⚡ **Speed** | ~2-4 seconds per request |
| ✅ **Accuracy** | High confidence when >7 days of data available |
| 🔄 **Fallback** | If one source fails, uses the other automatically |

---

## Supported Crops

**Vegetables:** tomato, onion, potato, cabbage, carrot, brinjal, bhindi, cauliflower, capsicum, cucumber, ginger, garlic, and more...

**Fruits:** apple, orange, mango, banana, grapes, papaya, guava, pineapple, watermelon, lemon, coconut, and more...

---

## Sample Response

```json
{
  "crop": "tomato",
  "current_price": "₹43 – ₹65/kg",
  "predicted_price": "₹52.50/kg",
  "price_trend": "rising",
  "selling_advice": "Prices expected to RISE by ~5.2%. Consider waiting to sell for a better price.",
  "confidence": "high",
  "historical_data_points": 8
}
```

---

## What Changed From Original

| Aspect | Before | After |
|--------|--------|-------|
| **Location** | `crop_price_advisor.py` (standalone) | `agent_system/price_agent.py` (integrated) |
| **Input** | Interactive CLI prompts | Programmatic function call |
| **Output** | Printed console text | Structured JSON dict |
| **Integration** | Standalone script | Part of multi-agent system |
| **Data Flow** | Manual user input | Reasoner extracts from user query |

---

## Configuration

Need to adjust behavior? Edit `agent_system/price_agent.py`:

```python
HISTORY_DAYS = 10          # Change how many days of history to use
MANDI_STALE_DAYS = 180     # Change how old data can be before ignoring
```

---

## Testing

Run this to verify integration works:

```python
from agent_system.price_agent import PriceAgentNode

agent = PriceAgentNode()

# Test 1: Basic query
result = agent.process("tomato", "Kerala", "Ernakulam")
assert result["agent"] == "price_agent"
assert "selling_advice" in result
print("✅ Test passed")

# Test 2: Different crop
result = agent.process("apple", "Karnataka", "Bengaluru")
assert "predicted_price" in result
print("✅ Test passed")

# Test 3: Error handling
result = agent.process("xyz_crop", "Kerala", "Ernakulam")
assert "error" in result
print("✅ Test passed")
```

---

## Common Issues & Solutions

**Q: Getting "timeout" errors**  
A: Network might be slow. Internet connection required for web scraping.

**Q: Price is 0 or missing**  
A: Crop might not exist in API. Check spelling (e.g., "bhindi" vs "okra").

**Q: Confidence is "very_low"**  
A: Not enough historical data yet. System needs 2+ days of prices.

**Q: State/District not recognized**  
A: Check `STATE_DISTRICTS` dict in `price_agent.py` for valid names.

---

## Next Steps

1. ✅ Integration complete - code is ready to use
2. 📊 **Optional:** Add Redis caching for faster repeated queries
3. 🌐 **Optional:** Integrate with frontend (web/mobile)
4. 📈 **Optional:** Add historical trending features
5. 🧪 **Optional:** Test with real farmer feedback

---

## Full Documentation

See **PRICE_AGENT_INTEGRATION.md** for:
- Complete architecture details
- All parameters explained
- Error handling guide
- Performance tips
- Advanced customization

---

## Files Changed

✅ `agent_system/price_agent.py` - Complete rewrite with full integration  
✅ `agent_system/tools.py` - Updated price_tool to call new agent  
✅ `PRICE_AGENT_INTEGRATION.md` - Full technical documentation  
✅ `PRICE_AGENT_QUICK_START.md` - This file
