# Price Agent Integration Examples

This file contains practical code examples for integrating the price agent with your existing agent system.

---

## Example 1: Basic Usage - Query a Single Crop

```python
from agent_system.price_agent import PriceAgentNode

# Create the agent
agent = PriceAgentNode()

# Query for tomato price in Kerala, Ernakulam
result = agent.process(
    crop="tomato",
    state="Kerala",
    district="Ernakulam"
)

# Print the results
print(f"Crop: {result['crop']}")
print(f"Current Price: {result['current_price']}")
print(f"Tomorrow's Price: {result['predicted_price']}")
print(f"Advice: {result['selling_advice']}")
print(f"Confidence: {result['confidence']}")
```

**Output:**
```
Crop: tomato
Current Price: ₹43 – ₹65/kg
Tomorrow's Price: ₹52.50/kg
Advice: Prices expected to RISE by ~5.2%. Consider waiting to sell for a better price.
Confidence: high
```

---

## Example 2: Batch Query Multiple Crops

```python
from agent_system.price_agent import PriceAgentNode
import json

agent = PriceAgentNode()

crops_to_check = [
    ("tomato", "Kerala", "Ernakulam"),
    ("apple", "Karnataka", "Bengaluru"),
    ("onion", "Maharashtra", "Pune"),
    ("banana", "Tamil Nadu", "Chennai"),
]

results = {}
for crop, state, district in crops_to_check:
    result = agent.process(crop, state, district)
    results[crop] = {
        "current_price": result.get("current_price"),
        "predicted_price": result.get("predicted_price"),
        "selling_advice": result.get("selling_advice"),
        "confidence": result.get("confidence")
    }

# Save to file
with open("price_report.json", "w") as f:
    json.dump(results, f, indent=2)

print("✅ Price report generated!")
```

---

## Example 3: Compare Predictions for Decision Making

```python
from agent_system.price_agent import PriceAgentNode
from datetime import datetime

agent = PriceAgentNode()

# Get prices for different markets (same crop, different locations)
locations = [
    ("Kerala", "Ernakulam"),
    ("Karnataka", "Bengaluru"),
    ("Maharashtra", "Pune"),
]

print(f"\nTomato Price Comparison - {datetime.now().strftime('%Y-%m-%d')}")
print("=" * 70)
print(f"{'Location':<25} {'Current':<15} {'Tomorrow':<15} {'Recommendation':<15}")
print("=" * 70)

best_price_location = None
best_advice = None
max_potential = 0

for state, district in locations:
    result = agent.process("tomato", state, district)
    
    if "error" in result:
        print(f"{state}, {district:<10} ERROR: {result['error']}")
        continue
    
    location = f"{state}, {district}"
    current = result["current_price"]
    tomorrow = result["predicted_price"]
    advice = "WAIT" if "RISE" in result["selling_advice"] else "SELL"
    
    print(f"{location:<25} {current:<15} {tomorrow:<15} {advice:<15}")
    
    # Track best opportunity
    if "RISE" in result["selling_advice"] and result["confidence"] == "high":
        # Extract numeric value for comparison
        try:
            curr_val = float(tomorrow.replace("₹", "").split("/")[0])
            if curr_val > max_potential:
                max_potential = curr_val
                best_price_location = location
                best_advice = result["selling_advice"]
        except:
            pass

print("=" * 70)
if best_price_location:
    print(f"\n💡 Best opportunity: {best_price_location}")
    print(f"   {best_advice}")
```

---

## Example 4: Using the price_tool Directly

```python
from agent_system.tools import price_tool
import json

# Call the tool
result_json = price_tool(
    crop_name="apple",
    state="Karnataka",
    district="Bengaluru"
)

# Parse the JSON response
result = json.loads(result_json)

# Extract key information
if "error" not in result:
    print("Apple Price Analysis - Bengaluru, Karnataka")
    print("-" * 50)
    print(f"Current Price:    {result['current_price']}")
    print(f"Predicted Price:  {result['predicted_price']}")
    print(f"Price Trend:      {result['price_trend']}")
    print(f"Selling Advice:   {result['selling_advice']}")
    print(f"Data Points:      {result['historical_data_points']} days")
    print(f"Confidence:       {result['confidence']}")
else:
    print(f"Error: {result['error']}")
```

