"""
DataQualityRouter - Routes analytics queries to specialized agents
"""

from typing import Dict, List
from enhanced_state import AppState
from config import Config


class DataQualityRouter:
    """
    Routes analytics queries to appropriate specialized agents.
    """
    
    def __init__(self):
        self.llm = Config.get_llm()
    
    def __call__(self, state: AppState) -> Dict:
        """
        Determine which analytics agents to invoke.
        
        Args:
            state: Current application state
            
        Returns:
            Partial state update with analytics plan
        """
        print("\n🧭 DataQualityRouter: Planning analytics pipeline...")
        
        user_question = state["messages"][-1].content.lower()
        plan = []
        
        # Skill-infrastructure mismatch detection
        mismatch_keywords = [
            "claim", "without", "lack", "missing", "mismatch",
            "infrastructure", "equipment", "capability"
        ]
        if any(kw in user_question for kw in mismatch_keywords):
            plan.append("SkillInfraAgent")
        
        # Reachability scoring
        reachability_keywords = [
            "access", "reachable", "reachability", "coverage",
            "how accessible", "can people reach"
        ]
        if any(kw in user_question for kw in reachability_keywords):
            if "GeoAgent" not in plan:
                plan.append("GeoAgent")
            plan.append("ReachabilityAgent")
        
        # Contradiction analysis
        contradiction_keywords = [
            "contradiction", "inconsistent", "pattern", "systemic",
            "data quality", "widespread", "common issue"
        ]
        if any(kw in user_question for kw in contradiction_keywords):
            if "SkillInfraAgent" not in plan:
                plan.append("SkillInfraAgent")
            plan.append("ContradictionAgent")
        
        # Medical desert classification
        desert_keywords = [
            "desert", "underserved", "gap", "cold spot",
            "no access", "no coverage", "poorest coverage"
        ]
        if any(kw in user_question for kw in desert_keywords):
            if "GeoAgent" not in plan:
                plan.append("GeoAgent")
            if "ReachabilityAgent" not in plan:
                plan.append("ReachabilityAgent")
            plan.append("DesertTypologyAgent")
        
        # If no specific triggers, run basic analytics
        if not plan:
            plan = ["SkillInfraAgent"]
        
        # Remove duplicates while preserving order
        seen = set()
        plan = [x for x in plan if not (x in seen or seen.add(x))]
        
        print(f"✓ Analytics plan: {' → '.join(plan)}")
        
        return {
            "analytics_plan": plan,
            "intermediate_results": {
                **state.get("intermediate_results", {}),
                "analytics_router_decision": " → ".join(plan)
            }
        }