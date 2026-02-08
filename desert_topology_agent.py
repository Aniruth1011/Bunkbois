"""
DesertTypologyAgent - Classifies medical deserts by type
Identifies geographic, capability, and skill deserts
"""

from typing import Dict, Any, List
from collections import defaultdict
from enhanced_state import AppState, DesertClassification, AnalyticsResult
from config import Config


class DesertTypologyAgent:
    """
    Classifies medical deserts into types:
    - Geographic: No facilities within reasonable distance
    - Capability: Facilities exist but lack key services
    - Skill: Facilities claim services but lack verified infrastructure

    DESERT CLASSIFICATION RULES:

- Regions are identified using USPS state codes or explicit city names.
- Do not mix full state names and USPS codes.
- A “region” must be internally consistent in format.

    """
    
    def __init__(self):
        self.llm = Config.get_llm()
    
    def __call__(self, state: AppState) -> Dict:
        """
        Classify medical deserts by type.
        
        Args:
            state: Current application state
            
        Returns:
            Partial state update with desert classifications
        """
        print("\n🏜️  DesertTypologyAgent: Classifying medical deserts...")
        
        # Get required data
        geo_result = state.get("geo_result")
        reachability_scores = state.get("reachability_scores", {})
        skill_mismatches = state.get("skill_infra_mismatches", [])
        
        if not geo_result and not reachability_scores:
            print("⚠️  No geographic or reachability data available")
            return {
                "desert_typology": {},
                "analytics_results": {
                    **state.get("analytics_results", {}),
                    "desert_typology": {
                        "agent": "DesertTypologyAgent",
                        "summary": "Insufficient data for desert classification",
                        "metadata": {}
                    }
                },
                "analytics_executed": state.get("analytics_executed", []) + ["DesertTypologyAgent"]
            }
        
        # Classify deserts
        classifications = self._classify_deserts(
            geo_result, reachability_scores, skill_mismatches, state
        )
        
        # Generate summary
        severe_count = sum(1 for c in classifications.values() if c["severity"] == "severe")
        total_affected = sum(c.get("affected_population_estimate", 0) for c in classifications.values())
        
        summary = (
            f"Classified {len(classifications)} desert regions. "
            f"{severe_count} severe deserts affecting ~{total_affected:,} people."
        )
        
        print(f"✓ Desert classification complete: {summary}")
        
        # Update citations
        citations = state.get("citations", []).copy()
        if classifications:
            citations.append({
                "agent": "DesertTypologyAgent",
                "deserts_classified": len(classifications),
                "severe_deserts": severe_count
            })
        
        return {
            "desert_typology": classifications,
            "analytics_results": {
                **state.get("analytics_results", {}),
                "desert_typology": {
                    "agent": "DesertTypologyAgent",
                    "total_deserts": len(classifications),
                    "severe_deserts": severe_count,
                    "total_affected_population": total_affected,
                    "summary": summary,
                    "metadata": {}
                }
            },
            "citations": citations,
            "analytics_executed": state.get("analytics_executed", []) + ["DesertTypologyAgent"]
        }
    
    def _classify_deserts(
        self,
        geo_result: Dict[str, Any],
        reachability_scores: Dict[str, Any],
        skill_mismatches: List[Dict[str, Any]],
        state: AppState
    ) -> Dict[str, DesertClassification]:
        """Classify medical deserts by analyzing multiple data sources."""
        
        classifications = {}
        
        # Extract target capability from user question
        user_question = state["messages"][-1].content.lower()
        target_capability = self._extract_capability(user_question)
        
        # Analyze reachability scores
        for key, score in reachability_scores.items():
            if score["combined_score"] < 50:  # Low reachability threshold
                region = score["location"]
                
                classification = self._classify_region(
                    region=region,
                    capability=target_capability,
                    reachability_score=score,
                    geo_result=geo_result,
                    skill_mismatches=skill_mismatches
                )
                
                classifications[f"{region}_{target_capability}"] = classification
        
        # Analyze geographic cold spots
        if geo_result and geo_result.get("type") == "cold_spots":
            cold_spots = geo_result.get("cold_spots", [])
            for spot in cold_spots:
                region = spot.get("region", "Unknown")
                
                # Create classification for geographic desert
                classification: DesertClassification = {
                    "region": region,
                    "desert_types": ["geographic"],
                    "severity": "severe",
                    "affected_population_estimate": self._estimate_population(region),
                    "primary_gaps": [
                        f"No {target_capability} facilities within 50km",
                        "Limited transportation infrastructure"
                    ],
                    "recommended_interventions": [
                        f"Establish {target_capability} center in regional capital",
                        "Mobile health units for rural areas",
                        "Telemedicine infrastructure"
                    ]
                }
                
                classifications[f"{region}_{target_capability}"] = classification
        
        return classifications
    
    def _classify_region(
        self,
        region: str,
        capability: str,
        reachability_score: Dict[str, Any],
        geo_result: Dict[str, Any],
        skill_mismatches: List[Dict[str, Any]]
    ) -> DesertClassification:
        """Classify a specific region as a medical desert."""
        
        desert_types = []
        primary_gaps = []
        
        # Analyze geographic access
        geo_score = reachability_score.get("geographic_score", 0)
        if geo_score < 30:  # Poor geographic access
            desert_types.append("geographic")
            distance = reachability_score.get("distance_km")
            if distance:
                primary_gaps.append(f"Nearest facility {distance:.1f}km away")
        
        # Analyze capability availability
        capability_score = reachability_score.get("capability_score", 0)
        if capability_score < 50:  # Poor capability coverage
            desert_types.append("capability")
            if capability_score == 0:
                primary_gaps.append(f"No facilities offering {capability}")
            else:
                primary_gaps.append(f"Limited {capability} facilities available")
        
        # Analyze skill/infrastructure quality
        infrastructure_gaps = reachability_score.get("infrastructure_gaps", [])
        if infrastructure_gaps:
            desert_types.append("skill")
            primary_gaps.extend(infrastructure_gaps[:2])  # Top 2 gaps
        
        # Determine severity
        severity = self._determine_severity(
            desert_types,
            reachability_score["combined_score"]
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            region, capability, desert_types
        )
        
        # Estimate affected population
        affected_population = self._estimate_population(region)
        
        classification: DesertClassification = {
            "region": region,
            "desert_types": desert_types if desert_types else ["capability"],
            "severity": severity,
            "affected_population_estimate": affected_population,
            "primary_gaps": primary_gaps,
            "recommended_interventions": recommendations
        }
        
        return classification
    
    def _determine_severity(
        self,
        desert_types: List[str],
        combined_score: float
    ) -> str:
        """Determine severity of medical desert."""
        
        # Calculate severity score
        severity_score = len(desert_types) * 20  # More types = worse
        severity_score += (100 - combined_score)  # Lower reachability = worse
        
        if severity_score > 70:
            return "severe"
        elif severity_score > 40:
            return "moderate"
        else:
            return "mild"
    
    def _generate_recommendations(
        self,
        region: str,
        capability: str,
        desert_types: List[str]
    ) -> List[str]:
        """Generate intervention recommendations based on desert types."""
        
        recommendations = []
        
        if "geographic" in desert_types:
            recommendations.extend([
                f"Establish {capability} center in {region}",
                "Improve transportation infrastructure",
                "Mobile health services for remote areas"
            ])
        
        if "capability" in desert_types:
            recommendations.extend([
                f"Upgrade existing facilities to offer {capability}",
                "Train local healthcare workers",
                "Equipment procurement program"
            ])
        
        if "skill" in desert_types:
            recommendations.extend([
                "Infrastructure quality assurance program",
                "Equipment maintenance training",
                "Medical licensing verification"
            ])
        
        # Add general recommendations
        recommendations.append("Telemedicine consultation services")
        
        return recommendations[:5]  # Return top 5
    
    def _estimate_population(self, region: str) -> int:
        """Estimate affected population for a region."""
        
        population_estimates = {
            "Greater major cities": 4000000,
            "Texas": 4800000,
            "Eastern": 2600000,
            "Central": 2200000,
            "Western": 2400000,
            "Northern": 2500000,
            "Upper East": 1050000,
            "Upper West": 700000,
            "Volta": 2100000,
            "Brong Ahafo": 2300000
        }
        
        # Try to match region name
        for known_region, population in population_estimates.items():
            if known_region.lower() in region.lower() or region.lower() in known_region.lower():
                return population
        
        # Default estimate for unknown regions
        return 500000
    
    def _extract_capability(self, question: str) -> str:
        """Extract target capability from user question."""
        capabilities = [
            "dialysis", "cardiology", "neurosurgery", "ophthalmology",
            "surgery", "maternity", "ICU", "emergency"
        ]
        
        for capability in capabilities:
            if capability in question:
                return capability
        
        return "healthcare services"