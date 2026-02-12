#!/usr/bin/env python3
"""
Generate comprehensive district name mapping from database
"""

# All 77 districts from database in sorted order
districts_nepali = [
    "अछाम",
    "अर्घाखाँची",
    "इलाम",
    "उदयपुर",
    "ओखलढुंगा",
    "कञ्चनपुर",
    "कपिलबस्तु",
    "काठमाडौं",
    "काभ्रेपलाञ्चोक",
    "कालिकोट",
    "कास्की",
    "कैलाली",
    "खोटाङ",
    "गुल्मी",
    "गोरखा",
    "चितवन",
    "जाजरकोट",
    "जुम्ला",
    "झापा",
    "डडेलधुरा",
    "डोटी",
    "डोल्पा",
    "तनहुँ",
    "ताप्लेजुङ",
    "तेह्रथुम",
    "दाङ",
    "दार्चुला",
    "दैलेख",
    "दोलखा",
    "धनकुटा",
    "धनुषा",
    "धादिङ",
    "नवलपरासी (बर्दघाट सुस्ता पश्चिम)",
    "नवलपरासी (बर्दघाट सुस्ता पूर्व)",
    "नुवाकोट",
    "पर्वत",
    "पर्सा",
    "पाँचथर",
    "पाल्पा",
    "प्यूठान",
    "बर्दिया",
    "बाग्लुङ",
    "बारा",
    "बाग्लुङ",
    "बाँके",
    "बाजुरा",
    "बारा",
    "बैतडी",
    "भक्तपुर",
    "भोजपुर",
    "मकवानपुर",
    "मनाङ",
    "महोत्तरी",
    "मुगु",
    "मुस्ताङ",
    "मोरङ",
    "म्याग्दी",
    "रसुवा",
    "रामेछाप",
    "रुकुम (पश्चिम भाग)",
    "रुकुम (पूर्वी भाग)",
    "रूपन्देही",
    "रोल्पा",
    "रौतहट",
    "लमजुङ",
    "ललितपुर",
    "संखुवासभा",
    "सप्तरी",
    "सल्यान",
    "सिराहा",
    "सिन्धुपाल्चोक",
    "सिराहा",
    "सुनसरी",
    "सुर्खेत",
    "सोलुखुम्बु",
    "स्याङजा",
    "हुम्ला",
]

