# ✅ Testing Guide - Verify Integration is Working

## Quick Test (30 seconds)

Run this in Python to verify basic functionality:

```python
from agent_system.price_agent import PriceAgentNode

# Test 1: Can we import?
print("✅ Import successful")

# Test 2: Can we create the agent?
agent = PriceAgentNode()
print("✅ Agent created")

# Test 3: Can we call process()?
result = agent.process("tomato", "Kerala", "Ernakulam")
print("✅ Process called successfully")

# Test 4: Do we get the expected response?
assert "crop" in result, "Missing 'crop' field"
assert "current_price" in result, "Missing 'current_price' field"
assert "predicted_price" in result, "Missing 'predicted_price' field"
assert "selling_advice" in result, "Missing 'selling_advice' field"
print("✅ All expected fields present")

print("\n🎉 BASIC TEST PASSED!\n")
print(f"Crop: {result['crop']}")
print(f"Current Price: {result['current_price']}")
print(f"Tomorrow's Price: {result['predicted_price']}")
print(f"Advice: {result['selling_advice']}")
print(f"Confidence: {result['confidence']}")
```

---

## Test Suite 1: Syntax & Import Checks

```python
# Test: Can Python parse the file?
import py_compile
try:
    py_compile.compile('agent_system/price_agent.py', doraise=True)
    print("✅ price_agent.py: Syntax OK")
except py_compile.PyCompileError as e:
    print(f"❌ Syntax Error: {e}")

# Test: Can we import the module?
try:
    from agent_system.price_agent import PriceAgentNode
    print("✅ Import successful")
except ImportError as e:
    print(f"❌ Import failed: {e}")

# Test: Can we import tools?
try:
    from agent_system.tools import price_tool
    print("✅ price_tool imported")
except ImportError as e:
    print(f"❌ price_tool import failed: {e}")
```

---

## Test Suite 2: Basic Functionality

```python
from agent_system.price_agent import PriceAgentNode
import json

agent = PriceAgentNode()

# Test 1: Single crop query
print("\n--- Test 1: Single Crop Query ---")
result = agent.process("tomato", "Kerala", "Ernakulam")
print(f"Result type: {type(result)}")
print(f"Is dict: {isinstance(result, dict)}")
print(f"Has 'crop': {'crop' in result}")
print(f"Crop value: {result.get('crop')}")

# Test 2: Response structure
print("\n--- Test 2: Response Structure ---")
required_fields = [
    "crop", "current_price", "predicted_price", 
    "selling_advice", "confidence", "agent"
]
for field in required_fields:
    if field in result:
        print(f"✅ {field}: {result[field]}")
    else:
        print(f"❌ Missing: {field}")

# Test 3: Confidence levels
print("\n--- Test 3: Confidence Levels ---")
valid_confidence = ["high", "medium", "low", "very_low"]
conf = result.get("confidence")
if conf in valid_confidence:
    print(f"✅ Confidence valid: {conf}")
else:
    print(f"❌ Invalid confidence: {conf}")

# Test 4: Response is JSON-serializable
print("\n--- Test 4: JSON Serialization ---")
try:
    json_str = json.dumps(result)
    print(f"✅ JSON serializable: {len(json_str)} characters")
except Exception as e:
    print(f"❌ JSON serialization failed: {e}")
```

---

## Test Suite 3: Different Crops & Locations

```python
from agent_system.price_agent import PriceAgentNode

agent = PriceAgentNode()

test_cases = [
    ("tomato", "Kerala", "Ernakulam"),
    ("apple", "Karnataka", "Bengaluru"),
    ("onion", "Maharashtra", "Pune"),
    ("banana", "Tamil Nadu", "Chennai"),
    ("potato", "Uttar Pradesh", "Lucknow"),
]

print("\n--- Testing Multiple Crops ---\n")

passed = 0
failed = 0

for crop, state, district in test_cases:
    try:
        result = agent.process(crop, state, district)
        
        if "error" not in result and "crop" in result:
            print(f"✅ {crop.upper():10} ({state}, {district})")
            print(f"   Price: {result.get('current_price')}")
            print(f"   Advice: {result.get('selling_advice', 'N/A')[:50]}...")
            passed += 1
        else:
            print(f"❌ {crop.upper():10} - Got error: {result.get('error')}")
            failed += 1
    except Exception as e:
        print(f"❌ {crop.upper():10} - Exception: {e}")
        failed += 1

print(f"\n✅ Passed: {passed}/{len(test_cases)}")
print(f"❌ Failed: {failed}/{len(test_cases)}")
```

---

## Test Suite 4: Error Handling

