import json
import difflib

def parse_until_dict(data):
    """Parse stringified JSON until dict."""
    while isinstance(data, str):
        try:
            data = json.loads(data.replace("'", "\""))
        except Exception:
            break
    return data

def get_close_match_key(key, candidates, cutoff=0.8):
    """Return the closest matching key from candidates."""
    matches = difflib.get_close_matches(key, candidates, n=1, cutoff=cutoff)
    return matches[0] if matches else None

def compare_values(base_val, bill_val, variance_percent):
    """
    Compare numeric values with percentage variance tolerance.
    Ensures negative numbers have exactly one minus sign.
    """
    bill_val_init = str(bill_val).strip()

    try:
        # Clean out symbols, detect sign
        is_negative = "-" in bill_val_init
        base_float = float(str(base_val).replace("$", "").replace("-", "").strip())
        bill_float = float(bill_val_init.replace("$", "").replace("-", "").strip())

        # Case 1: both zero → approve
        if base_float == 0 and bill_float == 0:
            return "0.0", True

        # Case 2: base != 0 → check % range
        if base_float != 0:
            low_range = bill_float - (variance_percent / 100 * bill_float)
            high_range = bill_float + (variance_percent / 100 * bill_float)
            tag = low_range <= base_float <= high_range
        else:
            tag = False

        # Normalize sign
        normalized_val = f"-{bill_float}" if is_negative and bill_float != 0 else str(bill_float)

        return normalized_val, tag

    except ValueError:
        # If non-numeric, fallback to string equality
        return bill_val_init, (str(base_val).strip() == bill_val_init.strip())


def compare_and_tag(base, bill, variance_percent):
    """Recursively compare and tag bill against baseline."""
    result = {}
    for key, bill_val in bill.items():
        # Match key with baseline
        closely_matched = key if key in base else get_close_match_key(key, list(base.keys()))

        # Key not found → accept with approved=True
        if not closely_matched:
            if isinstance(bill_val, dict):
                nested = compare_and_tag({}, bill_val, variance_percent)
                result[key] = nested
            else:
                
                result[key] = {"amount": str(bill_val), "approved": True if float(bill_val) == 0 else False}
            continue

        base_val = base[closely_matched]

        # Both dicts → recurse
        if isinstance(bill_val, dict) and isinstance(base_val, dict):
            result[key] = compare_and_tag(base_val, bill_val, variance_percent)
        else:
            amount, approved = compare_values(base_val, bill_val, variance_percent)
            result[key] = {"amount": amount, "approved": approved}

    return result


def object_tagging(baseline_data, bill_data, variance):
    baseline_data = parse_until_dict(baseline_data)
    bill_data = parse_until_dict(bill_data)

    tagged = compare_and_tag(baseline_data, bill_data, variance)
    return json.dumps(tagged)


# baseline = "{\"MONTHLY CHARGES\": {\"ADDL SMARTPHN DATA ACCESS\": 25.0, \"BUSINESS UNLIMITED SMARTPHONE\": 45.0}, \"OTHER CHARGES AND CREDITS\": {\"ECONOMIC ADJUSTMENT CHARGE\": 3.97}, \"SURCHARGES\": {\"ADMINISTRATIVE CHARGE\": 1.95, \"FED UNIVERSAL SERVICE CHARGE\": 0.48, \"REGULATORY CHARGE\": 0.16}, \"TAXES GOVERNMENTAL SURCHARGES AND FEES\": {\"KITSAP CNTY 911 SURCHG\": 0.7, \"KITSAP CNTY SALES TAX-TELECOM\": 0.16, \"WA STATE 911 FEE\": 0.25, \"WA STATE 988 TAX\": 0.4, \"WA STATE SALES TAX-TELECOM\": 0.37}}"
# bill = "{\"MONTHLY CHARGES\": {\"ADDL SMARTPHN DATA ACCESS\": 25.0, \"BUSINESS UNLIMITED SMARTPHONE\": 45.0}, \"OTHER CHARGES AND CREDITS\": {\"ECONOMIC ADJUSTMENT CHARGE\": 3.97}, \"SURCHARGES\": {\"ADMINISTRATIVE CHARGE\": 1.95, \"FED UNIVERSAL SERVICE CHARGE\": 0.48, \"REGULATORY CHARGE\": 0.16}, \"TAXES GOVERNMENTAL SURCHARGES AND FEES\": {\"KITSAP CNTY 911 SURCHG\": 0.7, \"KITSAP CNTY SALES TAX-TELECOM\": 0.16, \"WA STATE 911 FEE\": 0.25, \"WA STATE 988 TAX\": 0.4, \"WA STATE SALES TAX-TELECOM\": 0.37}}"

# print(tagging(baseline, bill, 5))
import re
def create_category_object(self, plan, monthly_charges):
    res = {}
    matches = list(re.finditer(r'\$(\d*\.?\d+)', plan))

    if matches:
        for i, match in enumerate(matches):
            amount = float(match.group(1))

            # Determine description boundaries
            start = matches[i-1].end() if i > 0 else 0
            end = match.start()

            desc = plan[start:end].strip().upper()

            # Remove leading/trailing garbage words
            desc = re.sub(r'^\d[\d\.]*\s*', '', desc).strip()

            res[desc] = amount
    else:
        res[plan] = monthly_charges

    # Wrap inside Monthly Charges
    return json.dumps({"Monthly Charges": res})



