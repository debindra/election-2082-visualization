# Political Party Mapping System

## Overview

This system provides comprehensive mapping of political party names, aliases, and shortcuts used in Nepal's House of Representatives elections. It enables users to query election data using common shortcuts and aliases instead of needing to know the official party names.

## Supported Party Aliases

### Major Political Parties

| Shortcut / Alias | Official Party Name (English) | Official Party Name (Nepali) | Symbol |
|------------------|------------------------------|--------------------------------|---------|
| NC, Congress, rukh | Nepali Congress | नेपाली काँग्रेस | रुख (Tree) |
| UML, Yemale, Surya | Communist Party of Nepal (Unified Marxist-Leninist) | नेपाल कम्युनिष्ट पार्टी (एकीकृत मार्क्सवादी लेनिनवादी) | सुर्य (Sun) |
| RSP, Rasapa, Ra Sa Pa, Ghati | Rastriya Swatantra Party | राष्ट्रिय स्वतन्त्र पार्टी | घण्टी (Bell) |
| NCP, Tara | Nepali Communist Party | नेपाली कम्युनिष्ट पार्टी | पाँचकुने तारा (Star) |
| MNO | Mongol National Organization | मंगोल नेशनल अर्गनाइजेसन | कुखुराको भाले |
| Chim | Ujjaya Nepal Party | उज्यालो नेपाल पार्टी | बलिरहेको बिजुलीको चिम (Electric bulb) |
| Swatantra, Swotantra | Independent | स्वतन्त्र | मुढा |

### Other Parties

| Shortcut / Alias | Official Party Name (English) | Symbol |
|------------------|------------------------------|---------|
| JSP, Samajwadi | Janata Samajwadi Party, Nepal | ढल्केको छाता |
| Maoist | Communist Party of Nepal (Maoist) | गोलो घेराभित्र दुई पात भएको गुलाफको फूल |
| Janmukti | Nepal Janmukti Party | घर |
| NFD | Federal Democratic National Forum | दाप सहितको खुकुरी |
| ND | National Democratic Party | हलो |
| NWFP | Nepal Workers Farmers Party | मादल |

## Usage Examples

### In Python Code

```python
from config.party_mapping import normalize_party_name, get_party_info

# Normalize a user input party name
normalized = normalize_party_name("NC")
# Returns: "नेपाली काँग्रेस"

normalized = normalize_party_name("rasapa")
# Returns: "राष्ट्रिय स्वतन्त्र पार्टी"

normalized = normalize_party_name("surya")
# Returns: "नेपाल कम्युनिष्ट पार्टी (एकीकृत मार्क्सवादी लेनिनवादी)"

# Get complete party information
info = get_party_info("RSP")
# Returns: {
#     "official_name": "राष्ट्रिय स्वतन्त्र पार्टी",
#     "official_name_english": "Rastriya Swatantra Party (RSP)",
#     "symbol": "घण्टी",
#     "aliases": ["rsp", "rasapa", "ra sa pa", "ghati", "bell", ...]
# }
```

### In SQL Queries

When building SQL queries for party filters, always use the official Nepali name:

```sql
-- Good: Uses official Nepali name
SELECT * FROM candidates 
WHERE political_party = 'राष्ट्रिय स्वतन्त्र पार्टी'

-- Also works: Search both columns
SELECT * FROM candidates 
WHERE political_party LIKE '%नेपाली काँग्रेस%' 
   OR political_party_in_english LIKE '%Nepali Congress%'
```

### In LLM Prompts

Use `get_party_mapping_context()` to provide party mappings to the LLM:

```python
from config.party_mapping import get_party_mapping_context

party_context = get_party_mapping_context()
prompt = f"""
{party_context}

User Query: "Show me RSP candidates in Kathmandu"
"""
```

## How It Works

1. **Normalization**: The `normalize_party_name()` function converts any party input (alias, English, or Nepali) to the official Nepali name stored in the database.

