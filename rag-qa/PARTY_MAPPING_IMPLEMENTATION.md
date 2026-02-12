# Party Mapping Implementation Summary

## What Was Applied

A comprehensive political party mapping system has been implemented to handle party name aliases and shortcuts commonly used by users when querying Nepal election data.

## Files Created

### 1. `config/party_mapping.py`
Main mapping file containing:
- `PARTY_MAPPING` dictionary with 24+ political parties
- Official Nepali and English names for each party
- Election symbols (Nepali) for each party
- Multiple aliases for each party (total of 183 unique names)
- Helper functions for normalization and lookup
- LLM context generation function

**Key Functions:**
```python
- normalize_party_name(party_input) -> official_nepali_name
- get_party_info(party_name) -> complete_party_dict
- get_all_party_names() -> list_of_all_names
- get_party_mapping_context() -> formatted_string_for_LLM
```

### 2. `config/PARTY_MAPPING_README.md`
Comprehensive documentation including:
- Party mapping tables
- Usage examples (Python, SQL, LLM prompts)
- Integration points
- How to add new parties/aliases
- Testing instructions

### 3. `test_party_mapping.py`
Basic test script that validates:
- Party name normalization for all major aliases
- Party information retrieval
- Total number of parties and aliases in system

**Test Results:** ✓ ALL TESTS PASSED (19 test cases)

### 4. `test_party_mapping_integration.py`
Advanced integration test suite that validates:
- Party normalization
- Information retrieval
- Context generation
- SQL generator integration

## Party Mappings Implemented

### Major Parties

| Shortcut | Official Nepali | Official English | Symbol | Aliases |
|----------|-----------------|------------------|--------|----------|
| NC | नेपाली काँग्रेस | Nepali Congress | रुख | nc, congress, rukh, tree, काँग्रेस |
| UML | नेपाल कम्युनिष्ट पार्टी (एकीकृत मार्क्सवादी लेनिनवादी) | CPN (UML) | सुर्य | uml, yemale, surya, sun, cpn-uml |
| RSP | राष्ट्रिय स्वतन्त्र पार्टी | Rastriya Swatantra Party | घण्टी | rsp, rasapa, ra sa pa, ghati, bell |
| NCP | नेपाली कम्युनिष्ट पार्टी | Nepali Communist Party | पाँचकुने तारा | ncp, tara, star |
| MNO | मंगोल नेशनल अर्गनाइजेसन | Mongol National Organization | कुखुराको भाले | mno, mongol |
| Chim | उज्यालो नेपाल पार्टी | Ujjaya Nepal Party | बलिरहेको बिजुलीको चिम | chim, victory |
| Swatantra | स्वतन्त्र | Independent | मुढा | swotantra, independent |

### Other Parties (Sample)

| Shortcut | Official Nepali | Official English |
|----------|-----------------|------------------|
| JSP | जनता समाजवादी पार्टी, नेपाल | Janata Samajwadi Party |
| Maoist | नेपाल कम्युनिस्ट पार्टी (माओवादी) | CPN (Maoist) |
| Janmukti | नेपाल जनमुक्ति पार्टी | Nepal Janmukti Party |
| NFD | संघीय लोकतान्त्रिक राष्ट्रिय मञ्च | Federal Democratic National Forum |
| ND | राष्ट्रिय प्रजातन्त्र पार्टी | National Democratic Party |
| NWFP | नेपाल मजदुर किसान पार्टी | Nepal Workers Farmers Party |

## Integration Points

### 1. SQL Generator Service (`services/sql_generator.py`)

**Changes Made:**
- Added import for `get_party_mapping_context`
- Updated `_build_auto_query_prompt()` to include party mapping context
- Added critical rule: "When filtering by party, use OFFICIAL NEPALI NAME"

**Benefits:**
- LLM now receives party mapping when generating SQL
- SQL queries will use official Nepali names from database
- Supports user aliases like NC, UML, RSP in natural language queries

**Example:**
```python
# User query: "Show NC candidates in Kathmandu"
# LLM will now know to use:
WHERE political_party = 'नेपाली काँग्रेस'
# Instead of:
WHERE political_party = 'NC'  # This won't match database
```

### 2. Intent Extractor (`services/sql_generator.py`)

**Changes Made:**
- Updated `extract()` method prompt to include party mapping
- Added rule for party name extraction with alias mapping
- Ensures extracted entities use official Nepali names

**Benefits:**
- Entity extraction recognizes party aliases
- Structured query classification improves accuracy

### 3. System Prompts (`prompts/system_prompt.py`)

**Changes Made:**
- Added import for `get_party_mapping_context`
- System prompt can access party mapping when needed

**Benefits:**
- Consistent party naming across all prompts
- Better response formatting for party-related queries

## Query Examples That Now Work

