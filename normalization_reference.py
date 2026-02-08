"""
QUICK REFERENCE: Normalization Mappings
========================================

This file contains all the mappings used by the Domain Knowledge Agent
to translate user language into exact database values.
"""


# ============================================================
# GEOGRAPHIC MAPPINGS
# ============================================================

GEOGRAPHIC_REGIONS = {
    
    "Northern US / Northern America": [
        "WA", "OR", "ID", "MT", "WY",  # Northwest
        "ND", "SD", "MN",               # North Central
        "WI", "MI",                     # Great Lakes
        "IL", "IN", "OH",               # Midwest overlap
        "PA", "NY",                     # Mid-Atlantic
        "VT", "NH", "ME",               # New England
        "MA", "CT", "RI"                # New England
    ],
    
    "Southern US": [
        "TX", "OK", "AR", "LA",         # South Central
        "MS", "AL",                     # Deep South
        "TN", "KY",                     # Upper South
        "WV", "VA",                     # Border states
        "NC", "SC", "GA", "FL"          # Southeast
    ],
    
    "Western US": [
        "WA", "OR", "CA",               # Pacific
        "NV", "ID", "MT", "WY",         # Mountain West
        "UT", "CO", "AZ", "NM"          # Southwest overlap
    ],
    
    "Eastern US": [
        "ME", "NH", "VT", "MA", "RI", "CT",  # New England
        "NY", "PA", "NJ", "DE", "MD",        # Mid-Atlantic
        "VA", "WV", "NC", "SC", "GA", "FL"   # Southeast
    ],
    
    "Midwest": [
        "OH", "IN", "IL", "MI", "WI",   # East North Central
        "MN", "IA", "MO",                # West North Central
        "ND", "SD", "NE", "KS"          # Great Plains
    ],
    
    "Northeast": [
        "ME", "NH", "VT", "MA", "RI", "CT",  # New England
        "NY", "PA", "NJ"                      # Mid-Atlantic core
    ],
    
    "Southeast": [
        "VA", "WV", "NC", "SC", "GA", "FL",  # South Atlantic
        "KY", "TN", "AL", "MS", "AR", "LA"   # East South Central
    ],
    
    "Southwest": [
        "TX", "OK", "NM", "AZ"          # Southwest core
    ],
    
    "Pacific": [
        "WA", "OR", "CA",               # West Coast
        "AK", "HI"                       # Pacific islands/Alaska
    ]
}


INDIVIDUAL_STATES = {
    # Full name → USPS code
    "alabama": "AL",
    "alaska": "AK",
    "arizona": "AZ",
    "arkansas": "AR",
    "california": "CA",
    "colorado": "CO",
    "connecticut": "CT",
    "delaware": "DE",
    "florida": "FL",
    "georgia": "GA",
    "hawaii": "HI",
    "idaho": "ID",
    "illinois": "IL",
    "indiana": "IN",
    "iowa": "IA",
    "kansas": "KS",
    "kentucky": "KY",
    "louisiana": "LA",
    "maine": "ME",
    "maryland": "MD",
    "massachusetts": "MA",
    "michigan": "MI",
    "minnesota": "MN",
    "mississippi": "MS",
    "missouri": "MO",
    "montana": "MT",
    "nebraska": "NE",
    "nevada": "NV",
    "new hampshire": "NH",
    "new jersey": "NJ",
    "new mexico": "NM",
    "new york": "NY",
    "north carolina": "NC",
    "north dakota": "ND",
    "ohio": "OH",
    "oklahoma": "OK",
    "oregon": "OR",
    "pennsylvania": "PA",
    "rhode island": "RI",
    "south carolina": "SC",
    "south dakota": "SD",
    "tennessee": "TN",
    "texas": "TX",
    "utah": "UT",
    "vermont": "VT",
    "virginia": "VA",
    "washington": "WA",
    "west virginia": "WV",
    "wisconsin": "WI",
    "wyoming": "WY",
    "district of columbia": "DC"
}


# ============================================================
# MEDICAL SPECIALTY MAPPINGS
# ============================================================

