import json
def parse_until_dict(data):
    while isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            break
    return data
co = "{\"GOVERNMENT TAXES AND FEES AND T-MOBILE FEES AND CHARGES\": {\"COUNTY 911 \": 0.5, \"FEDERAL UNIVERSAL SERVICE FUND \": 0.02, \"LOCAL BANDO \": 0.24, \"NE UNIVERSAL SERVICE \": 1.75, \"STATE AND LOCAL SALES TAX \": 0.28, \"TRS SURCHARGE \": 0.03}, \"MONTHLY RECURRING CHARGES\": {\"BUS UNL DATA 10 GB HS \": 0.0, \"BUS UNL PHONE  10 NO AVD \": 10.0}, \"OTHER CHARGES\": {\"REGULATORY PROGRAMS AND TELCO RECOVERY FEE \": 3.49}}"

itemCat = "GOVERNMENT TAXES AND FEES AND T-MOBILE FEES AND CHARGES"
itemLst = ["REGULATORY PROGRAMS & TELCO RECOVERY FEE", "STATE & LOCAL SALES TAX", "STATE 911"]
co = parse_until_dict(co)
lst = co.keys()
if itemCat in lst:
    
    subDescriptions = list(co.get(itemCat).keys())
    subDescriptions.append("STATE 911")
    updated = [item for item in itemLst if item not in subDescriptions]
    print(updated)
    for itemDescription in updated:
        co[itemCat][itemDescription] = 0
else:
    co[itemCat] = {}
    for itemDescription in itemLst:
        co[itemCat][itemDescription] = 0
    
print(co)