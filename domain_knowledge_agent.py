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

2. Geography:
   - State column: address_stateOrRegion (USPS codes)
   - City column: address_city
   - Coordinates: latitude, longitude

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
- ALWAYS output USPS state codes.

"Northern America" or "Northern US" means:

WA, OR, ID, MT, WY,
ND, SD, MN, WI, MI,
IL, IN, OH,
PA, NY,
VT, NH, ME, MA, CT, RI

----------------------------------------
MEDICAL NORMALIZATION RULES
----------------------------------------

- gynecologist → Obstetrics & Gynecology
- OB/GYN → Obstetrics & Gynecology
- women's health → Obstetrics & Gynecology
- C-section → Obstetrics / Labor & Delivery

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

        response = self.llm.invoke(
            self.prompt.format(query=user_query)
        )

        # HARD SAFETY: ensure valid JSON
        try:
            normalized_constraints = json.loads(response.content)
        except Exception as e:
            raise ValueError(
                f"DomainKnowledgeAgent produced invalid JSON:\n{response.content}"
            )

        return {
            "normalized_constraints": normalized_constraints,
            "messages": state["messages"] + [
                AIMessage(content="Query normalized for dataset compatibility.")
            ]
        }
