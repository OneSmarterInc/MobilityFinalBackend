import json

def parse_until_dict(data):
    while isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            break
    return data
def tagging(baseline_data, bill_data):

    baseline_data = parse_until_dict(baseline_data) if isinstance(baseline_data, str) else baseline_data
    bill_data = parse_until_dict(bill_data) if isinstance(bill_data,str) else bill_data
    def compare_and_tag(base, bill):
        def normalize(key):
            return key.strip().lower()
        
        base_keys_normalized = {normalize(k): k for k in base.keys()}

        for bill_key in list(bill.keys()):
            norm_key = normalize(bill_key)
            if norm_key not in base_keys_normalized:
                continue

            base_key = base_keys_normalized[norm_key]
            base_val = base[base_key]
            bill_val = bill[bill_key]

            if isinstance(bill_val, dict) and isinstance(base_val, dict):
                compare_and_tag(base_val, bill_val)
            else:
                try:
                    base_val = str(base_val).replace('$', '').replace('-', '')
                    bill_val_init = str(bill_val).replace('$', '')
                    bill_val = bill_val_init.replace('-', '')
                    base_float = float(base_val)
                    bill_float = float(bill_val)
                    if base_float != 0:
                        low_range = bill_float - (5 / 100 * bill_float)
                        high_range = bill_float + (5 / 100 * bill_float)
                        tag = low_range < base_float < high_range
                        if '-' in bill_val_init:
                            bill[bill_key] = {"amount": f'-{bill_val}', "approved": tag}
                        else:
                            bill[bill_key] = {"amount": bill_val, "approved": tag}
                except (ValueError, TypeError):
                    print("error")
                    bill[bill_key] = {"amount": bill_val, "approved": False}


    compare_and_tag(baseline_data, bill_data)
    
    json_string = json.dumps(bill_data)
    return json_string

form1 = "{\"Monthly Charges\": {\"Flex Business Data Device 2GB\": 35.0, \"10% Access Discount\": -3.5}, \"Surcharges\": {\"Regulatory Charge\": 0.02, \"Administrative Charge\": 0.06, \"OH Tax Recovery Surcharge\": 0.08}, \"Other Charges and Credits\": {\"Economic Adjustment Charge\": 0.98}}"
form2 = "{\"Monthly Charges\": {\"Flex Business Data Device 2GB\": 35.0, \"10% Access Discount\": -3.5}, \"Surcharges\": {\"Regulatory Charge\": 0.02, \"Administrative Charge\": 0.06, \"OH Tax Recovery Surcharge\": 0.08}, \"Other Charges and Credits\": {\"Economic Adjustment Charge\": 0.98}}"
tag =  tagging(form1, form2)
print(tag)