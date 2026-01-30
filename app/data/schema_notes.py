"""
Schema Documentation: Expected CSV Column Assumptions

This module documents the expected structure of election CSV files.
These are ASSUMPTIONS, not guarantees. The validator will check for
presence and handle missing columns gracefully.

================================
REQUIRED COLUMNS (Core Identity)
================================
These columns are expected to be present in all election CSV files.
If missing, the system will attempt to infer or fail gracefully.

- candidate_id: Unique identifier for the candidate
- candidate_name: Full name of the candidate
- party: Political party affiliation
- district: District name
- constituency: Constituency identifier/name
- province: Province name or identifier
- election_year: Year of the election (e.g., 2017, 2022, 2026)

======================================
OPTIONAL COLUMNS (Current Enrichment)
======================================
These columns enhance analysis but are not required. When present, they
enable richer metrics across multiple insight families.

- is_independent: Boolean flag indicating independent candidate status
- age: Candidate age at time of election
- gender: Gender identity (M/F/Other/Unknown)
- education_level: Highest education level achieved
- birth_district: District of birth
- symbol: Election symbol identifier
- votes_received: Number of votes received
- votes_percentage: Percentage of votes received
- is_winner: Boolean flag indicating if candidate won
- margin: Victory margin (if winner)
- total_voters: Total registered voters in constituency
- voter_turnout: Voter turnout percentage

================================
DATA QUALITY NOTES
================================
- Column names may vary in case (e.g., "Candidate_Name" vs "candidate_name")
- Some columns may have missing values (NaN/null)
- Date formats may vary across election years
- District/Province names may have spelling variations

================================
VALIDATION STRATEGY
================================
1. Normalize column names (lowercase, strip whitespace)
2. Check for required columns (warn or fail based on strict_validation)
3. Log missing optional columns
4. Attempt type inference and conversion
5. Provide data quality report

===========================================
FUTURE ENRICHMENT FOR ADVANCED INSIGHTS
===========================================
The following fields are not strictly required for core operation, but
are highly recommended to unlock advanced insights:

- dob: Date of birth (enables more precise age-based analysis)
- image_url: Candidate photo (for richer comparison UI)

================================
ENGLISH-TRANSLATED COLUMNS
================================
When present, these columns improve search and display (e.g. English UI):

- candidate_name_en: Candidate full name in English
- district_en: District in English
- birth_place_en: Birth place in English
- party_en: Political party in English
- province_en: State/Province in English
- province_np: State name in Nepali

CSV headers normalize to these names (e.g. "Candidate Full Name in English" → candidate_name_en,
"State name in English" / "State name in Nepali" → province_en / province_np).
Column "Q" (or "q") also maps to candidate_name_en and is used for the name in English.
Search matches against both original and _en columns; filters match both when _en exists.

For specific insight ideas:

- Age Gap Between Political Movements:
  - Requires consistent `age` or `dob` for most candidates.

- Education vs Political Path:
  - Requires `education_level` using a limited, documented vocabulary
    (e.g., below SLC, SLC, intermediate, bachelors, masters, PhD).

- Local Representation Authenticity:
  - Requires `birth_district` in addition to `district` so local vs
    outsider status can be inferred reliably.

- Symbol Overload / Ballot UX:
  - Requires `symbol` and consistent encoding of ballot structure at
    constituency level (number of symbols per ballot, symbol reuse).

- Gender Gap:
  - Strongly prefers explicit `gender` over inferred values. If any
    inference is applied, it should be documented and flagged in
    metrics as estimated, not exact.

Metadata to consider storing alongside these fields:
- `source`: where the data came from (official gazette, scraped site, manual entry)
- `confidence`: optional numeric or categorical confidence for inferred attributes
- `last_updated`: when enrichment was last modified

"""

# Expected required columns (made more flexible - only truly essential)
REQUIRED_COLUMNS = [
    "candidate_name",
    "party",
    "district",
]