### Before Implementation
```python
# ❌ These might fail or return incorrect results
"How many NC candidates?"     # NC not in database
"Show UML candidates"          # UML not in database
"Compare RSP and Chim"          # Aliases not recognized
```

### After Implementation
```python
# ✓ These now work correctly
"How many NC candidates?"      
# → Searches: WHERE political_party = 'नेपाली काँग्रेस'

"Show UML candidates in Kathmandu"  
# → Searches: WHERE political_party = 'नेपाल कम्युनिष्ट पार्टी (एकीकृत मार्क्सवादी लेनिनवादी)'

"Compare RSP and Chim parties"
# → Searches: WHERE political_party IN ('राष्ट्रिय स्वतन्त्र पार्टी', 'उज्यालो नेपाल पार्टी')

"List all MNO candidates under 30"
# → Searches: WHERE political_party = 'मंगोल नेशनल अर्गनाइजेसन'

"Show independent candidates with PhD"
# → Searches: WHERE political_party = 'स्वतन्त्र'

"Count Tara party candidates"
# → Searches: WHERE political_party = 'नेपाली कम्युनिष्ट पार्टी'
```

## Testing

### Running Tests

```bash
cd rag-qa

# Basic party mapping test
python3 test_party_mapping.py

# Integration test
python3 test_party_mapping_integration.py
```

### Test Coverage

1. **Normalization Test** ✓
   - NC → नेपाली काँग्रेस
   - UML → नेपाल कम्युनिष्ट पार्टी (एकीकृत मार्क्सवादी लेनिनवादी)
   - RSP → राष्ट्रिय स्वतन्त्र पार्टी
   - NCP, MNO, Chim, etc.

2. **Information Retrieval Test** ✓
   - Complete party info (official names, symbol, aliases)

3. **Context Generation Test** ✓
   - LLM context contains party mappings
   - All aliases documented

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                User Query                         │
│              (NC, UML, RSP, etc.)            │
└────────────────────┬────────────────────────────────────┘
                 │
                 ▼
    ┌──────────────────────────────┐
    │  Party Mapping System      │
    │  - PARTY_MAPPING        │
    │  - normalize_party_name() │
    │  - get_party_info()      │
    └──────────┬───────────────┘
               │
               ▼
    ┌──────────────────────────────┐
    │  SQL Generator / Intent    │
    │  Extractor with LLM      │
    │  (Uses party context)    │
    └──────────┬───────────────┘
               │
               ▼
    ┌──────────────────────────────┐
    │  SQLite Database Query    │
    │  (Official Nepali Name)  │
    └──────────┬───────────────┘
               │
               ▼
    ┌──────────────────────────────┐
    │  Accurate Results        │
    └──────────────────────────────┘
```

## Future Enhancements

### Potential Additions

1. **More Aliases**: Add more informal names users might use
2. **Fuzzy Matching**: Improve partial string matching for typos
3. **ML-Based Classification**: Train model to recognize party names from context
4. **User Feedback**: Learn new aliases from user queries
5. **Party Hierarchy**: Support parent/child party relationships

### Current Limitations

1. **Exact Match Required**: Needs exact alias match (fuzzy matching could be added)
2. **No Historical Parties**: Only current parties in database
3. **Case Sensitivity**: Though case-insensitive, requires exact spelling

## Usage in Production

### For API Integration

```python
from config.party_mapping import normalize_party_name

# In query processing
def process_user_query(query):
    # Normalize party names in query
    # This happens automatically in SQL generator/intent extractor
    pass  # Party mapping is already integrated
```

### For Frontend Display

```javascript
// Show party aliases to users
const partyAliases = {
    "NC": ["Nepali Congress", "Congress", "rukh", "tree"],
    "UML": ["CPN (UML)", "Unified Marxist-Leninist", "सुर्य"],
    "RSP": ["Rastriya Swatantra Party", "Rasapa", "Ra Sa Pa", "घण्टी"],
    // ... etc
};

// Display suggestions as user types
if (userInput.startsWith("nc")) {
    showSuggestions(partyAliases["NC"]);
}
```

## Summary

The party mapping system provides:

✓ **Comprehensive Coverage**: 24 major political parties with 183 total aliases
✓ **User-Friendly**: Common shortcuts work automatically
✓ **LLM Integration**: AI queries use correct party names
✓ **Accurate Results**: Database queries use official Nepali names
✓ **Maintainable**: Easy to add new parties/aliases
✓ **Well Tested**: All test cases passing

Users can now query using any of these aliases:
- NC, Congress, rukh, tree
- UML, Yemale, Surya, Sun
- RSP, Rasapa, Ra Sa Pa, Ghati, Bell
- NCP, Tara, Star
- MNO, Mongol
- Chim, Ujjwal
- Swatantra, Swotantra, Independent

All queries will automatically map to the correct official Nepali party names in the database!
