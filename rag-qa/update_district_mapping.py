#!/usr/bin/env python3
"""
Update query_router.py with complete district mapping
"""

# Complete district mapping (English -> Nepali)
district_mapping = {
    # Achham District
    "achham": "अछाम",
    # Arghakhachi District  
    "arghakhachi": "अर्घाखाँची",
    # Bara District
    "bara": "बारा",
    # Bardia District
    "bardia": "बर्दिया",
    # Bhaktapur District
    "bhaktapur": "भक्तपुर",
    # Chitwan District
    "chitwan": "चितवन",
    # Dadeldhura District
    "dadeldhura": "डडेलधुरा",
    # Dang District
    "dang": "दाङ",
    # Dailekh District
    "dailekh": "दैलेख",
    # Dolkha District
    "dolkha": "दोलखा",
    # Dolpa District
    "dolpa": "डोल्पा",
    # Doti District
    "doti": "डोटी",
    # Gorkha District
    "gorakha": "गोरखा",
    # Gulmi District
    "gulmi": "गुल्मी",
    # Humla District
    "humla": "हुम्ला",
    # Ilam District
    "ilam": "इलाम",
    # Jajarkot District
    "jajarkot": "जाजरकोट",
    # Jhapa District
    "jhap": "झापा",
    # Jumla District
    "jumla": "जुम्ला",
    # Kailali District
    "kailali": "कैलाली",
    # Kalikot District
    "kalikot": "कालिकोट",
    # Kanchanpur District
    "kanchanpur": "कञ्चनपुर",
    # Kapilbastu District
    "kapilbastu": "कपिलबस्तु",
    # Kaski District
    "kaski": "कास्की",
    # Kathmandu District
    "kathmandu": "काठमाडौं",
    # Kavrepalanchok District
    "kavrepalanchok": "काभ्रेपलाञ्चोक",
    # Khotang District
    "khotang": "खोटाङ",
    # Lalitpur District
    "lalitpur": "ललितपुर",
    # Lamjung District
    "lamjung": "लमजुङ",
    # Mahottari District
    "mahottari": "महोत्तरी",
    # Makawanpur District
    "makawanpur": "मकवानपुर",
    # Manang District
    "manang": "मनाङ",
    # Mugu District
    "mugu": "मुगु",
    # Mustang District
    "mustang": "मुस्ताङ",
    # Myagdi District
    "myagdi": "म्याग्दी",
    # Nawalparasi District (Nawalparasi)
    "nawalparasi": "नवलपरासी (बर्दघाट सुस्ता पूर्व)",
    # Nawalparasi District (Nawalparasi variant)
    "nawalparasi2": "नवलपरासी (बर्दघाट सुस्ता पश्चिम)",
    # Nuwakot District
    "nuwakot": "नुवाकोट",
    # Okhaldhunga District
    "okhaldhunga": "ओखलढुंगा",
    # Palpa District
    "palpa": "पाल्पा",
    # Panchthar District
    "panchthar": "पाँचथर",
    # Parbat District
    "parbat": "पर्वत",
    # Parsa District
    "parsa": "पर्सा",
    # Pyuthan District
    "pyuthan": "प्यूठान",
    # Ramechhap District
    "ramechhap": "रामेछाप",
    # Rasuwa District
    "rasuwa": "रसुवा",
    # Rautahat District
    "rautahat": "रौतहट",
    # Rolpa District
    "rolpa": "रोल्पा",
    # Rukum District (with brackets)
    "rukum": "रुकुम (पश्चिम भाग)",
    # Rukum District (variant)
    "rukum2": "रुकुम (पूर्वी भाग)",
    # Rupandehi District
    "rupandehi": "रूपन्देही",
    # Salyan District
    "salyan": "सल्यान",
    # Sankhuwasabha District
    "sankhuwasabha": "संखुवासभा",
    # Saptari District
    "saptari": "सप्तरी",
    # Siraha District
    "siraha": "सिराहा",
    # Siraha District (variation)
    "siraha2": "सिराहा",
    # Solukhumbu District
    "solukhumbu": "सोलुखुम्बु",
    # Sunsari District
    "sunsari": "सुनसरी",
    # Sunseri District
    "sunseri": "सुनसरी",
    # Unsaree District
    "unsaree": "सुनसरी",
    # Surkhet District
    "surkhet": "सुर्खेत",
    # Syangja District
    "syangja": "स्याङजा",
    # Tanahun District
    "tanahun": "तनहुँ",
    # Taplejung District
    "taplejung": "ताप्लेजुङ",
    # Terhathum District
    "terhathum": "तेह्रथुम",
    # Udaypur District
    "udaypur": "उदयपुर",
    # Humla District
    "humla": "हुम्ला",
}

# Output as Python dict format
print("self.district_mapping = {")
for english, nepali in sorted(district_mapping.items()):
    print(f'    "{english}": "{nepali}",')
print("}")
