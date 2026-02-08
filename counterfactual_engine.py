"""
CounterfactualEngine - Simulates "what-if" scenarios
Creates hypothetical facility states without mutating real data
"""

import uuid
import pandas as pd
from typing import Dict, Any, List
from enhanced_state import AppState, CounterfactualState, SimulatedFacility
from config import Config


class CounterfactualEngine:
    """
    Simulates counterfactual scenarios for healthcare coverage planning.
NORMALIZATION REQUIREMENT:

- Normalize all state references to USPS 2-letter codes.
- Store normalized regions in simulated facility location data.


    """
    
    def __init__(self):
        self.llm = Config.get_llm()
    
    def __call__(self, state: AppState) -> Dict:
        """
        Create counterfactual simulation based on user scenario.
        
        Args:
            state: Current application state
            
        Returns:
            Partial state update with counterfactual state
        """
        print("\n🔮 CounterfactualEngine: Creating simulation...")
        
        user_question = state["messages"][-1].content
        
        # Parse counterfactual scenario from question
        scenario = self._parse_scenario(user_question)
        
        if not scenario:
            print("⚠️  Could not parse counterfactual scenario")
            return {
                "counterfactual_state": None,
                "analytics_executed": state.get("analytics_executed", []) + ["CounterfactualEngine"]
            }
        
        # Create simulated facilities
        simulated_facilities = self._create_simulated_facilities(scenario)
        
        # Compute baseline metrics (before simulation)
        baseline_metrics = self._compute_baseline_metrics(state, scenario)
        
        # Create counterfactual state
        scenario_id = str(uuid.uuid4())[:8]
        counterfactual: CounterfactualState = {
            "scenario_id": scenario_id,
            "description": scenario["description"],
            "simulated_facilities": simulated_facilities,
            "baseline_metrics": baseline_metrics,
            "counterfactual_metrics": {},  # Will be computed after re-running agents
            "delta_metrics": {},
            "is_active": True
        }
        
        print(f"✓ Created simulation: {scenario['description']}")
        print(f"  Simulated facilities: {len(simulated_facilities)}")
        
        return {
            "counterfactual_state": counterfactual,
            "analytics_executed": state.get("analytics_executed", []) + ["CounterfactualEngine"]
        }
    
    def _parse_scenario(self, question: str) -> Dict[str, Any]:
        """Parse counterfactual scenario from user question using LLM."""
        
        prompt = f"""Parse this counterfactual healthcare scenario question and extract key parameters.

Question: {question}

Extract:
1. Scenario type: "add_facilities", "upgrade_facilities", "close_facilities"
2. Number of facilities affected
3. Location/region
4. Medical capabilities to add/modify
5. Equipment to add/modify

Return a JSON object with these fields:
{{
    "type": "add_facilities|upgrade_facilities|close_facilities",
    "count": <number>,
    "region": "<region name>",
    "capabilities": ["capability1", "capability2"],
    "equipment": ["equipment1", "equipment2"],
    "description": "<brief scenario description>"
}}

If question is not a counterfactual scenario, return {{"type": null}}

JSON:"""
        
        try:
            response = self.llm.invoke(prompt)
            content = response.content.strip()
            
            # Clean up JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            import json
            scenario = json.loads(content)
            
            if scenario.get("type"):
                return scenario
            
        except Exception as e:
            print(f"⚠️  Failed to parse scenario: {e}")
        
        return None
    
    def _create_simulated_facilities(self, scenario: Dict[str, Any]) -> List[SimulatedFacility]:
        """Create simulated facilities based on scenario."""
        
        simulated = []
        scenario_type = scenario.get("type")
        count = scenario.get("count", 1)
        region = scenario.get("region", "Unknown")
        capabilities = scenario.get("capabilities", [])
        equipment = scenario.get("equipment", [])
        
        if scenario_type == "add_facilities":
            # Create new facilities
            for i in range(count):
                facility: SimulatedFacility = {
                    "original_id": None,  # New facility
                    "simulation_type": "new_facility",
                    "modified_capabilities": capabilities,
                    "modified_equipment": equipment,
                    "location": {
                        "region": region,
                        "city": f"{region} (simulated location {i+1})",
                        "latitude": 0.0,  # Would need actual coordinates
                        "longitude": 0.0
                    }
                }
                simulated.append(facility)
        
        elif scenario_type == "upgrade_facilities":
            # Upgrade existing facilities (would need to identify specific ones)
            for i in range(count):
                facility: SimulatedFacility = {
                    "original_id": f"UPGRADE_TARGET_{i}",
                    "simulation_type": "upgrade",
                    "modified_capabilities": capabilities,
                    "modified_equipment": equipment,
                    "location": {"region": region}
                }
                simulated.append(facility)
        
        return simulated
    
    def _compute_baseline_metrics(
        self, 
        state: AppState, 
        scenario: Dict[str, Any]
    ) -> Dict[str, float]:
        """Compute baseline metrics before simulation."""
        
        metrics = {}
        
        # Try to extract from existing geo/reachability results
        geo_result = state.get("geo_result")
        if geo_result and geo_result.get("success"):
            if geo_result.get("type") == "proximity":
                metrics["facilities_in_range"] = geo_result.get("count", 0)
        
        reachability_scores = state.get("reachability_scores", {})
        if reachability_scores:
            avg_reachability = sum(
                s["combined_score"] for s in reachability_scores.values()
            ) / len(reachability_scores)
            metrics["average_reachability"] = avg_reachability
        
        # Default metrics
        if not metrics:
            metrics = {
                "facilities_with_capability": 0,
                "average_distance_km": 0,
                "coverage_percentage": 0
            }
        
        return metrics