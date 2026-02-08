"""
SkillInfraAgent - Detects skill-infrastructure mismatches
"""

import json
from typing import Dict, Any, List
import pandas as pd
from enhanced_state import AppState, SkillInfraMismatch, AnalyticsResult
from medical_knowledge import MedicalKnowledge
from config import Config


class SkillInfraAgent:
    """
    Detects facilities claiming medical capabilities without required infrastructure.
FACILITY DATA RULES:

- Each facility is uniquely identified by pk_unique_id.
- Facility name is descriptive only and must not be used for grouping or joins.
- Claimed capabilities come from JSON/text fields and are unverified.
- Absence of data does NOT imply absence of capability.
Do not infer infrastructure requirements unless defined in MedicalKnowledge.
- Only flag mismatches when there's a clear medical justification.
- Use severity levels (critical/moderate) based on potential patient impact.

    """
    
    def __init__(self):
        self.llm = Config.get_llm()
        self.knowledge = MedicalKnowledge()
    
    def __call__(self, state: AppState) -> Dict:
        """
        Analyze facilities for skill-infrastructure mismatches.
        
        Args:
            state: Current application state
            
        Returns:
            Partial state update with mismatches found
        """
        print("\n🔍 SkillInfraAgent: Analyzing skill-infrastructure mismatches...")
        
        # Get facility data from SQL result or trigger SQL query
        facilities_df = self._get_facilities_data(state)
        
        if facilities_df is None or len(facilities_df) == 0:
            print("⚠️  No facility data available for analysis")
            return {
                "skill_infra_mismatches": [],
                "analytics_results": {
                    **state.get("analytics_results", {}),
                    "skill_infra": {
                        "agent": "SkillInfraAgent",
                        "total_facilities_analyzed": 0,
                        "summary": "No facility data available",
                        "metadata": {}
                    }
                },
                "analytics_executed": state.get("analytics_executed", []) + ["SkillInfraAgent"]
            }
        
        # Analyze each facility for mismatches
        mismatches = []
        verification_needed = []
        
        for idx, row in facilities_df.iterrows():
            facility_mismatches = self._analyze_facility(row)
            mismatches.extend(facility_mismatches)
            
            # Flag critical mismatches for external verification
            for mismatch in facility_mismatches:
                if mismatch["severity"] == "critical":
                    verification_needed.append({
                        "id": f"verify_{mismatch['facility_id']}",
                        "procedure": mismatch["claimed_capability"],
                        "missing_infra": mismatch["missing_infrastructure"],
                        "uncertainty": "high"
                    })
        
        # Generate summary
        critical_count = sum(1 for m in mismatches if m["severity"] == "critical")
        moderate_count = sum(1 for m in mismatches if m["severity"] == "moderate")
        
        summary = f"Found {len(mismatches)} mismatches ({critical_count} critical, {moderate_count} moderate) across {len(facilities_df)} facilities"
        
        print(f"✓ Analysis complete: {summary}")
        
        # Update citations
        citations = state.get("citations", []).copy()
        if mismatches:
            citations.append({
                "agent": "SkillInfraAgent",
                "facilities_analyzed": len(facilities_df),
                "mismatches_found": len(mismatches),
                "critical_mismatches": critical_count
            })
        
        return {
            "skill_infra_mismatches": mismatches,
            "verification_needed": state.get("verification_needed", []) + verification_needed,
            "analytics_results": {
                **state.get("analytics_results", {}),
                "skill_infra": {
                    "agent": "SkillInfraAgent",
                    "total_facilities_analyzed": len(facilities_df),
                    "mismatches_found": len(mismatches),
                    "critical_mismatches": critical_count,
                    "moderate_mismatches": moderate_count,
                    "summary": summary,
                    "metadata": {
                        "facilities_with_issues": len(set(m["facility_id"] for m in mismatches))
                    }
                }
            },
            "citations": citations,
            "analytics_executed": state.get("analytics_executed", []) + ["SkillInfraAgent"]
        }
    
    def _get_facilities_data(self, state: AppState) -> pd.DataFrame:
        """Extract facilities data from state."""
        # Try to get from SQL result
        if state.get("sql_result") and state["sql_result"].get("success"):
            return state["sql_result"]["data"]
        
        # Otherwise, load from CSV directly
        try:
            import os
            csv_path = Config.HOSPITALS_CSV
            if not os.path.exists(csv_path):
                # Try uploads directory
                csv_path = f"/mnt/user-data/uploads/{os.path.basename(csv_path)}"
            
            if os.path.exists(csv_path):
                return pd.read_csv(csv_path)
        except Exception as e:
            print(f"⚠️  Could not load facility data: {e}")
        
        return None
    
    def _analyze_facility(self, row: pd.Series) -> List[SkillInfraMismatch]:
        """
        Analyze a single facility for skill-infrastructure mismatches.
        
        Args:
            row: Facility data row
            
        Returns:
            List of detected mismatches
        """
        mismatches = []
        
        # Extract facility info
        facility_id = str(row.get("unique_id", "unknown"))
        facility_name = str(row.get("name", "Unknown Facility"))
        city = str(row.get("address_city", ""))
        region = str(row.get("address_stateOrRegion", ""))
        
        # Extract claimed capabilities
        claimed_capabilities = self._extract_capabilities(row)
        
        # Extract available equipment
        available_equipment = self._extract_equipment(row)
        
        # Validate each claimed capability
        for capability in claimed_capabilities:
            validation = self.knowledge.validate_equipment(capability, available_equipment)
            
            # Only flag if validation failed or found missing critical equipment
            if validation["valid"] is False or validation["missing_critical"]:
                mismatch: SkillInfraMismatch = {
                    "facility_id": facility_id,
                    "facility_name": facility_name,
                    "claimed_capability": capability,
                    "missing_infrastructure": (
                        validation["missing_critical"] + 
                        validation["missing_required"]
                    ),
                    "severity": validation["severity"],
                    "medical_justification": validation["justification"],
                    "location": {
                        "city": city,
                        "region": region
                    }
                }
                mismatches.append(mismatch)
        
        return mismatches
    
    def _extract_capabilities(self, row: pd.Series) -> List[str]:
        """Extract claimed medical capabilities from facility row."""
        capabilities = []
        
        # From specialties field
        if pd.notna(row.get("specialties")):
            specialties = self._parse_json_field(row["specialties"])
            capabilities.extend(specialties)
        
        # From procedure field
        if pd.notna(row.get("procedure")):
            procedures = self._parse_json_field(row["procedure"])
            capabilities.extend(procedures)
        
        # From capability field
        if pd.notna(row.get("capability")):
            caps = self._parse_json_field(row["capability"])
            capabilities.extend(caps)
        
        return list(set(capabilities))  # Remove duplicates
    
    def _extract_equipment(self, row: pd.Series) -> List[str]:
        """Extract available equipment from facility row."""
        equipment = []
        
        if pd.notna(row.get("equipment")):
            equipment = self._parse_json_field(row["equipment"])
        
        return equipment
    
    def _parse_json_field(self, field_value: Any) -> List[str]:
        """Parse JSON field value into list of strings."""
        if isinstance(field_value, list):
            return [str(item) for item in field_value if item]
        
        if isinstance(field_value, str):
            try:
                data = json.loads(field_value)
                if isinstance(data, list):
                    return [str(item) for item in data if item]
            except:
                pass
        
        return []
