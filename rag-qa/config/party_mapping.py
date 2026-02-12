"""
Political Party Mapping for Nepal Elections

Handles party name aliases and shortcuts commonly used by users.
Maps user-input shortcuts to official party names in the database.
"""

# Complete party mapping with aliases
PARTY_MAPPING = {
    # Nepali Congress (नेपाली काँग्रेस)
    "nepali congress": {
        "official_name": "नेपाली काँग्रेस",
        "official_name_english": "Nepali Congress",
        "symbol": "रुख",
        "aliases": ["nc", "congress", "rukh", "tree", "काँग्रेस"]
    },

    # Communist Party of Nepal (Unified Marxist-Leninist)
    "communist party of nepal (unified marxist-leninist)": {
        "official_name": "नेपाल कम्युनिष्ट पार्टी (एकीकृत मार्क्सवादी लेनिनवादी)",
        "official_name_english": "Communist Party of Nepal (Unified Marxist-Leninist)",
        "symbol": "सुर्य",
        "aliases": ["uml", "yemale", "surya", "sun", "cpn-uml", "unified marxist-leninist", "marxist-leninist", "यमले", "सूर्य", "communist party"]
    },

    # Nepali Communist Party
    "nepali communist party": {
        "official_name": "नेपाली कम्युनिष्ट पार्टी",
        "official_name_english": "Nepali Communist Party",
        "symbol": "पाँचकुने तारा",
        "aliases": ["ncp", "tara", "star", "पाँचकुने तारा", "communist party", "nepali communist", "communist"]
    },

    # Rastriya Swatantra Party
    "rastriya swatantra party": {
        "official_name": "राष्ट्रिय स्वतन्त्र पार्टी",
        "official_name_english": "Rastriya Swatantra Party (RSP)",
        "symbol": "घण्टी",
        "aliases": ["rsp", "rasapa", "ra sa pa", "ghati", "bell", "national liberal party", "swatantra", "liberal party", "रा सा पा", "स्वतन्त्र पार्टी"]
    },

    # Communist Party of Nepal (Maoist)
    "communist party of nepal (maoist)": {
        "official_name": "नेपाल कम्युनिस्ट पार्टी (माओवादी)",
        "official_name_english": "Communist Party of Nepal (Maoist)",
        "symbol": "गोलो घेराभित्र दुई पात भएको गुलाफको फूल",
        "aliases": ["maoist", "cpn-maoist", "maoist center", "flower", "maobaadi", "माओवादी", "माओवादी केन्द्र"]
    },

    # Janata Samajwadi Party, Nepal
    "janata samajwadi party": {
        "official_name": "जनता समाजवादी पार्टी, नेपाल",
        "official_name_english": "Janata Samajwadi Party, Nepal",
        "symbol": "ढल्केको छाता",
        "aliases": ["jsp", "jspan", "jspon", "samajwadi", "socialist", "people's socialist", "janata samajwadi", "जसपा", "समाजवादी", "जनता समाजवादी"]
    },

    # Mongol National Organization
    "mongol national organization": {
        "official_name": "मंगोल नेशनल अर्गनाइजेसन",
        "official_name_english": "Mongol National Organization",
        "symbol": "कुखुराको भाले",
        "aliases": ["mno", "mongol", "mongol national", "एमएनओ", "मंगोल"]
    },

    # Nepal Janmukti Party
    "nepal janmukti party": {
        "official_name": "नेपाल जनमुक्ति पार्टी",
        "official_name_english": "Nepal Janmukti Party",
        "symbol": "घर",
        "aliases": ["njp", "janmukti", "liberation party", "जनमुक्ति"]
    },

    # Ujjaya Nepal Party
    "ujjaya nepal party": {
        "official_name": "उज्यालो नेपाल पार्टी",
        "official_name_english": "Ujjaya Nepal Party",
        "symbol": "बलिरहेको बिजुलीको चिम",
        "aliases": ["chim", "victory nepal party", "ujjwal", "उज्यालो", "चिम"]
    },

    # Independent
    "independent": {
        "official_name": "स्वतन्त्र",
        "official_name_english": "Independent",
        "symbol": "मुढा",
        "aliases": ["swatantra", "swotantra", "independent candidate", "no party", "स्वतन्त्र", "स्वतंत्र"]
    },

    # National Democratic Party
    "national democratic party": {
        "official_name": "राष्ट्रिय प्रजातन्त्र पार्टी",
        "official_name_english": "National Democratic Party",
        "symbol": "हलो",
        "aliases": ["ndp", "rpp", "rastriya prajatantra", "राप्रपा", "democratic national"]
    },

    # Nepal Workers Farmers Party
    "nepal workers farmers party": {
        "official_name": "नेपाल मजदुर किसान पार्टी",
        "official_name_english": "Nepal Workers Farmers Party",
        "symbol": "मादल",
        "aliases": ["nwfp", "kisan majdur", "workers farmers", "मजदुर किसान"]
    },

    # Federal Democratic National Forum
    "federal democratic national forum": {
        "official_name": "संघीय लोकतान्त्रिक राष्ट्रिय मञ्च",
        "official_name_english": "Federal Democratic National Forum",
        "symbol": "दाप सहितको खुकुरी",
        "aliases": ["fdnf", "loktantrik", "federal democratic"]
    },

    # Communist Party of Nepal (United)
    "communist party of nepal (united)": {
        "official_name": "नेपाल कम्युनिष्ट पार्टी (संयुक्त)",
        "official_name_english": "Communist Party of Nepal (United)",
        "symbol": "हँसिया",
        "aliases": ["cpn-united", "sanyukta", "communist united", "संयुक्त", "हँसिया"]
    },

    # People's Party
    "people's party": {
        "official_name": "जनमत पार्टी",
        "official_name_english": "People's Party",
        "symbol": "लाउड स्पिकर",
        "aliases": ["janamat", "जनमत", "janata party"]
    },

    # Nepal Sadbhavana Party
    "nepal sadbhavana party": {
        "official_name": "नेपाल सद्भावना पार्टी",
        "official_name_english": "Nepal Sadbhavana Party",
        "symbol": "पञ्जा छाप",
        "aliases": ["nsp", "sadbhavana", "goodwill party", "सद्भावना"]
    },

    # Progressive Democratic Party
    "progressive democratic party": {
        "official_name": "प्रगतिशील लोकतान्त्रिक पार्टी",
        "official_name_english": "Progressive Democratic Party",
        "symbol": "खुलेको एकल आँखा",
        "aliases": ["pdp", "pragatisheel", "loktantrik", "progressive"]
    },

    # National Change Party
    "national change party": {
        "official_name": "राष्ट्रिय परिवर्तन पार्टी",
        "official_name_english": "National Change Party",
        "symbol": "बाँसुरी",
        "aliases": ["ncp-change", "parivartan", "change party", "परिवर्तन"]
    },

    # Inclusive Socialist Party
    "inclusive socialist party": {
        "official_name": "समावेशी समाजवादी पार्टी",
        "official_name_english": "Inclusive Socialist Party",
        "symbol": "श्रीवत्स समृद्धिको प्रतीक",
        "aliases": ["isp", "samaveshi", "inclusive", "समावेशी"]
    },

    # Nepal Democratic Party
    "nepal democratic party": {
        "official_name": "नेपाल लोकतान्त्रिक पार्टी",
        "official_name_english": "Nepal Democratic Party",
        "symbol": "दुई हात जोडेको नमस्कार",
        "aliases": ["ndp-nepal", "lok tantrik", "nepal loktantrik", "नेलोपा"]
    },

    # Nepal Janata Party
    "nepal janata party": {
        "official_name": "नेपाल जनता पार्टी",
        "official_name_english": "Nepal Janata Party",
        "symbol": "कमलको फूल",
        "aliases": ["njp", "nepal janata", "lotus party", "कमल"]
    },

    # Nepali Janata Dal
    "nepali janata dal": {
        "official_name": "नेपाली जनता दल",
        "official_name_english": "Nepali Janata Dal",
        "symbol": "सिट्ठी",
        "aliases": ["njd", "janata dal", "जनता दल"]
    },

    # Swabhiman Party
    "swabhiman party": {
        "official_name": "स्वाभिमान पार्टी",
        "official_name_english": "Swabhiman Party",
        "symbol": "बाली बोकेको महिलाको आकृति",
        "aliases": ["self-respect party", "स्वाभिमान", "swabhimana"]
    },
}