---

## Example 5: Integration with Reasoner (Automatic Routing)

```python
from agent_system.reasoner_coordinator import ReasonerNode
import json

reasoner = ReasonerNode()

# User asks about price
user_input = "What is the price of tomato in Kerala, Ernakulam?"

# Reasoner processes and routes to appropriate agent
response = reasoner.process(user_input)

print(f"Intent Detected: {response['intent']}")
print(f"Crop Extracted: {response['crop']}")
print(f"Agents Triggered: {response['agents_to_trigger']}")

# If price_agent was triggered, get its response
if "price_agent" in response.get("agents_to_trigger", []):
    print("\n✅ Price Agent Response:")
    print(json.dumps(response, indent=2))
```

---

## Example 6: Build a Price Recommendation System

```python
from agent_system.price_agent import PriceAgentNode
from datetime import datetime, timedelta

agent = PriceAgentNode()

def get_selling_recommendation(crop, state, district, quantity_kg):
    """
    Get selling recommendation considering price trends and quantity.
    """
    result = agent.process(crop, state, district)
    
    if "error" in result:
        return {"error": result["error"]}
    
    current = result["current_price"]
    predicted = result["predicted_price"]
    advice = result["selling_advice"]
    confidence = result["confidence"]
    
    # Extract numeric values
    try:
        if "–" in current:
            prices = current.replace("₹", "").replace("/kg", "").split("–")
            current_avg = sum(float(p.strip()) for p in prices) / len(prices)
        else:
            current_avg = float(current.replace("₹", "").replace("/kg", ""))
        
        predicted_val = float(predicted.replace("₹", "").replace("/kg", ""))
    except:
        return {"error": "Could not parse prices"}
    
    # Calculate potential earnings
    current_earnings = current_avg * quantity_kg
    predicted_earnings = predicted_val * quantity_kg
    potential_gain = predicted_earnings - current_earnings
    
    return {
        "crop": crop,
        "location": f"{state}, {district}",
        "current_price_per_kg": round(current_avg, 2),
        "predicted_price_per_kg": round(predicted_val, 2),
        "quantity_kg": quantity_kg,
        "current_earnings": round(current_earnings, 2),
        "predicted_earnings": round(predicted_earnings, 2),
        "potential_gain_loss": round(potential_gain, 2),
        "recommendation": "WAIT" if potential_gain > 0 else "SELL TODAY",
        "selling_advice": advice,
        "confidence": confidence,
        "timestamp": datetime.now().isoformat()
    }

# Example usage
recommendation = get_selling_recommendation(
    crop="tomato",
    state="Kerala",
    district="Ernakulam",
    quantity_kg=100
)

print(f"Selling Recommendation for {recommendation['crop']}")
print("=" * 60)
print(f"Location:              {recommendation['location']}")
print(f"Quantity:              {recommendation['quantity_kg']} kg")
print(f"Current Price:         ₹{recommendation['current_price_per_kg']}/kg")
print(f"Predicted Tomorrow:    ₹{recommendation['predicted_price_per_kg']}/kg")
print(f"Current Earnings:      ₹{recommendation['current_earnings']}")
print(f"Predicted Earnings:    ₹{recommendation['predicted_earnings']}")
print(f"Potential Gain/Loss:   ₹{recommendation['potential_gain_loss']}")
print(f"\n💡 Recommendation:     {recommendation['recommendation']}")
print(f"Reason:                {recommendation['selling_advice']}")
print(f"Confidence:            {recommendation['confidence']}")
```

---

## Example 7: Historical Trend Tracking

