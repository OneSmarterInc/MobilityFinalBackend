
import json
def parse_until_dict(data):
    while isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            break
    return data

def str_to_bool(value):
    print(value)
    return str(value).strip().lower() in ['true','yes']