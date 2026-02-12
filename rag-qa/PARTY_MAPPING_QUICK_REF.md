# Party Mapping - Quick Reference

## Supported Party Shortcuts

### Major Parties

| Shortcut | Official Name | Symbol |
|----------|--------------|--------|
| **NC** | Nepali Congress (नेपाली काँग्रेस) | रुख (Tree) |
| **UML** | Communist Party of Nepal (नेपाल कम्युनिष्ट पार्टी (एकीकृत मार्क्सवादी लेनिनवादी)) | सुर्य (Sun) |
| **RSP** | Rastriya Swatantra Party (राष्ट्रिय स्वतन्त्र पार्टी) | घण्टी (Bell) |
| **NCP** | Nepali Communist Party (नेपाली कम्युनिष्ट पार्टी) | पाँचकुने तारा (Star) |
| **MNO** | Mongol National Organization (मंगोल नेशनल अर्गनाइजेसन) | कुखुराको भाले |
| **Chim** | Ujjaya Nepal Party (उज्यालो नेपाल पार्टी) | बलिरहेको बिजुलीको चिम |
| **Swatantra** | Independent (स्वतन्त्र) | मुढा |

### Common Aliases

**Nepali Congress (नेपाली काँग्रेस)**
- NC, Congress, rukh, tree, काँग्रेस

**Communist Party of Nepal UML (नेपाल कम्युनिष्ट पार्टी (एकीकृत मार्क्सवादी लेनिनवादी))**
- UML, Yemale, Surya, Sun, CPN-UML, यमले, सूर्य

**Rastriya Swatantra Party (राष्ट्रिय स्वतन्त्र पार्टी)**
- RSP, Rasapa, Ra Sa Pa, Ghati, Bell, रा सा पा

**Nepali Communist Party (नेपाली कम्युनिष्ट पार्टी)**
- NCP, Tara, Star, पाँचकुने तारा

**Mongol National Organization (मंगोल नेशनल अर्गनाइजेसन)**
- MNO, Mongol, एमएनओ

**Ujjaya Nepal Party (उज्यालो नेपाल पार्टी)**
- Chim, Victory Nepal, चिम

**Independent (स्वतन्त्र)**
- Swatantra, Swotantra, स्वतन्त्र, स्वतंत्र

## Query Examples

You can now use any of these shortcuts in your queries:

✓ "How many **NC** candidates are there?"
✓ "Show **UML** candidates in Kathmandu"
✓ "List **RSP** candidates with PhD"
✓ "Compare **MNO** and **Chim** parties"
✓ "Count **NCP** candidates under 30"
✓ "Show **swatantra** (independent) candidates"
✓ "Find **tara** party candidates"
✓ "**ghati** candidates by education level"
✓ "**yemale** party average age"
✓ "**congress** candidates in Morang"
✓ "**surya** party in area 1"
✓ "**MNO** party symbol"
✓ "**ra sa pa** candidates count"
✓ "**star** party candidates"
✓ "**chim** party total seats"

## All 183 Supported Names

The system supports 183 unique party names including:
- 24 official party names
- 159 aliases and shortcuts

All automatically mapped to correct official Nepali names for database queries!

## Implementation Details

**Files Created:**
1. `config/party_mapping.py` - Main mapping data
2. `config/PARTY_MAPPING_README.md` - Full documentation
3. `test_party_mapping.py` - Basic tests
4. `test_party_mapping_integration.py` - Integration tests

**Integration Points:**
- SQL Generator service (uses party context in LLM prompts)
- Intent Extractor (recognizes party aliases)
- System Prompt (accesses party mapping)

## Testing

```bash
# Run tests
cd rag-qa
python3 test_party_mapping.py
```

All tests passing ✓
