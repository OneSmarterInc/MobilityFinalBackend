import re
add1 = "7293 BEECHMONT AVE CINCINNATI, OH 45230-4125"
add2 = "PO BOX 16810  NEWARK,NJ 07101-6522"
addlst = add1.strip().replace(',',' ').split(" ")
addlst = [item for item in addlst if item]
print(addlst)
print(" ".join(addlst))
RemittanceZip = addlst[-1]
RemittanceState = addlst[-2]
RemittanceAdd = " ".join(addlst[0:3])
RemittanceCity = " ".join(addlst[3:-2])
print(RemittanceZip,RemittanceState,RemittanceAdd,RemittanceCity)

from addon import parse_until_dict
# RemittanceState = str(addlst[-2]).split(',')[1] if ',' in addlst[-2] else addlst[-2]
# RemittanceCity = str(addlst[-2]).split(',')[0] if ',' in addlst[-2] else " ".join(addlst[:3])
# RemittanceCity = RemittanceCity.replace(",","")

# print(RemittanceAdd, RemittanceCity, RemittanceState,RemittanceZip)