# Common English transliterations and variations
district_mapping = {
    # District 1: अछाम
    "achham": "अछाम",
    
    # District 2: अर्घाखाँची
    "arghakhachi": "अर्घाखाँची",
    
    # District 3: इलाम
    "ilam": "इलाम",
    
    # District 4: उदयपुर
    "udaypur": "उदयपुर",
    
    # District 5: ओखलढुंगा
    "okhaldhunga": "ओखलढुंगा",
    
    # District 6: कञ्चनपुर
    "kanchanpur": "कञ्चनपुर",
    
    # District 7: कपिलबस्तु
    "kapilbastu": "कपिलबस्तु",
    
    # District 8: काठमाडौं
    "kathmandu": "काठमाडौं",
    
    # District 9: काभ्रेपलाञ्चोक
    "kavrepalanchok": "काभ्रेपलाञ्चोक",
    
    # District 10: कालिकोट
    "kalikot": "कालिकोट",
    
    # District 11: कास्की
    "kaski": "कास्की",
    
    # District 12: कैलाली
    "kailali": "कैलाली",
    
    # District 13: खोटाङ
    "khotang": "खोटाङ",
    
    # District 14: गुल्मी
    "gulmi": "गुल्मी",
    
    # District 15: गोरखा
    "gorakha": "गोरखा",
    
    # District 16: चितवन
    "chitwan": "चितवन",
    
    # District 17: जाजरकोट
    "jajarkot": "जाजरकोट",
    
    # District 18: जुम्ला
    "jumla": "जुम्ला",
    
    # District 19: झापा
    "jhap": "झापा",
    
    # District 20: डडेलधुरा
    "dadeldhura": "डडेलधुरा",
    
    # District 21: डोटी
    "doti": "डोटी",
    
    # District 22: डोल्पा
    "dolpa": "डोल्पा",
    
    # District 23: तनहुँ
    "tanahun": "तनहुँ",
    
    # District 24: ताप्लेजुङ
    "taplejung": "ताप्लेजुङ",
    
    # District 25: तेह्रथुम
    "terhathum": "तेह्रथुम",
    
    # District 26: दाङ
    "dang": "दाङ",
    
    # District 27: दार्चुला
    "darchula": "दार्चुला",
    
    # District 28: दैलेख
    "dailekh": "दैलेख",
    
    # District 29: दोलखा
    "dolkha": "दोलखा",
    
    # District 30: धनकुटा
    "dhankuta": "धनकुटा",
    
    # District 31: धनुषा
    "dhankuta": "धनुषा",
    
    # District 32: धादिङ
    "dhading": "धादिङ",
    
    # District 33: नवलपरासी (बर्दघाट सुस्ता पश्चिम)
    "nawalparasi": "नवलपरासी (बर्दघाट सुस्ता पश्चिम)",
    
    # District 34: नवलपरासी (बर्दघाट सुस्ता पूर्व)
    "nawalparasi": "नवलपरासी (बर्दघाट सुस्ता पूर्व)",
    
    # District 35: नुवाकोट
    "nuwakot": "नुवाकोट",
    
    # District 36: पर्वत
    "parbat": "पर्वत",
    
    # District 37: पर्सा
    "parsa": "पर्सा",
    
    # District 38: पाँचथर
    "panchthar": "पाँचथर",
    
    # District 39: पाल्पा
    "palpa": "पाल्पा",
    
    # District 40: प्यूठान
    "pyuthan": "प्यूठान",
    
    # District 41: बर्दिया
    "bardia": "बर्दिया",
    
    # District 42: बाग्लुङ
    "baglung": "बाग्लुङ",
    
    # District 43: बारा
    "bara": "बारा",
    
    # District 44: बाग्लुङ (Note: Another variation)
    "baglung2": "बाग्लुङ",
    
    # District 45: बाँके
    "bake": "बाँके",
    
    # District 46: बाजुरा
    "bajura": "बाजुरा",
    
    # District 47: बारा (Variation)
    "bara2": "बारा",
    
    # District 48: बैतडी
    "baitadi": "बैतडी",
    
    # District 49: भक्तपुर
    "bhaktapur": "भक्तपुर",
    
    # District 50: भोजपुर
    "bhaktapur": "भोजपुर",
    
    # District 51: मकवानपुर
    "makawanpur": "मकवानपुर",
    
    # District 52: मनाङ
    "manang": "मनाङ",
    
    # District 53: महोत्तरी
    "mahottari": "महोत्तरी",
    
    # District 54: मुगु
    "mugu": "मुगु",
    
    # District 55: मुस्ताङ
    "mustang": "मुस्ताङ",
    
    # District 56: मोरङ
    "morang": "मोरङ",
    
    # District 57: म्याग्दी
    "myagdi": "म्याग्दी",
    
    # District 58: रसुवा
    "rasuwa": "रसुवा",
    
    # District 59: रामेछाप
    "ramechhap": "रामेछाप",
    
    # District 60: रुकुम (पश्चिम भाग)
    "rukum": "रुकुम (पश्चिम भाग)",
    
    # District 61: रुकुम (पूर्वी भाग)
    "rukum2": "रुकुम (पूर्वी भाग)",
    
    # District 62: रूपन्देही
    "rupandehi": "रूपन्देही",
    
    # District 63: रोल्पा
    "rolpa": "रोल्पा",
    
    # District 64: रौतहट
    "rohat": "रौतहट",
    
    # District 65: लमजुङ
    "lamjung": "लमजुङ",
    
    # District 66: ललितपुर
    "lalitpur": "ललितपुर",
    
    # District 67: संखुवासभा
    "sankhuwasabha": "संखुवासभा",
    
    # District 68: सप्तरी
    "saptari": "सप्तरी",
    
    # District 69: सल्यान
    "salyan": "सल्यान",
    
    # District 70: सिराहा
    "siraha": "सिराहा",
    
    # District 71: सिन्धुपाल्चोक
    "sindhuplachok": "सिन्धुपाल्चोक",
    
    # District 72: सिराहा (Variation)
    "siraha2": "सिराहा",
    
    # District 73: सुनसरी
    "sunsari": "सुनसरी",
    
    # District 74: सुर्खेत
    "surkhet": "सुर्खेत",
    
    # District 75: सोलुखुम्बु
    "solukhumbu": "सोलुखुम्बु",
    
    # District 76: स्याङजा
    "syangja": "स्याङजा",
    
    # District 77: हुम्ला
    "humla": "हुम्ला",
}

# Common transliterations - add more variations
transliteration_mapping = {
    "sunsari": "सुनसरी",
    "sunseri": "सुनसरी",
    "sunsaree": "सुनसरी",
    "sunsare": "सुनसरी",
    "kathmandu": "काठमाडौं",
}

# Merge mappings
district_mapping.update(transliteration_mapping)

# Output as Python dict format
print("self.district_mapping = {")
for english, nepali in sorted(district_mapping.items()):
    print(f'    "{english}": "{nepali}",')
print("}")
