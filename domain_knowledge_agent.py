from langchain_core.prompts import PromptTemplate
from langchain_core.messages import AIMessage
from typing import Dict
import json

class DomainKnowledgeAgent:
    """
    Dataset-aware normalization agent.
    MUST run before any dataset access.
    """

    def __init__(self, llm):
        self.llm = llm

        self.prompt = PromptTemplate.from_template("""
You are the Domain Knowledge Agent for a US healthcare dataset.

Your job is to NORMALIZE the user query into dataset-compatible constraints.
You do NOT answer the query.
You do NOT access data.
You ONLY translate human language into schema-safe meaning.

----------------------------------------
DATASET FACTS (AUTHORITATIVE)
----------------------------------------

1. Dataset contains ONLY US hospitals and doctors.
   - NO Canadian facilities
   - NO Mexican facilities  
   - NO other international data
   - When user says "North America", they mean USA only

2. Geography:
   - State column: address_stateOrRegion (USPS codes)
   - City column: address_city
   - Coordinates: latitude, longitude
   - All locations are within the 50 US states + DC

3. Hospital capabilities are inferred from:
   - department_summary.department
   - doctors.specialty
   - hospital_doctor_mapping

4. Workforce means:
   COUNT(DISTINCT doctor_npi)

----------------------------------------
GEOGRAPHIC NORMALIZATION RULES
----------------------------------------

- NEVER output informal geography terms.
- ALWAYS output USPS state codes as an array in the "states" field.
- Dataset contains ONLY US data - ignore Canada, Mexico, or other countries.

CRITICAL: ALL queries are limited to United States ONLY.

COMPREHENSIVE US REGIONAL MAPPINGS:

"North America" OR "north america" OR "USA" OR "United States" OR "America" OR no location specified means ALL US states:
["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", 
 "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", 
 "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", 
 "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", 
 "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY", "DC"]

"East Coast" OR "Eastern US" OR "Atlantic Coast":
["ME", "NH", "VT", "MA", "RI", "CT", "NY", "NJ", "PA", "DE", "MD", "VA", "NC", "SC", "GA", "FL", "DC"]

"West Coast" OR "Western US" OR "Pacific Coast":
["WA", "OR", "CA", "AK", "HI"]

"South" OR "Southern US" OR "South Side" OR "Southern States":
["TX", "OK", "AR", "LA", "MS", "AL", "TN", "KY", "WV", "VA", "NC", "SC", "GA", "FL"]

"Midwest" OR "Middle America" OR "Central US":
["OH", "MI", "IN", "IL", "WI", "MN", "IA", "MO", "ND", "SD", "NE", "KS"]

"Southwest" OR "Southwestern US":
["AZ", "NM", "TX", "OK"]

"Northeast" OR "New England":
["ME", "NH", "VT", "MA", "RI", "CT", "NY", "NJ", "PA"]

"Mountain West" OR "Rocky Mountain States":
["MT", "ID", "WY", "NV", "UT", "CO", "AZ", "NM"]

"Pacific Northwest" OR "PNW":
["WA", "OR", "ID"]

"Sun Belt":
["CA", "AZ", "NM", "TX", "LA", "MS", "AL", "GA", "SC", "NC", "FL"]

INDIVIDUAL STATE MAPPINGS:
- "California" → ["CA"]
- "Texas" → ["TX"]
- "New York" → ["NY"]
- "Florida" → ["FL"]
etc.

MULTI-STATE EXAMPLES:
- "California and Texas" → ["CA", "TX"]
- "New York or Florida" → ["NY", "FL"]

EXAMPLES:
- "neurologists in north america" → states: [all 51 states + DC]
- "hospitals in California" → states: ["CA"]
- "doctors on the east coast" → states: [17 eastern states]
- "cardiologists in the south" → states: [14 southern states]
- "west coast facilities" → states: ["WA", "OR", "CA", "AK", "HI"]

----------------------------------------
MEDICAL NORMALIZATION RULES
----------------------------------------

CRITICAL: Map user terms to EXACT database specialty names.

- neurologist → Psychiatry & Neurology
- neurology → Psychiatry & Neurology
- brain doctor → Psychiatry & Neurology
- gynecologist → Obstetrics & Gynecology
- OB/GYN → Obstetrics & Gynecology
- women's health → Obstetrics & Gynecology
- C-section → Obstetrics / Labor & Delivery
- cardiologist → Cardiovascular Disease
- heart doctor → Cardiovascular Disease

----------------------------------------
OUTPUT FORMAT (STRICT JSON)
----------------------------------------

Return ONLY valid JSON.
DO NOT include explanations.
DO NOT include markdown.

{{
  "entity": "",
  "geography": {{
    "states": [],
    "cities": []
  }},
  "medical": {{
    "departments": [],
    "specialties": [],
    "capabilities": []
  }},
  "joins_required": [],
  "metrics": {{}},
  "assumptions": []
}}

----------------------------------------
USER QUERY:
{query}
""")

    def __call__(self, state: Dict) -> Dict:
        user_query = state["messages"][-1].content
        print("First shit l" , user_query)
        response = self.llm.invoke(
            self.prompt.format(query=user_query)
        )

        print("After shit" , response.content)

        # HARD SAFETY: ensure valid JSON
        try:
            normalized_constraints = json.loads(response.content)
        except Exception as e:
            raise ValueError(
                f"DomainKnowledgeAgent produced invalid JSON:\n{response.content}"
            )
        
        print("normalsed stuff" , normalized_constraints)
        # state.update({"normalized_constraints": normalized_constraints,
        #                "messages": state["messages"] + [
        #         AIMessage(content="Query normalized for dataset compatibility.")
        #     ]})
    
        return {
            **state,
            "normalized_constraints": normalized_constraints,
            "messages": state["messages"] + [
                AIMessage(content="Query normalized for dataset compatibility.")
            ]
        }