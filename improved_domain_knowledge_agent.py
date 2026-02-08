"""
Enhanced Domain Knowledge Agent - Dataset-aware normalization
MUST run before any dataset access to normalize queries.
"""

from langchain_core.prompts import PromptTemplate
from langchain_core.messages import AIMessage
from typing import Dict, Any
import json


class ImprovedDomainKnowledgeAgent:
    """
    Dataset-aware normalization agent.
    Translates human language into exact database values.
    """

    def __init__(self, llm):
        self.llm = llm
        
        # Load actual database values for exact matching
        self.specialty_mappings = self._load_specialty_mappings()
        self.geographic_mappings = self._load_geographic_mappings()
        
        self.prompt = PromptTemplate.from_template("""
You are the Domain Knowledge Agent for a US healthcare dataset.

Your job is to NORMALIZE the user query into dataset-compatible constraints.
You do NOT answer the query.
You do NOT access data.
You ONLY translate human language into exact database values.

----------------------------------------
DATASET FACTS (AUTHORITATIVE)
----------------------------------------

1. Dataset contains ONLY US hospitals and doctors.

2. Geography:
   - State column: address_stateOrRegion (USPS codes ONLY)
   - City column: address_city
   - Coordinates: latitude, longitude

3. Specialties available in database (EXACT TEXT):
{available_specialties}

4. Departments available in database (EXACT TEXT):
{available_departments}

5. Facility types available:
{available_facility_types}

----------------------------------------
GEOGRAPHIC NORMALIZATION RULES
----------------------------------------

CRITICAL: ALWAYS output USPS state codes, NEVER full names.

US STATES BY REGION:

Northern US / Northern America:
{northern_states}

Southern US:
{southern_states}

Western US:
{western_states}

Eastern US:
{eastern_states}

Midwest US:
{midwest_states}

EXAMPLES:
- "Northern America" → ["WA", "OR", "ID", "MT", "WY", "ND", "SD", "MN", "WI", "MI", "IL", "IN", "OH", "PA", "NY", "VT", "NH", "ME", "MA", "CT", "RI"]
- "California" → ["CA"]
- "New York" → ["NY"]
- "Texas" → ["TX"]

----------------------------------------
MEDICAL NORMALIZATION RULES
----------------------------------------

CRITICAL: Map user terms to EXACT database values.

SPECIALTY MAPPINGS:
- "gynecologist" → "Obstetrics & Gynecology"
- "gynecology" → "Obstetrics & Gynecology"
- "OB/GYN" → "Obstetrics & Gynecology"
- "women's health" → "Obstetrics & Gynecology"
- "cardiologist" → "Cardiology"
- "heart doctor" → "Cardiology"
- "brain surgeon" → "Neurology" OR "Surgery"
- "eye doctor" → "Ophthalmology"
- "surgeon" → "Surgery"
- "emergency doctor" → "Emergency Medicine"
- "family doctor" → "Family Medicine"
- "pediatrician" → "Pediatrics"
- "psychiatrist" → "Psychiatry & Neurology"

PROCEDURE MAPPINGS:
- "C-section" → capability: "Obstetrics & Gynecology", department: "Obstetrics & Gynecology"
- "heart surgery" → capability: "Cardiology" or "Surgery"
- "cataract surgery" → capability: "Ophthalmology"

----------------------------------------
OUTPUT FORMAT (STRICT JSON)
----------------------------------------

Return ONLY valid JSON.
DO NOT include explanations.
DO NOT include markdown.

{{
  "normalized_query": {{
    "geography": {{
      "states": [],  // USPS codes ONLY
      "cities": [],
      "region_name": ""  // Original region name for reference
    }},
    "medical": {{
      "specialties": [],  // EXACT database values
      "departments": [],  // EXACT database values
      "capabilities": [],
      "procedures": [],
      "original_terms": []  // What user actually said
    }},
    "search_strategy": {{
      "use_specialty_column": true/false,
      "use_department_column": true/false,
      "use_capability_text": true/false,
      "fuzzy_matching_needed": true/false
    }},
    "sql_hints": {{
      "state_filter": "",  // SQL WHERE clause for states
      "specialty_filter": "",  // SQL WHERE clause for specialties
      "suggested_joins": []
    }}
  }},
  "warnings": [],  // Any ambiguities or assumptions made
  "confidence": "high/medium/low"
}}

----------------------------------------
USER QUERY:
{query}

NORMALIZATION:""")

    def _load_specialty_mappings(self) -> Dict[str, str]:
        """Load specialty mappings from uploaded data files."""
        return {
            # Common user terms -> exact database values
            "gynecologist": "Obstetrics & Gynecology",
            "gynecology": "Obstetrics & Gynecology",
            "ob/gyn": "Obstetrics & Gynecology",
            "obgyn": "Obstetrics & Gynecology",
            "women's health": "Obstetrics & Gynecology",
            "cardiologist": "Cardiology",
            "heart doctor": "Cardiology",
            "cardiac": "Cardiology",
            "neurologist": "Psychiatry & Neurology",
            "brain doctor": "Psychiatry & Neurology",
            "eye doctor": "Ophthalmology",
            "ophthalmologist": "Ophthalmology",
            "surgeon": "Surgery",
            "emergency": "Emergency Medicine",
            "emergency room": "Emergency Medicine",
            "er doctor": "Emergency Medicine",
            "family doctor": "Family Medicine",
            "general practice": "General Practice",
            "pediatrician": "Pediatrics",
            "child doctor": "Pediatrics",
            "psychiatrist": "Psychiatry & Neurology",
            "mental health": "Psychiatry & Neurology",
            "anesthesiologist": "Anesthesiology",
            "radiologist": "Radiology",
            "pathologist": "Pathology",
            "dermatologist": "Dermatology",
            "skin doctor": "Dermatology",
        }
    
    def _load_geographic_mappings(self) -> Dict[str, Any]:
        """Load geographic region mappings."""
        return {
            "northern_us": ["WA", "OR", "ID", "MT", "WY", "ND", "SD", "MN", 
                           "WI", "MI", "IL", "IN", "OH", "PA", "NY", "VT", 
                           "NH", "ME", "MA", "CT", "RI"],
            "northern_america": ["WA", "OR", "ID", "MT", "WY", "ND", "SD", "MN", 
                                "WI", "MI", "IL", "IN", "OH", "PA", "NY", "VT", 
                                "NH", "ME", "MA", "CT", "RI"],
            "southern_us": ["TX", "OK", "AR", "LA", "MS", "AL", "TN", "KY", 
                           "WV", "VA", "NC", "SC", "GA", "FL"],
            "western_us": ["WA", "OR", "CA", "NV", "ID", "MT", "WY", "UT", 
                          "CO", "AZ", "NM"],
            "eastern_us": ["ME", "NH", "VT", "MA", "RI", "CT", "NY", "PA", 
                          "NJ", "DE", "MD", "VA", "WV", "NC", "SC", "GA", "FL"],
            "midwest": ["OH", "IN", "IL", "MI", "WI", "MN", "IA", "MO", 
                       "ND", "SD", "NE", "KS"],
            "northeast": ["ME", "NH", "VT", "MA", "RI", "CT", "NY", "PA", "NJ"],
            "southeast": ["VA", "WV", "NC", "SC", "GA", "FL", "KY", "TN", 
                         "AL", "MS", "AR", "LA"],
            "southwest": ["TX", "OK", "NM", "AZ"],
            "pacific": ["WA", "OR", "CA", "AK", "HI"],
        }

    def _get_formatted_specialties(self) -> str:
        """Get formatted list of available specialties."""
        specialties = [
            "Allergy & Immunology",
            "Anesthesiology",
            "Cardiology",
            "Critical Care",
            "Dermatology",
            "Emergency Medicine",
            "Endocrinology",
            "Family Medicine",
            "Gastroenterology",
            "General Practice",
            "Hematology",
            "Infectious Disease",
            "Internal Medicine",
            "Nephrology",
            "Neurology",
            "Nuclear Medicine",
            "Obstetrics & Gynecology",
            "Ophthalmology",
            "Orthopedic Surgery",
            "Pain Management",
            "Pathology",
            "Pediatrics",
            "Physical Medicine & Rehabilitation",
            "Preventive Medicine",
            "Psychiatry",
            "Psychiatry & Neurology",
            "Radiology",
            "Rheumatology",
            "Sports Medicine",
            "Surgery",
            "Urology"
        ]
        return "\n".join(f"  - {s}" for s in specialties)
    
    def _get_formatted_departments(self) -> str:
        """Get formatted list of available departments."""
        departments = [
            "Anesthesiology",
            "Cardiology",
            "Critical Care",
            "Dermatology",
            "Emergency Medicine",
            "Endocrinology",
            "Family Medicine",
            "Gastroenterology",
            "General Practice",
            "Hematology",
            "Infectious Disease",
            "Internal Medicine",
            "Nephrology",
            "Neurology",
            "Nuclear Medicine",
            "Obstetrics & Gynecology",
            "Ophthalmology",
            "Orthopedic Surgery",
            "Pain Management",
            "Pathology",
            "Pediatrics",
            "Physical Medicine & Rehabilitation",
            "Preventive Medicine",
            "Psychiatry",
            "Radiology",
            "Rheumatology",
            "Sports Medicine",
            "Surgery",
            "Urology"
        ]
        return "\n".join(f"  - {d}" for d in departments)

    def _get_formatted_states(self, region_key: str) -> str:
        """Get formatted state list for a region."""
        states = self.geographic_mappings.get(region_key, [])
        return ", ".join(states)

    def normalize_query(self, user_query: str) -> Dict[str, Any]:
        """
        Normalize user query into database-compatible format.
        
        Args:
            user_query: Raw user question
            
        Returns:
            Normalized query constraints
        """
        # First, try simple keyword matching for speed
        normalized = self._quick_normalize(user_query)
        
        if normalized["confidence"] == "high":
            return normalized
        
        # Fall back to LLM for complex queries
        return self._llm_normalize(user_query)
    
    def _quick_normalize(self, query: str) -> Dict[str, Any]:
        """Quick rule-based normalization."""
        query_lower = query.lower()
        result = {
            "normalized_query": {
                "geography": {"states": [], "cities": [], "region_name": ""},
                "medical": {
                    "specialties": [],
                    "departments": [],
                    "capabilities": [],
                    "procedures": [],
                    "original_terms": []
                },
                "search_strategy": {
                    "use_specialty_column": False,
                    "use_department_column": False,
                    "use_capability_text": False,
                    "fuzzy_matching_needed": False
                },
                "sql_hints": {
                    "state_filter": "",
                    "specialty_filter": "",
                    "suggested_joins": []
                }
            },
            "warnings": [],
            "confidence": "low"
        }
        
        # Geographic normalization
        for region_name, states in self.geographic_mappings.items():
            if region_name.replace("_", " ") in query_lower:
                result["normalized_query"]["geography"]["states"] = states
                result["normalized_query"]["geography"]["region_name"] = region_name
                result["normalized_query"]["sql_hints"]["state_filter"] = \
                    f"address_stateOrRegion IN ({','.join(repr(s) for s in states)})"
                result["confidence"] = "high"
                break
        
        # Check individual states
        state_map = {
            "california": "CA", "texas": "TX", "new york": "NY", 
            "florida": "FL", "illinois": "IL", "pennsylvania": "PA",
            "ohio": "OH", "georgia": "GA", "michigan": "MI",
            "north carolina": "NC", "washington": "WA"
        }
        for state_name, code in state_map.items():
            if state_name in query_lower:
                result["normalized_query"]["geography"]["states"] = [code]
                result["normalized_query"]["sql_hints"]["state_filter"] = \
                    f"address_stateOrRegion = '{code}'"
                result["confidence"] = "high"
                break
        
        # Medical term normalization
        for user_term, db_value in self.specialty_mappings.items():
            if user_term in query_lower:
                result["normalized_query"]["medical"]["specialties"].append(db_value)
                result["normalized_query"]["medical"]["original_terms"].append(user_term)
                result["normalized_query"]["search_strategy"]["use_specialty_column"] = True
                result["normalized_query"]["sql_hints"]["specialty_filter"] = \
                    f"LOWER(specialty) LIKE '%{db_value.lower()}%'"
                result["confidence"] = "high"
        
        return result
    
    def _llm_normalize(self, query: str) -> Dict[str, Any]:
        """LLM-based normalization for complex queries."""
        prompt_text = self.prompt.format(
            query=query,
            available_specialties=self._get_formatted_specialties(),
            available_departments=self._get_formatted_departments(),
            available_facility_types="Hospital, Clinic, Medical Center",
            northern_states=self._get_formatted_states("northern_america"),
            southern_states=self._get_formatted_states("southern_us"),
            western_states=self._get_formatted_states("western_us"),
            eastern_states=self._get_formatted_states("eastern_us"),
            midwest_states=self._get_formatted_states("midwest")
        )
        
        response = self.llm.invoke(prompt_text)
        content = response.content.strip()
        
        # Clean JSON
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        try:
            normalized = json.loads(content)
            return normalized
        except json.JSONDecodeError as e:
            print(f"⚠️ Failed to parse LLM response: {e}")
            print(f"Response was: {content}")
            # Return empty normalization
            return {
                "normalized_query": {
                    "geography": {"states": [], "cities": [], "region_name": ""},
                    "medical": {
                        "specialties": [],
                        "departments": [],
                        "capabilities": [],
                        "procedures": [],
                        "original_terms": []
                    },
                    "search_strategy": {
                        "use_specialty_column": False,
                        "use_department_column": False,
                        "use_capability_text": False,
                        "fuzzy_matching_needed": True
                    },
                    "sql_hints": {
                        "state_filter": "",
                        "specialty_filter": "",
                        "suggested_joins": []
                    }
                },
                "warnings": ["Failed to parse normalization"],
                "confidence": "low"
            }

    def __call__(self, state: Dict) -> Dict:
        """
        LangGraph node interface.
        
        Args:
            state: AppState dictionary
            
        Returns:
            Partial state update with normalized constraints
        """
        user_query = state["messages"][-1].content
        
        # Normalize the query
        normalized = self.normalize_query(user_query)
        
        print(f"\n🧠 Domain Knowledge Agent: Query normalized")
        print(f"   Geography: {normalized['normalized_query']['geography']}")
        print(f"   Medical: {normalized['normalized_query']['medical']['specialties']}")
        print(f"   Confidence: {normalized['confidence']}")
        
        return ({
            "normalized_constraints": normalized,
            "messages": state["messages"] + [
                AIMessage(content=f"Query normalized (confidence: {normalized['confidence']})")
            ]
        })


# def __call__(self, state: Dict) -> Dict:
#     user_query = state["messages"][-1].content
    
#     # Normalize the query
#     normalized = self.normalize_query(user_query)
    
#     print(f"\n🧠 Domain Knowledge Agent: Query normalized")
#     print(f"   Geography: {normalized['normalized_query']['geography']}")
#     print(f"   Medical: {normalized['normalized_query']['medical']['specialties']}")
#     print(f"   Confidence: {normalized['confidence']}")
    
#     # Extract the data from normalized (NOT from empty state!)
#     geography = normalized['normalized_query']['geography']
#     medical = normalized['normalized_query']['medical']
#     sql_hints = normalized['normalized_query']['sql_hints']
#     warnings = normalized.get('warnings', [])
#     confidence = normalized.get('confidence', 'low')
    
#     return {
#         "normalized_constraints": {
#             "geography": geography,
#             "medical": medical,
#             "sql_hints": sql_hints,
#             "warnings": warnings,
#             "confidence": confidence
#         },
#         "messages": state["messages"] + [
#             AIMessage(content=f"Query normalized (confidence: {confidence})")
#         ]
#     }