```python
from agent_system.price_agent import PriceAgentNode

agent = PriceAgentNode()

print("\n--- Testing Error Handling ---\n")

# Test 1: Invalid crop
print("Test 1: Invalid crop")
result = agent.process("xyz_unknown_crop_123", "Kerala", "Ernakulam")
if "error" in result or result.get("crop") == "xyz_unknown_crop_123":
    print("✅ Handles invalid crop gracefully")
else:
    print("⚠️  Might have issue with invalid crop")

# Test 2: Missing state
print("\nTest 2: Empty state")
result = agent.process("tomato", "", "Ernakulam")
if "error" in result:
    print("✅ Handles missing state")
else:
    print("⚠️  Should handle empty state")

# Test 3: Missing district
print("\nTest 3: Empty district")
result = agent.process("tomato", "Kerala", "")
if "error" in result:
    print("✅ Handles missing district")
else:
    print("⚠️  Should handle empty district")

# Test 4: Response on error
print("\nTest 4: Error response format")
result = agent.process("invalid", "invalid", "invalid")
if isinstance(result, dict):
    print("✅ Returns dict even on error")
else:
    print("❌ Should return dict")
```

---

## Test Suite 5: Tool Integration

```python
from agent_system.tools import price_tool
import json

print("\n--- Testing price_tool Integration ---\n")

# Test 1: Can we call the tool?
print("Test 1: Calling price_tool")
try:
    result_json = price_tool("tomato", "Kerala", "Ernakulam")
    print("✅ Tool callable")
except Exception as e:
    print(f"❌ Tool error: {e}")
    exit(1)

# Test 2: Does it return JSON string?
print("\nTest 2: Returns JSON string")
if isinstance(result_json, str):
    print("✅ Returns string")
else:
    print(f"❌ Returns {type(result_json)}")

# Test 3: Can we parse the JSON?
print("\nTest 3: JSON parsing")
try:
    result = json.loads(result_json)
    print("✅ Valid JSON")
except Exception as e:
    print(f"❌ JSON parse error: {e}")

# Test 4: Does parsed result have expected fields?
print("\nTest 4: Response fields")
required = ["crop", "current_price", "predicted_price", "selling_advice"]
for field in required:
    if field in result:
        print(f"✅ {field}: {result[field]}")
    else:
        print(f"❌ Missing: {field}")
```

---

## Test Suite 6: Complete End-to-End

```python
from agent_system.price_agent import PriceAgentNode
import json
from datetime import datetime

agent = PriceAgentNode()

print("\n" + "="*60)
print("🧪 COMPLETE END-TO-END TEST")
print("="*60 + "\n")

# Step 1: Query a crop
print("Step 1: Querying tomato price...")
result = agent.process("tomato", "Kerala", "Ernakulam")

# Step 2: Verify response
print("Step 2: Verifying response structure...")
checks = [
    ("Is dict", isinstance(result, dict)),
    ("Has crop", "crop" in result),
    ("Has current_price", "current_price" in result),
    ("Has predicted_price", "predicted_price" in result),
    ("Has selling_advice", "selling_advice" in result),
    ("Has confidence", "confidence" in result),
    ("Has timestamp", "timestamp" in result),
    ("Has agent field", result.get("agent") == "price_agent"),
]

passed = 0
for name, check in checks:
    status = "✅" if check else "❌"
    print(f"  {status} {name}")
    if check:
        passed += 1

# Step 3: Display data
print(f"\nStep 3: Displaying results...")
print(f"  Crop: {result.get('crop')}")
print(f"  State: {result.get('state')}")
print(f"  District: {result.get('district')}")
print(f"  Current Price: {result.get('current_price')}")
print(f"  Tomorrow Price: {result.get('predicted_price')}")
print(f"  Trend: {result.get('price_trend')}")
print(f"  Advice: {result.get('selling_advice')[:100]}...")
print(f"  Confidence: {result.get('confidence')}")
print(f"  Data Points: {result.get('historical_data_points')}")

# Step 4: Verify JSON serialization
print(f"\nStep 4: Testing JSON serialization...")
try:
    json_str = json.dumps(result)
    print(f"  ✅ Can convert to JSON ({len(json_str)} chars)")
except Exception as e:
    print(f"  ❌ JSON error: {e}")

# Summary
print(f"\n" + "="*60)
print(f"✅ PASSED: {passed}/{len(checks)} checks")
print("="*60 + "\n")

if passed == len(checks):
    print("🎉 ALL TESTS PASSED! Integration is working!\n")
else:
    print(f"⚠️  Some tests failed. Check the output above.\n")
```

---

## Test Suite 7: Reasoner Integration

```python
from agent_system.reasoner_coordinator import ReasonerNode

print("\n--- Testing Reasoner Integration ---\n")

try:
    reasoner = ReasonerNode()
    print("✅ ReasonerNode imported")
    
    # Test: Does reasoner route to price_agent?
    user_input = "What's the price of tomato in Kerala?"
    response = reasoner.process(user_input)
    
    if "price_agent" in response.get("agents_to_trigger", []):
        print("✅ Reasoner routes to price_agent for price queries")
    else:
        print("⚠️  Check reasoner routing")
        
    print(f"\nReasoner detected:")
    print(f"  Intent: {response.get('intent')}")
    print(f"  Crop: {response.get('crop')}")
    print(f"  Agents: {response.get('agents_to_trigger')}")
    
except Exception as e:
    print(f"❌ Reasoner test failed: {e}")
```