```python
from agent_system.price_agent import PriceAgentNode
import json
from datetime import datetime

agent = PriceAgentNode()

class PriceTracker:
    def __init__(self):
        self.history = []
    
    def track_price(self, crop, state, district):
        """Track price over multiple queries"""
        result = agent.process(crop, state, district)
        
        if "error" in result:
            return False
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "crop": crop,
            "state": state,
            "district": district,
            "current_price": result["current_price"],
            "predicted_price": result["predicted_price"],
            "trend": result["price_trend"],
            "confidence": result["confidence"]
        }
        
        self.history.append(entry)
        return True
    
    def get_trend_report(self):
        """Generate trend report from history"""
        if not self.history:
            return {"error": "No tracking history yet"}
        
        return {
            "total_queries": len(self.history),
            "crops_tracked": list(set(h["crop"] for h in self.history)),
            "first_timestamp": self.history[0]["timestamp"],
            "last_timestamp": self.history[-1]["timestamp"],
            "history": self.history
        }

# Usage
tracker = PriceTracker()

# Track same crop over time
print("Tracking tomato prices...")
for i in range(3):
    tracker.track_price("tomato", "Kerala", "Ernakulam")
    print(f"  Query {i+1} completed")
    # In real scenario, you'd wait some time between queries
    # time.sleep(3600)  # Wait 1 hour

# Get report
report = tracker.get_trend_report()
print("\nTracking Report:")
print(json.dumps(report, indent=2))
```

---

## Example 8: Error Handling & Graceful Degradation

```python
from agent_system.price_agent import PriceAgentNode
import logging

logger = logging.getLogger(__name__)
agent = PriceAgentNode()

def safe_get_price(crop, state, district, fallback_price=None):
    """
    Safely get price with fallback and logging
    """
    try:
        result = agent.process(crop, state, district)
        
        if "error" in result:
            logger.warning(f"Price query failed: {result['error']}")
            
            if fallback_price:
                logger.info(f"Using fallback price: ₹{fallback_price}/kg")
                return {
                    "current_price": f"₹{fallback_price}/kg (fallback)",
                    "confidence": "very_low",
                    "note": "Using cached fallback price"
                }
            else:
                raise Exception(result["error"])
        
        logger.info(f"Successfully fetched price: {result['current_price']}")
        return result
    
    except Exception as e:
        logger.error(f"Exception in price query: {e}")
        if fallback_price:
            return {
                "current_price": f"₹{fallback_price}/kg (fallback)",
                "confidence": "very_low",
                "error": str(e),
                "note": "Using cached fallback price due to error"
            }
        else:
            return {
                "error": str(e),
                "note": "No price data available"
            }

# Usage with fallback prices
fallback_prices = {
    "tomato": 50,
    "apple": 80,
    "onion": 45,
}

price_data = safe_get_price(
    crop="tomato",
    state="Kerala",
    district="Ernakulam",
    fallback_price=fallback_prices.get("tomato")
)

print(f"Price: {price_data['current_price']}")
if "error" in price_data:
    print(f"Warning: {price_data.get('note')}")
```

---

## Example 9: Dashboard Data Aggregation

