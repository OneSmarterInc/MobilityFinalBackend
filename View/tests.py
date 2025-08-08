from django.test import TestCase
import re
# Create your tests here.
def separate_words(text):
    words = re.findall(r'[A-Z][a-z]*|[a-z]+|[A-Z]+(?![a-z])', text)
    for word in words:
        if "Charges" in word and len(word) > len("Charges"):
            separate = list(str(word).strip().partition("Charges"))
            newWord = " ".join(separate).strip()
            words[words.index(word)] = newWord
            
    return " ".join(words)

print(separate_words("Monthly andChargesand"))