# Expected optional columns
OPTIONAL_COLUMNS = [
    "candidate_id",
    "constituency",
    "province",
    "election_year",
    "is_independent",
    "age",
    "gender",
    "education_level",
    "academic_qualification_generalized",
    "birth_district",
    "symbol",
    "votes_received",
    "votes_percentage",
    "is_winner",
    "margin",
    "total_voters",
    "voter_turnout",
    "dob",
    "image_url",
    # English-translated columns (search and display)
    "candidate_name_en",
    "district_en",
    "birth_place_en",
    "party_en",
    "province_en",
    "province_np",
]

# Nepal district to province mapping
# Used to infer province from district if not provided
DISTRICT_TO_PROVINCE = {
    # Province 1 (Koshi)
    "ताप्लेजुङ": "कोशी प्रदेश", "taplejung": "Province 1",
    "पाँचथर": "कोशी प्रदेश", "panchthar": "Province 1",
    "इलाम": "कोशी प्रदेश", "ilam": "Province 1",
    "झापा": "कोशी प्रदेश", "jhapa": "Province 1",
    "मोरङ": "कोशी प्रदेश", "morang": "Province 1",
    "सुनसरी": "कोशी प्रदेश", "sunsari": "Province 1",
    "धनकुटा": "कोशी प्रदेश", "dhankuta": "Province 1",
    "तेह्रथुम": "कोशी प्रदेश", "terhathum": "Province 1",
    "संखुवासभा": "कोशी प्रदेश", "sankhuwasabha": "Province 1",
    "भोजपुर": "कोशी प्रदेश", "bhojpur": "Province 1",
    "सोलुखुम्बु": "कोशी प्रदेश", "solukhumbu": "Province 1",
    "ओखलढुंगा": "कोशी प्रदेश", "okhaldhunga": "Province 1",
    "खोटाङ": "कोशी प्रदेश", "khotang": "Province 1",
    "उदयपुर": "कोशी प्रदेश", "udayapur": "Province 1",
    
    # Province 2 (Madhesh)
    "सप्तरी": "मधेश प्रदेश", "saptari": "Province 2",
    "सिराहा": "मधेश प्रदेश", "siraha": "Province 2",
    "धनुषा": "मधेश प्रदेश", "dhanusha": "Province 2",
    "महोत्तरी": "मधेश प्रदेश", "mahottari": "Province 2",
    "सर्लाही": "मधेश प्रदेश", "sarlahi": "Province 2",
    "रौतहट": "मधेश प्रदेश", "rautahat": "Province 2",
    "बारा": "मधेश प्रदेश", "bara": "Province 2",
    "पर्सा": "मधेश प्रदेश", "parsa": "Province 2",
    
    # Province 3 (Bagmati)
    "दोलखा": "बागमती प्रदेश", "dolakha": "Province 3",
    "सिन्धुपाल्चोक": "बागमती प्रदेश", "sindhupalchok": "Province 3",
    "रसुवा": "बागमती प्रदेश", "rasuwa": "Province 3",
    "धादिङ": "बागमती प्रदेश", "dhading": "Province 3",
    "नुवाकोट": "बागमती प्रदेश", "nuwakot": "Province 3",
    "काठमाडौं": "बागमती प्रदेश", "kathmandu": "Province 3",
    "भक्तपुर": "बागमती प्रदेश", "bhaktapur": "Province 3",
    "ललितपुर": "बागमती प्रदेश", "lalitpur": "Province 3",
    "काभ्रेपलाञ्चोक": "बागमती प्रदेश", "kavrepalanchok": "Province 3",
    "रामेछाप": "बागमती प्रदेश", "ramechhap": "Province 3",
    "सिन्धुली": "बागमती प्रदेश", "sindhuli": "Province 3",
    "मकवानपुर": "बागमती प्रदेश", "makwanpur": "Province 3",
    "चितवन": "बागमती प्रदेश", "chitwan": "Province 3",
    
    # Province 4 (Gandaki)
    "गोरखा": "गण्डकी प्रदेश", "gorkha": "Province 4",
    "लम्जुङ": "गण्डकी प्रदेश", "lamjung": "Province 4",
    "तनहुँ": "गण्डकी प्रदेश", "tanahun": "Province 4",
    "स्याङ्जा": "गण्डकी प्रदेश", "syangja": "Province 4",
    "कास्की": "गण्डकी प्रदेश", "kaski": "Province 4",
    "मनाङ": "गण्डकी प्रदेश", "manang": "Province 4",
    "मुस्ताङ": "गण्डकी प्रदेश", "mustang": "Province 4",
    "म्याग्दी": "गण्डकी प्रदेश", "myagdi": "Province 4",
    "पर्वत": "गण्डकी प्रदेश", "parbat": "Province 4",
    "बागलुङ": "गण्डकी प्रदेश", "baglung": "Province 4",
    "नवलपरासी (बर्दघाट सुस्ता पूर्व)": "गण्डकी प्रदेश", "nawalparasi (bardaghat susta east)": "Province 4",
    
    # Province 5 (Lumbini)
    "रुपन्देही": "लुम्बिनी प्रदेश", "rupandehi": "Province 5",
    "कपिलवस्तु": "लुम्बिनी प्रदेश", "kapilvastu": "Province 5",
    "पाल्पा": "लुम्बिनी प्रदेश", "palpa": "Province 5",
    "अर्घाखाँची": "लुम्बिनी प्रदेश", "arghakhanchi": "Province 5",
    "गुल्मी": "लुम्बिनी प्रदेश", "gulmi": "Province 5",
    "रोल्पा": "लुम्बिनी प्रदेश", "rolpa": "Province 5",
    "प्युठान": "लुम्बिनी प्रदेश", "pyuthan": "Province 5",
    "रुकुम (पूर्वी भाग)": "लुम्बिनी प्रदेश", "rukum (east)": "Province 5",
    "दाङ": "लुम्बिनी प्रदेश", "dang": "Province 5",
    "बाँके": "लुम्बिनी प्रदेश", "banke": "Province 5",
    "बर्दिया": "लुम्बिनी प्रदेश", "bardiya": "Province 5",
    "नवलपरासी (बर्दघाट सुस्ता पश्चिम)": "लुम्बिनी प्रदेश", "nawalparasi (bardaghat susta west)": "Province 5",
    
    # Province 6 (Karnali)
    "डोल्पा": "कर्णाली प्रदेश", "dolpa": "Province 6",
    "मुगु": "कर्णाली प्रदेश", "mugu": "Province 6",
    "हुम्ला": "कर्णाली प्रदेश", "humla": "Province 6",
    "जुम्ला": "कर्णाली प्रदेश", "jumla": "Province 6",
    "कालिकोट": "कर्णाली प्रदेश", "kalikot": "Province 6",
    "दैलेख": "कर्णाली प्रदेश", "dailekh": "Province 6",
    "जाजरकोट": "कर्णाली प्रदेश", "jajarkot": "Province 6",
    "रुकुम (पश्चिमी भाग)": "कर्णाली प्रदेश", "rukum (west)": "Province 6",
    "सल्यान": "कर्णाली प्रदेश", "salyan": "Province 6",
    "सुर्खेत": "कर्णाली प्रदेश", "surkhet": "Province 6",
    
    # Province 7 (Sudurpashchim)
    "बाजुरा": "सुदूरपश्चिम प्रदेश", "bajura": "Province 7",
    "बझाङ": "सुदूरपश्चिम प्रदेश", "bajhang": "Province 7",
    "डोटी": "सुदूरपश्चिम प्रदेश", "doti": "Province 7",
    "अछाम": "सुदूरपश्चिम प्रदेश", "achham": "Province 7",
    "कैलाली": "सुदूरपश्चिम प्रदेश", "kailali": "Province 7",
    "कञ्चनपुर": "सुदूरपश्चिम प्रदेश", "kanchanpur": "Province 7",
    "डडेलधुरा": "सुदूरपश्चिम प्रदेश", "dadeldhura": "Province 7",
    "बैतडी": "सुदूरपश्चिम प्रदेश", "baitadi": "Province 7",
    "दार्चुला": "सुदूरपश्चिम प्रदेश", "darchula": "Province 7",
}