SPECIALTY_MAPPINGS = {
    # User term → Exact database value
    
    # Women's Health
    "gynecologist": "Obstetrics & Gynecology",
    "gynecology": "Obstetrics & Gynecology",
    "ob/gyn": "Obstetrics & Gynecology",
    "obgyn": "Obstetrics & Gynecology",
    "women's health": "Obstetrics & Gynecology",
    "obstetrician": "Obstetrics & Gynecology",
    
    # Cardiology
    "cardiologist": "Cardiology",
    "heart doctor": "Cardiology",
    "cardiac": "Cardiology",
    "cardiovascular": "Cardiology",
    
    # Neurology
    "neurologist": "Psychiatry & Neurology",
    "brain doctor": "Psychiatry & Neurology",
    "neuro": "Psychiatry & Neurology",
    
    # Ophthalmology
    "eye doctor": "Ophthalmology",
    "ophthalmologist": "Ophthalmology",
    "optometrist": "Ophthalmology",
    
    # Surgery
    "surgeon": "Surgery",
    "surgical": "Surgery",
    
    # Emergency
    "emergency": "Emergency Medicine",
    "emergency room": "Emergency Medicine",
    "er doctor": "Emergency Medicine",
    "emergency physician": "Emergency Medicine",
    
    # Primary Care
    "family doctor": "Family Medicine",
    "family physician": "Family Medicine",
    "general practice": "General Practice",
    "gp": "General Practice",
    "primary care": "Family Medicine",
    
    # Pediatrics
    "pediatrician": "Pediatrics",
    "child doctor": "Pediatrics",
    "pediatric": "Pediatrics",
    
    # Mental Health
    "psychiatrist": "Psychiatry & Neurology",
    "mental health": "Psychiatry & Neurology",
    "psychologist": "Psychologist",
    
    # Specialists
    "anesthesiologist": "Anesthesiology",
    "radiologist": "Radiology",
    "pathologist": "Pathology",
    "dermatologist": "Dermatology",
    "skin doctor": "Dermatology",
    "orthopedist": "Orthopedic Surgery",
    "bone doctor": "Orthopedic Surgery",
    "urologist": "Urology",
    "gastroenterologist": "Gastroenterology",
    "endocrinologist": "Endocrinology",
    "nephrologist": "Nephrology",
    "kidney doctor": "Nephrology",
    "rheumatologist": "Rheumatology"
}


# ============================================================
# DEPARTMENT MAPPINGS
# ============================================================

DEPARTMENT_MAPPINGS = {
    # Similar to specialties but for departments
    "gynecology": "Obstetrics & Gynecology",
    "ob/gyn": "Obstetrics & Gynecology",
    "cardiology": "Cardiology",
    "heart": "Cardiology",
    "emergency": "Emergency Medicine",
    "er": "Emergency Medicine",
    "surgery": "Surgery",
    "surgical": "Surgery",
    "pediatrics": "Pediatrics",
    "children": "Pediatrics",
    "internal medicine": "Internal Medicine",
    "family medicine": "Family Medicine",
    "radiology": "Radiology",
    "imaging": "Radiology",
    "pathology": "Pathology",
    "anesthesiology": "Anesthesiology"
}


# ============================================================
# PROCEDURE MAPPINGS
# ============================================================

PROCEDURE_MAPPINGS = {
    # Procedure → Specialty/Department
    "c-section": {
        "specialty": "Obstetrics & Gynecology",
        "department": "Obstetrics & Gynecology"
    },
    "cesarean": {
        "specialty": "Obstetrics & Gynecology",
        "department": "Obstetrics & Gynecology"
    },
    "delivery": {
        "specialty": "Obstetrics & Gynecology",
        "department": "Obstetrics & Gynecology"
    },
    "heart surgery": {
        "specialty": "Surgery",
        "department": "Cardiology"
    },
    "bypass": {
        "specialty": "Surgery",
        "department": "Cardiology"
    },
    "angioplasty": {
        "specialty": "Cardiology",
        "department": "Cardiology"
    },
    "cataract surgery": {
        "specialty": "Ophthalmology",
        "department": "Ophthalmology"
    },
    "knee replacement": {
        "specialty": "Orthopedic Surgery",
        "department": "Orthopedic Surgery"
    },
    "hip replacement": {
        "specialty": "Orthopedic Surgery",
        "department": "Orthopedic Surgery"
    }
}


# ============================================================
# USAGE EXAMPLES
# ============================================================

