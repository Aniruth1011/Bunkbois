"""
ReachabilityAgent - Computes medical reachability scores
Combines geographic access with capability verification
"""

import math
from typing import Dict, Any, List
from enhanced_state import AppState, ReachabilityScore, AnalyticsResult
from config import Config


class ReachabilityAgent:
    """
    Computes medical reachability scores combining:
    - Geographic accessibility (distance to facilities)
    - Capability verification (infrastructure quality)
    REACHABILITY DATA CONTRACT:

    - Locations are keyed by USPS state codes, not full names.
    - All regional reachability scores must reference USPS codes.
    - Geographic distance is computed from normalized locations only.
    - Capability verification checks for critical infrastructure gaps.
    - Scores are on a 0-100 scale, with metadata on nearest verified facility.
    - Output includes detailed analytics results for transparency.
    SCORING GUIDELINES:
    - Geographic Score:
        - 100 at 0km, decaying exponentially with distance (e.g. ~
            37 at 30km, ~14 at 60km)
    - Capability Score:
        - 100 if verified facilities with no critical mismatches
        - 30 if facilities claim capability but have critical mismatches
        - 0 if no facilities with claimed capability
    - Combined Score:
        - Weighted average (default: 50% geographic, 50% capability)
    - Critical mismatches include missing ICU for neurosurgery, lack of emergency services for trauma, etc.
    - Infrastructure gaps are tracked and reported for facilities with critical mismatches.
    
    """
    
    def __init__(self):
        self.llm = Config.get_llm()
        self.geo_weight = Config.REACHABILITY_WEIGHT_GEOGRAPHIC
        self.capability_weight = Config.REACHABILITY_WEIGHT_CAPABILITY
    
    def __call__(self, state: AppState) -> Dict:
        """
        Compute reachability scores for locations/capabilities.
        
        Args:
            state: Current application state
            
        Returns:
            Partial state update with reachability scores
        """
        print("\n📊 ReachabilityAgent: Computing medical reachability scores...")
        
        # Check if we have required data
        geo_result = state.get("geo_result")
        skill_mismatches = state.get("skill_infra_mismatches", [])
        
        if not geo_result or not geo_result.get("success"):
            print("⚠️  No geographic data available for reachability analysis")
            return {
                "reachability_scores": {},
                "analytics_results": {
                    **state.get("analytics_results", {}),
                    "reachability": {
                        "agent": "ReachabilityAgent",
                        "summary": "No geographic data available",
                        "metadata": {}
                    }
                },
                "analytics_executed": state.get("analytics_executed", []) + ["ReachabilityAgent"]
            }
        
        # Compute reachability scores
        scores = self._compute_scores(geo_result, skill_mismatches, state)
        
        # Generate summary
        avg_score = sum(s["combined_score"] for s in scores.values()) / len(scores) if scores else 0
        low_reachability = sum(1 for s in scores.values() if s["combined_score"] < 50)
        
        summary = f"Computed reachability for {len(scores)} locations. Average score: {avg_score:.1f}/100. {low_reachability} locations with low reachability (<50)."
        
        print(f"✓ Reachability analysis complete: {summary}")
        
        # Update citations
        citations = state.get("citations", []).copy()
        if scores:
            citations.append({
                "agent": "ReachabilityAgent",
                "locations_analyzed": len(scores),
                "average_score": round(avg_score, 1)
            })
        
        return {
            "reachability_scores": scores,
            "analytics_results": {
                **state.get("analytics_results", {}),
                "reachability": {
                    "agent": "ReachabilityAgent",
                    "total_locations_analyzed": len(scores),
                    "average_reachability_score": round(avg_score, 1),
                    "low_reachability_count": low_reachability,
                    "summary": summary,
                    "metadata": {
                        "geo_weight": self.geo_weight,
                        "capability_weight": self.capability_weight
                    }
                }
            },
            "citations": citations,
            "analytics_executed": state.get("analytics_executed", []) + ["ReachabilityAgent"]
        }
    
    def _compute_scores(
        self, 
        geo_result: Dict[str, Any], 
        skill_mismatches: List[Dict[str, Any]],
        state: AppState
    ) -> Dict[str, ReachabilityScore]:
        """Compute reachability scores for all locations."""
        scores = {}
        
        # Extract target capability from user question
        user_question = state["messages"][-1].content.lower()
        target_capability = self._extract_target_capability(user_question)
        
        # Handle proximity-based geo results
        if geo_result.get("type") == "proximity":
            location_name = geo_result.get("center", "Unknown")
            facilities = geo_result.get("facilities", [])
            
            if facilities:
                score = self._compute_location_score(
                    location=location_name,
                    facilities=facilities,
                    target_capability=target_capability,
                    skill_mismatches=skill_mismatches
                )
                scores[f"{location_name}_{target_capability}"] = score
        
        # Handle cold spots analysis
        elif geo_result.get("type") == "cold_spots":
            cold_spots = geo_result.get("cold_spots", [])
            for spot in cold_spots:
                location_name = spot.get("region", "Unknown")
                score: ReachabilityScore = {
                    "location": location_name,
                    "target_capability": target_capability,
                    "geographic_score": 0.0,  # Cold spot = no access
                    "capability_score": 0.0,
                    "combined_score": 0.0,
                    "nearest_verified_facility": None,
                    "distance_km": None,
                    "infrastructure_gaps": ["No facilities within reasonable distance"]
                }
                scores[f"{location_name}_{target_capability}"] = score
        
        # Handle general facility results
        else:
            # Group facilities by region and compute regional scores
            facilities = geo_result.get("facilities", [])
            if facilities:
                regions = set(f.get("region", "Unknown") for f in facilities)
                for region in regions:
                    region_facilities = [f for f in facilities if f.get("region") == region]
                    score = self._compute_location_score(
                        location=region,
                        facilities=region_facilities,
                        target_capability=target_capability,
                        skill_mismatches=skill_mismatches
                    )
                    scores[f"{region}_{target_capability}"] = score
        
        return scores
    
    def _compute_location_score(
        self,
        location: str,
        facilities: List[Dict[str, Any]],
        target_capability: str,
        skill_mismatches: List[Dict[str, Any]]
    ) -> ReachabilityScore:
        """Compute reachability score for a specific location."""
        
        # Geographic score: based on distance to nearest facility
        nearest_distance = min(
            (f.get("distance_km", float('inf')) for f in facilities),
            default=float('inf')
        )
        
        if nearest_distance == float('inf'):
            geographic_score = 0.0
        else:
            # Exponential decay: 100 at 0km, ~37 at 30km, ~14 at 60km
            geographic_score = 100 * math.exp(-nearest_distance / 30)
        
        # Capability score: based on verified infrastructure
        nearest_verified = None
        capability_score = 0.0
        infrastructure_gaps = []
        
        if facilities:
            # Find facilities with target capability
            capable_facilities = [
                f for f in facilities 
                if self._has_capability(f, target_capability)
            ]
            
            if capable_facilities:
                # Check infrastructure quality
                verified_facilities = []
                for facility in capable_facilities:
                    facility_id = facility.get("unique_id") or facility.get("id")
                    
                    # Check if this facility has critical mismatches
                    facility_mismatches = [
                        m for m in skill_mismatches 
                        if m["facility_id"] == str(facility_id) and m["severity"] == "critical"
                    ]
                    
                    if not facility_mismatches:
                        verified_facilities.append(facility)
                    else:
                        # Track infrastructure gaps
                        for mismatch in facility_mismatches:
                            infrastructure_gaps.extend(mismatch["missing_infrastructure"])
                
                # Calculate capability score
                if verified_facilities:
                    capability_score = 100.0
                    nearest_verified = verified_facilities[0].get("name", "Unknown")
                else:
                    # Facilities claim capability but lack infrastructure
                    capability_score = 30.0  # Partial score
                    infrastructure_gaps = list(set(infrastructure_gaps))
            else:
                capability_score = 0.0
                infrastructure_gaps = [f"No facilities with {target_capability} found"]
        
        # Combined score (weighted average)
        combined_score = (
            self.geo_weight * geographic_score +
            self.capability_weight * capability_score
        )
        
        score: ReachabilityScore = {
            "location": location,
            "target_capability": target_capability,
            "geographic_score": round(geographic_score, 1),
            "capability_score": round(capability_score, 1),
            "combined_score": round(combined_score, 1),
            "nearest_verified_facility": nearest_verified,
            "distance_km": round(nearest_distance, 1) if nearest_distance != float('inf') else None,
            "infrastructure_gaps": infrastructure_gaps[:5]  # Limit to top 5
        }
        
        return score
    
    def _extract_target_capability(self, question: str) -> str:
        """Extract target medical capability from user question."""
        # Common medical keywords
        capabilities = [
            "dialysis", "cardiology", "neurosurgery", "ophthalmology",
            "surgery", "maternity", "ICU", "emergency", "radiology",
            "laboratory", "pharmacy", "dental"
        ]
        
        question_lower = question.lower()
        for capability in capabilities:
            if capability in question_lower:
                return capability
        
        return "general medical services"
    
    def _has_capability(self, facility: Dict[str, Any], capability: str) -> bool:
        """Check if facility has claimed capability."""
        # Check in various fields
        fields_to_check = [
            facility.get("specialties", ""),
            facility.get("procedure", ""),
            facility.get("capability", ""),
            facility.get("services", "")
        ]
        
        capability_lower = capability.lower()
        for field in fields_to_check:
            if isinstance(field, str) and capability_lower in field.lower():
                return True
        
        return False