2. **Reverse Lookup**: An internal dictionary maps all aliases back to their official names for fast lookup.

3. **LLM Integration**: The `get_party_mapping_context()` function formats party mappings as instructions for the LLM, ensuring it uses official names when generating SQL queries.

4. **Flexible Matching**: Supports:
   - Direct alias match (e.g., "NC" → Nepali Congress)
   - Partial match (e.g., "Congr" matches "Congress")
   - Case-insensitive matching
   - Both English and Nepali inputs

## Adding New Parties or Aliases

To add a new party or alias, edit `config/party_mapping.py`:

```python
PARTY_MAPPING = {
    # Add new party
    "official_party_name_english": {
        "official_name": "आधिकारिक नेपाली नाम",
        "official_name_english": "Official English Name",
        "symbol": "प्रतीक",
        "aliases": ["shortcut1", "shortcut2", "alias1"]
    },
    
    # Add aliases to existing party
    "existing_party_name_english": {
        # ... existing fields ...
        "aliases": ["new_alias1", "new_alias2", ...]
    },
}
```

After modifying the mapping:
1. Run the test script: `python3 test_party_mapping.py`
2. Verify the new aliases work correctly
3. The system will automatically rebuild the lookup dictionaries

## Testing

Run the test script to verify party mapping works correctly:

```bash
cd /Users/deb/Documents/Projects/election-visualization/rag-qa
python3 test_party_mapping.py
```

This will:
- Test normalization of common aliases
- Display detailed party information
- Show total number of parties and aliases in the system
- Display the LLM context format

## Integration Points

The party mapping is integrated into:

1. **SQL Generator** (`services/sql_generator.py`):
   - Provides party context to LLM for query generation
   - Ensures SQL queries use official party names

2. **Intent Extractor** (`services/sql_generator.py`):
   - Helps identify party names from user queries
   - Extracts party entities with proper mapping

## Database Schema Reference

The `candidates` table contains these party-related columns:

| Column | Type | Description |
|--------|-------|-------------|
| `political_party` | TEXT | Official Nepali party name (use for queries) |
| `political_party_in_english` | TEXT | English party name (use for display) |
| `Election Symbol` | TEXT | Party election symbol (emoji/pictogram) |

**Important**: When filtering by party in SQL queries, use the `political_party` column with the **official Nepali name** from the mapping.

## Benefits

1. **User-Friendly**: Users can type shortcuts like "NC", "UML", "RSP" instead of full party names
2. **Language-Agnostic**: Works with both Nepali and English inputs
3. **Flexible**: Handles partial matches and multiple variations
4. **Maintainable**: Centralized mapping makes updates easy
5. **LLM-Aware**: Provides context to ensure AI uses correct names

## Example Queries

After integration, users can ask:

- "How many NC candidates are there?"
- "Show UML candidates in Kathmandu"
- "Compare RSP and MNO candidates by education"
- "List all Chim party candidates"
- "Show independent candidates with PhD"
- "Count Tara party candidates under 30"

The system will automatically map:
- NC → नेपाली काँग्रेस
- UML → नेपाल कम्युनिष्ट पार्टी (एकीकृत मार्क्सवादी लेनिनवादी)
- RSP → राष्ट्रिय स्वतन्त्र पार्टी
- MNO → मंगोल नेशनल अर्गनाइजेसन
- Chim → उज्यालो नेपाल पार्टी
- Tara → नेपाली कम्युनिष्ट पार्टी

## Files

- `config/party_mapping.py` - Main mapping file with all party data
- `config/__init__.py` - Package initialization
- `test_party_mapping.py` - Test script for validation
- `config/PARTY_MAPPING_README.md` - This documentation file

## Support

For questions or issues:
1. Check the test output: `python3 test_party_mapping.py`
2. Verify the party name exists in `PARTY_MAPPING`
3. Check for typos in alias definitions
4. Ensure database uses the official Nepali names in `political_party` column