---

## Quick Verification Script (Copy & Paste)

```python
#!/usr/bin/env python3
"""
Quick verification script - Run this to check if integration is working
"""

def test_all():
    print("\n" + "🔍 INTEGRATION VERIFICATION".center(60, "="))
    
    # Test 1: Import
    print("\n[1/6] Testing imports...")
    try:
        from agent_system.price_agent import PriceAgentNode
        from agent_system.tools import price_tool
        print("    ✅ Imports successful")
    except ImportError as e:
        print(f"    ❌ Import failed: {e}")
        return False
    
    # Test 2: Agent creation
    print("\n[2/6] Creating agent...")
    try:
        agent = PriceAgentNode()
        print("    ✅ Agent created")
    except Exception as e:
        print(f"    ❌ Failed: {e}")
        return False
    
    # Test 3: Process call
    print("\n[3/6] Calling process()...")
    try:
        result = agent.process("tomato", "Kerala", "Ernakulam")
        print("    ✅ Process executed")
    except Exception as e:
        print(f"    ❌ Failed: {e}")
        return False
    
    # Test 4: Response validation
    print("\n[4/6] Validating response...")
    required = ["crop", "current_price", "predicted_price", "selling_advice", "confidence"]
    missing = [f for f in required if f not in result]
    if not missing:
        print("    ✅ All fields present")
    else:
        print(f"    ❌ Missing: {missing}")
        return False
    
    # Test 5: Tool call
    print("\n[5/6] Testing price_tool...")
    try:
        import json
        result_json = price_tool("apple", "Karnataka", "Bengaluru")
        result = json.loads(result_json)
        print("    ✅ Tool works")
    except Exception as e:
        print(f"    ❌ Failed: {e}")
        return False
    
    # Test 6: Display results
    print("\n[6/6] Displaying results...")
    print(f"    Crop: {result.get('crop')}")
    print(f"    Price: {result.get('current_price')}")
    print(f"    Tomorrow: {result.get('predicted_price')}")
    print(f"    Advice: {result.get('selling_advice')[:60]}...")
    print("    ✅ Results displayed")
    
    print("\n" + "✅ ALL TESTS PASSED!".center(60, "=") + "\n")
    return True

if __name__ == "__main__":
    import sys
    success = test_all()
    sys.exit(0 if success else 1)
```

---

## Running Tests in Terminal

### Quick Test (Fastest)
```bash
cd /home/icfoss/Desktop/Price_Predictor/Final_Year_Project
python3 << 'EOF'
from agent_system.price_agent import PriceAgentNode
agent = PriceAgentNode()
result = agent.process("tomato", "Kerala", "Ernakulam")
print("✅ SUCCESS!")
print(f"Price: {result['current_price']}")
print(f"Advice: {result['selling_advice']}")
EOF
```

### Full Test Suite
```bash
cd /home/icfoss/Desktop/Price_Predictor/Final_Year_Project
python3 << 'EOF'
# Copy Test Suite 6 code here and run
EOF
```

---

## Checklist for Verification

### ✅ Code Level
- [ ] `agent_system/price_agent.py` exists and has ~557 lines
- [ ] `agent_system/tools.py` has updated `price_tool`
- [ ] No syntax errors when importing
- [ ] `PriceAgentNode` class exists

### ✅ Functionality Level
- [ ] Can create `PriceAgentNode()` instance
- [ ] Can call `agent.process(crop, state, district)`
- [ ] Returns a dictionary
- [ ] Dict has all required fields

### ✅ Response Level
- [ ] `crop` field present
- [ ] `current_price` field present
- [ ] `predicted_price` field present
- [ ] `selling_advice` field present
- [ ] `confidence` field is one of: high/medium/low/very_low

### ✅ Integration Level
- [ ] `price_tool()` callable from `tools.py`
- [ ] Returns valid JSON string
- [ ] Reasoner routes to price_agent

### ✅ Error Handling
- [ ] Invalid crop doesn't crash
- [ ] Empty state doesn't crash
- [ ] Error responses return dict
- [ ] No unhandled exceptions

---

## What Should You See?

### Success Output
```
✅ Import successful
✅ Agent created
✅ Process called successfully
✅ All expected fields present

🎉 BASIC TEST PASSED!

Crop: tomato
Current Price: ₹43 – ₹65/kg
Tomorrow's Price: ₹52.50/kg
Advice: Prices expected to RISE by ~5.2%. Consider waiting to sell for a better price.
Confidence: high
```

### Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` | Make sure you're in the right directory |
| `No module named 'requests'` | Install: `pip install requests beautifulsoup4 pandas numpy` |
| `price_tool not found` | Check tools.py was updated correctly |
| `Empty dict response` | Network issue - check internet connection |

---

**Ready to test? Run the "Quick Test" section above!** ✅
