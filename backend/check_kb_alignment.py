import json
from pathlib import Path

# Load diseases.json
kb_path = Path("../ml/knowledge_base/diseases.json")

with open(kb_path, 'r', encoding='utf-8') as f:
    kb = json.load(f)

print("=" * 80)
print("KNOWLEDGE BASE STRUCTURE ANALYSIS")
print("=" * 80)

print(f"\n✅ Total Diseases in KB: {len(kb)}")
print("\n📋 First 10 Disease Keys (Normalized Format):")
for i, key in enumerate(list(kb.keys())[:10], 1):
    raw_labels = kb[key].get("raw_labels", [])
    print(f"{i}. {key:50s} → Raw: {raw_labels}")

print("\n" + "=" * 80)
print("CHECKING raw_labels FIELD")
print("=" * 80)

# Count how many have raw_labels
has_raw_labels = sum(1 for v in kb.values() if "raw_labels" in v)
print(f"✅ Diseases with 'raw_labels' field: {has_raw_labels}/{len(kb)}")

# Check for common patterns
print("\n📊 Raw Label Patterns:")
patterns = {}
for key, value in kb.items():
    if "raw_labels" in value:
        for raw_label in value["raw_labels"]:
            if "___" in raw_label:
                patterns.setdefault("___", []).append(raw_label)
            elif "_" in raw_label:
                patterns.setdefault("_", []).append(raw_label)

for pattern, examples in patterns.items():
    print(f"  - Pattern '{pattern}': {len(examples)} occurrences")
    print(f"    Examples: {examples[:3]}")

print("\n" + "=" * 80)
print("NORMALIZATION TEST")
print("=" * 80)

# Test normalization logic from dual_classifier.py
def normalize_disease_name(raw_name):
    """Normalization used in dual_classifier.py"""
    return raw_name.replace("___", "_").replace(" ", "_").replace("(", "").replace(")", "").replace(",", "").lower()

print("Testing if raw_labels normalize to their KB keys:")
mismatches = []
for kb_key, value in list(kb.items())[:20]:  # Test first 20
    if "raw_labels" in value:
        for raw_label in value["raw_labels"]:
            normalized = normalize_disease_name(raw_label)
            if normalized != kb_key:
                mismatches.append((raw_label, normalized, kb_key))

if mismatches:
    print(f"⚠️ Found {len(mismatches)} MISMATCHES:")
    for raw, norm, expected in mismatches[:5]:
        print(f"  Raw: '{raw}' → Normalized: '{norm}' != KB Key: '{expected}'")
else:
    print("✅ All tested raw_labels normalize correctly to their KB keys!")

print("\n" + "=" * 80)
print("SEARCHING FOR POSSIBLE MODEL OUTPUTS")
print("=" * 80)

# Common disease names that might come from model
test_model_outputs = [
    "Apple___Apple_scab",
    "Apple_Apple_scab", 
    "apple_black_rot",
    "Tomato___Early_blight",
    "tomato_early_blight",
    "Corn_healthy"
]

print("Testing if these model outputs would be found:")
for model_output in test_model_outputs:
    normalized = normalize_disease_name(model_output)
    found = normalized in kb
    status = "✅ FOUND" if found else "❌ NOT FOUND"
    print(f"  {model_output:40s} → {normalized:40s} {status}")

