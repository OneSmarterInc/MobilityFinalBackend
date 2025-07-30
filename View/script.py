from difflib import SequenceMatcher
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

# Example
s1 = "MOB SELECT POOLED 5GB W/VVM FOR 5G+/5G IPHONE"
lst = ["MOB SELECT POOLED 10000GB W/VVM FOR 5G+/5G IPHONE","MOB SELECT POOLED 1000GB W/VVM FOR 5G+/5G IPHONE","MOB SELECT POOLED 100GB W/VVM FOR 5G+/5G IPHONE","MOB SELECT POOLED 10GB W/VVM FOR 5G+/5G IPHONE","MOB SELECT POOLED 5GB W/VVM FOR 5G+/5G IPHONE"]
x = get_close_match_key(s1, lst)
print(f"Similarity: {x}")