# Create reverse lookup (alias -> official name)
ALIAS_TO_OFFICIAL = {}
for official_name, info in PARTY_MAPPING.items():
    for alias in info["aliases"]:
        ALIAS_TO_OFFICIAL[alias.lower()] = official_name

# Also add official names to the lookup
ALIAS_TO_OFFICIAL.update({
    info["official_name"].lower(): official_name
    for official_name, info in PARTY_MAPPING.items()
})
ALIAS_TO_OFFICIAL.update({
    info["official_name_english"].lower(): official_name
    for official_name, info in PARTY_MAPPING.items()
})


def normalize_party_name(party_input: str) -> str:
    """
    Normalize party name input to official Nepali name.
    
    Args:
        party_input: User input for party name (can be alias, English, or Nepali)
        
    Returns:
        Official Nepali party name from database, or original input if not found
    """
    if not party_input:
        return party_input
    
    normalized = party_input.strip().lower()
    
    # Direct lookup
    if normalized in ALIAS_TO_OFFICIAL:
        official_key = ALIAS_TO_OFFICIAL[normalized]
        return PARTY_MAPPING[official_key]["official_name"]
    
    # Partial match - check if input contains any alias
    for alias, official_key in ALIAS_TO_OFFICIAL.items():
        if alias in normalized or normalized in alias:
            return PARTY_MAPPING[official_key]["official_name"]
    
    # Return original if no match found
    return party_input