# Column name normalization mappings
# Maps common variations to standard names
COLUMN_NORMALIZATION = {
    # Candidate ID variations
    "candidate id": "candidate_id",
    "candidateid": "candidate_id",
    "index": "candidate_id",
    "id": "candidate_id",
    "sn": "candidate_id",
    "s.n.": "candidate_id",
    "serial no": "candidate_id",
    
    # Candidate name variations
    "candidate name": "candidate_name",
    "candidatename": "candidate_name",
    "candidate full name": "candidate_name",
    "candidate_full_name": "candidate_name",
    "name": "candidate_name",
    "full name": "candidate_name",
    
    # Party variations
    "political party": "party",
    "political_party": "party",
    "party name": "party",
    "partyname": "party",
    
    # District variations
    "dist": "district",
    "district name": "district",
    "districtname": "district",
    
    # Constituency / Election Area variations
    "constituency name": "constituency",
    "constituency id": "constituency",
    "election area": "constituency",
    "election_area": "constituency",
    "electorate": "constituency",
    "seat": "constituency",
    
    # Province variations
    "province name": "province",
    "prov": "province",
    "state": "province",
    
    # Election year variations
    "year": "election_year",
    "election year": "election_year",
    "electionyear": "election_year",
    
    # Symbol variations
    "election symbol": "symbol",
    "election_symbol": "symbol",
    "party symbol": "symbol",
    
    # Education variations
    "academic qualification": "education_level",
    "academic_qualification": "education_level",
    "academic qualification generalized": "academic_qualification_generalized",
    "academic_qualification_generalized": "academic_qualification_generalized",
    "education": "education_level",
    "education level": "education_level",
    "qualification": "education_level",
    
    # Birth place variations
    "birth place": "birth_district",
    "birth_place": "birth_district",
    "birthplace": "birth_district",
    "birth district": "birth_district",
    "birthdistrict": "birth_district",
    
    # DOB variations
    "date of birth": "dob",
    "dateofbirth": "dob",
    "birth date": "dob",
    
    # Gender variations
    "sex": "gender",
    
    # Independent flag variations
    "independent": "is_independent",
    "is independent": "is_independent",
    
    # Vote-related variations
    "votes": "votes_received",
    "votes received": "votes_received",
    "vote count": "votes_received",
    "vote percentage": "votes_percentage",
    "votes percentage": "votes_percentage",
    "% votes": "votes_percentage",
    
    # Winner variations
    "winner": "is_winner",
    "is winner": "is_winner",
    "won": "is_winner",
    
    # Margin variations
    "victory margin": "margin",
    "win margin": "margin",
    
    # Voter-related variations
    "total voters": "total_voters",
    "registered voters": "total_voters",
    "turnout": "voter_turnout",
    "voter turnout": "voter_turnout",
    "turnout percentage": "voter_turnout",
    
    # Image URL variations
    "image url": "image_url",
    "photo url": "image_url",
    "photo": "image_url",

    # English-translated columns (for search and display)
    "candidate full name in english": "candidate_name_en",
    "name in english": "candidate_name_en",
    "candidate name in english": "candidate_name_en",
    "q": "candidate_name_en",  # column Q = English name (per data spec)
    "district in english": "district_en",
    "birth place in english": "birth_place_en",
    "political party in english": "party_en",
    "state in english": "province_en",
    "state name in english": "province_en",
    "state name in nepali": "province_np",
}
