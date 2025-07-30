
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

import re

def remove_digits_and_symbols(text):
    
    return re.sub(r'[^a-zA-Z\s]', '', text)
def string_similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    min_len = min(len(a), len(b))
    matches = sum(1 for i in range(min_len) if a[i] == b[i])
    return matches / max(len(a), len(b))


def get_close_match_key(target_key: str, key_list: list[str]) -> str | None:
    closest = ""
    max_similarity = 0.0

    for candidate in key_list:
        target_key_enhanced = remove_digits_and_symbols(target_key)
        candidate_enhanced = remove_digits_and_symbols(candidate)
        sim = string_similarity(target_key_enhanced, candidate_enhanced)
        if sim > 0.8 and sim > max_similarity:
            max_similarity = sim
            closest = candidate

    return closest if closest else None

def compare(str1, str2):
    str1lst = str1.split()
    str2lst = str2.split()
    points = 0
    for i in str2lst:
       if i in str1lst: points+=1 
    percent = (points/len(str2lst)) * 100
    return int(percent) > 80
    