USAGE_EXAMPLES = {
    "Example 1": {
        "user_query": "Give me doctors in gynecology in northern america",
        "normalized_geography": ["WA", "OR", "ID", "MT", "WY", "ND", "SD", "MN", 
                                 "WI", "MI", "IL", "IN", "OH", "PA", "NY", "VT", 
                                 "NH", "ME", "MA", "CT", "RI"],
        "normalized_specialty": "Obstetrics & Gynecology",
        "sql_filter_geography": "address_stateOrRegion IN ('WA','OR',...)",
        "sql_filter_specialty": "LOWER(specialty) LIKE '%obstetrics & gynecology%'"
    },
    
    "Example 2": {
        "user_query": "Find cardiologists in California",
        "normalized_geography": ["CA"],
        "normalized_specialty": "Cardiology",
        "sql_filter_geography": "address_stateOrRegion = 'CA'",
        "sql_filter_specialty": "LOWER(specialty) LIKE '%cardiology%'"
    },
    
    "Example 3": {
        "user_query": "Show pediatricians in the midwest",
        "normalized_geography": ["OH", "IN", "IL", "MI", "WI", "MN", "IA", "MO", 
                                "ND", "SD", "NE", "KS"],
        "normalized_specialty": "Pediatrics",
        "sql_filter_geography": "address_stateOrRegion IN ('OH','IN',...)",
        "sql_filter_specialty": "LOWER(specialty) LIKE '%pediatrics%'"
    },
    
    "Example 4": {
        "user_query": "Emergency medicine doctors in Texas",
        "normalized_geography": ["TX"],
        "normalized_specialty": "Emergency Medicine",
        "sql_filter_geography": "address_stateOrRegion = 'TX'",
        "sql_filter_specialty": "LOWER(specialty) LIKE '%emergency medicine%'"
    }
}


# ============================================================
# TESTING QUERIES
# ============================================================

TEST_QUERIES = [
    # Geographic variations
    "doctors in northern america",
    "hospitals in the south",
    "facilities in California",
    "clinics in the midwest",
    "providers in New York",
    
    # Medical term variations
    "gynecologists",
    "cardiologists",
    "heart doctors",
    "eye doctors",
    "brain surgeons",
    "emergency room doctors",
    "family physicians",
    
    # Combined
    "gynecology in northern america",
    "cardiologists in California",
    "pediatricians in the midwest",
    "emergency medicine in Texas",
    "surgeons in New York",
    "OB/GYN in Florida",
    "heart doctors in the northeast"
]


# ============================================================
# VALIDATION RULES
# ============================================================

VALIDATION_RULES = """
VALIDATION RULES FOR NORMALIZATION:

1. Geographic Normalization:
   ✓ ALWAYS output USPS 2-letter state codes
   ✓ NEVER output full state names
   ✓ For regions, expand to ALL constituent states
   ✓ For individual states, map full name → USPS code

2. Medical Normalization:
   ✓ Map user terms to EXACT database specialty names
   ✓ Use case-insensitive LIKE for SQL matching
   ✓ Include both specialty AND department where applicable
   ✓ Track original user terms for reference

3. SQL Generation:
   ✓ Use IN clause for multiple states
   ✓ Use = for single state
   ✓ Use LOWER() and LIKE for specialty matching
   ✓ Join tables as needed (doctors ↔ mapping ↔ hospitals)

4. Confidence Scoring:
   ✓ High: Direct mapping found for all terms
   ✓ Medium: Partial mapping, some ambiguity
   ✓ Low: No clear mapping, fuzzy matching needed
"""


if __name__ == "__main__":
    print("="*70)
    print("NORMALIZATION REFERENCE GUIDE")
    print("="*70)
    
    print(f"\n📍 Geographic Regions: {len(GEOGRAPHIC_REGIONS)}")
    for region, states in GEOGRAPHIC_REGIONS.items():
        print(f"   {region}: {len(states)} states")
    
    print(f"\n🏥 Medical Specialties: {len(SPECIALTY_MAPPINGS)} mappings")
    print(f"   Sample: gynecology → {SPECIALTY_MAPPINGS['gynecology']}")
    print(f"   Sample: cardiologist → {SPECIALTY_MAPPINGS['cardiologist']}")
    
    print(f"\n✅ Test Queries Available: {len(TEST_QUERIES)}")
    
    print(VALIDATION_RULES)