```python
from agent_system.price_agent import PriceAgentNode
import json
from datetime import datetime

agent = PriceAgentNode()

def generate_price_dashboard(farmer_crops):
    """
    Generate a dashboard with prices for all farmer's crops
    
    farmer_crops = [
        {"crop": "tomato", "state": "Kerala", "district": "Ernakulam"},
        {"crop": "apple", "state": "Karnataka", "district": "Bengaluru"},
        {"crop": "onion", "state": "Maharashtra", "district": "Pune"},
    ]
    """
    dashboard = {
        "generated_at": datetime.now().isoformat(),
        "crops": [],
        "summary": {
            "total_crops": len(farmer_crops),
            "rising_prices": 0,
            "falling_prices": 0,
            "stable_prices": 0,
            "high_confidence_recommendations": 0
        }
    }
    
    for item in farmer_crops:
        result = agent.process(item["crop"], item["state"], item["district"])
        
        crop_data = {
            "crop": item["crop"],
            "location": f"{item['state']}, {item['district']}",
            "current_price": result.get("current_price", "N/A"),
            "predicted_price": result.get("predicted_price", "N/A"),
            "selling_advice": result.get("selling_advice", "No data"),
            "confidence": result.get("confidence", "unknown"),
            "trend": result.get("price_trend", "unknown")
        }
        
        dashboard["crops"].append(crop_data)
        
        # Update summary
        trend = result.get("price_trend", "").lower()
        if trend == "rising":
            dashboard["summary"]["rising_prices"] += 1
        elif trend == "falling":
            dashboard["summary"]["falling_prices"] += 1
        elif trend == "stable":
            dashboard["summary"]["stable_prices"] += 1
        
        if result.get("confidence") == "high":
            dashboard["summary"]["high_confidence_recommendations"] += 1
    
    return dashboard

# Example usage
farmer_crops = [
    {"crop": "tomato", "state": "Kerala", "district": "Ernakulam"},
    {"crop": "apple", "state": "Karnataka", "district": "Bengaluru"},
]

dashboard = generate_price_dashboard(farmer_crops)

# Print dashboard
print("📊 PRICE DASHBOARD")
print("=" * 70)
print(f"Generated: {dashboard['generated_at']}")
print(f"Total Crops: {dashboard['summary']['total_crops']}")
print(f"Rising: {dashboard['summary']['rising_prices']} | Falling: {dashboard['summary']['falling_prices']} | Stable: {dashboard['summary']['stable_prices']}")
print("=" * 70)

for crop in dashboard['crops']:
    print(f"\n{crop['crop'].upper()} - {crop['location']}")
    print(f"  Current: {crop['current_price']}")
    print(f"  Tomorrow: {crop['predicted_price']}")
    print(f"  Trend: {crop['trend']} ({crop['confidence']})")
    print(f"  → {crop['selling_advice']}")
```

---

## Example 10: REST API Wrapper

```python
from agent_system.price_agent import PriceAgentNode
from flask import Flask, request, jsonify
import logging

app = Flask(__name__)
agent = PriceAgentNode()
logger = logging.getLogger(__name__)

@app.route('/api/price', methods=['GET'])
def get_price():
    """
    REST API endpoint for price queries
    
    Query params:
    - crop (required): Crop name
    - state (optional): State name (default: Kerala)
    - district (optional): District name (default: Ernakulam)
    
    Example: /api/price?crop=tomato&state=Kerala&district=Ernakulam
    """
    try:
        crop = request.args.get('crop')
        state = request.args.get('state', 'Kerala')
        district = request.args.get('district', 'Ernakulam')
        
        if not crop:
            return jsonify({"error": "crop parameter is required"}), 400
        
        result = agent.process(crop, state, district)
        
        return jsonify(result), 200
    
    except Exception as e:
        logger.error(f"API Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/batch-price', methods=['POST'])
def batch_price():
    """
    Batch API endpoint for multiple crops
    
    POST body:
    {
      "crops": [
        {"crop": "tomato", "state": "Kerala", "district": "Ernakulam"},
        {"crop": "apple", "state": "Karnataka", "district": "Bengaluru"}
      ]
    }
    """
    try:
        data = request.get_json()
        crops = data.get('crops', [])
        
        results = []
        for item in crops:
            result = agent.process(
                item.get('crop'),
                item.get('state', 'Kerala'),
                item.get('district', 'Ernakulam')
            )
            results.append(result)
        
        return jsonify({"results": results, "count": len(results)}), 200
    
    except Exception as e:
        logger.error(f"Batch API Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)

# Usage:
# curl "http://localhost:5000/api/price?crop=tomato&state=Kerala&district=Ernakulam"
# curl -X POST -H "Content-Type: application/json" -d '{"crops":[{"crop":"tomato","state":"Kerala","district":"Ernakulam"}]}' http://localhost:5000/api/batch-price
```

---

All these examples can be run and customized for your specific use case!