def get_party_info(party_name: str) -> dict:
    """
    Get complete party information for a party name.
    
    Args:
        party_name: Party name (official, alias, English, or Nepali)
        
    Returns:
        Dictionary with party information or None if not found
    """
    if not party_name:
        return None
    
    normalized = party_name.strip().lower()
    
    # Try direct lookup
    if normalized in ALIAS_TO_OFFICIAL:
        official_key = ALIAS_TO_OFFICIAL[normalized]
        return PARTY_MAPPING[official_key]
    
    # Try partial match
    for alias, official_key in ALIAS_TO_OFFICIAL.items():
        if alias in normalized or normalized in alias:
            return PARTY_MAPPING[official_key]
    
    return None


def get_all_party_names() -> list:
    """
    Get list of all official party names and aliases.
    
    Returns:
        List of all party names and their aliases
    """
    all_names = []
    for official_name, info in PARTY_MAPPING.items():
        all_names.extend([official_name, info["official_name"], info["official_name_english"]])
        all_names.extend(info["aliases"])
    return list(set(all_names))


def get_party_mapping_context() -> str:
    """
    Get party mapping as formatted string for LLM context.
    
    Returns:
        Formatted string with party aliases and mappings
    """
    context = "=== POLITICAL PARTY MAPPING ===\n\n"
    context += "Use these mappings when users refer to parties by aliases or shortcuts:\n\n"
    
    for official_key, info in PARTY_MAPPING.items():
        aliases_str = ", ".join(info["aliases"])
        context += f"Official Name (English): {info['official_name_english']}\n"
        context += f"Official Name (Nepali): {info['official_name']}\n"
        context += f"Symbol: {info['symbol']}\n"
        context += f"Aliases/Shortcuts: {aliases_str}\n\n"
    
    context += """
IMPORTANT RULES:
- When users type "NC", "Congress", or "rukh", map to "नेपाली काँग्रेस"
- When users type "UML", "Yemale", or "Surya", map to "नेपाल कम्युनिष्ट पार्टी (एकीकृत मार्क्सवादी लेनिनवादी)"
- When users type "RSP", "Rasapa", "Ra Sa Pa", or "Ghati", map to "राष्ट्रिय स्वतन्त्र पार्टी"
- When users type "NCP", "Tara", map to "नेपाली कम्युनिष्ट पार्टी"
- When users type "MNO", map to "मंगोल नेशनल अर्गनाइजेसन"
- When users type "Chim", map to "उज्यालो नेपाल पार्टी"
- When users type "Swatantra" or "Swotantra", map to "स्वतन्त्र" (Independent)
- Always search using the OFFICIAL NEPALI NAME in the database
- Both English and Nepali party names may appear in queries
"""
    return context
