"""
Enhanced State definitions for the VF Agent multi-agent system.
Includes all new analytics capabilities.
"""

from typing import  List, Dict, Any, Optional
from typing_extensions import TypedDict

from langchain_core.messages import BaseMessage


# ==================== ANALYTICS DATA STRUCTURES ====================

class AnalyticsResult(TypedDict, total=False):
    """Generic analytics result structure."""
    agent: str
    total_facilities_analyzed: int
    summary: str
    metadata: Dict[str, Any]


class SkillInfraMismatch(TypedDict, total=False):
    """Detected skill-infrastructure mismatch."""
    facility_id: str
    facility_name: str
    claimed_capability: str
    missing_infrastructure: List[str]
    severity: str  # "critical" | "moderate" | "minor"
    medical_justification: str
    location: Dict[str, str]


class ReachabilityScore(TypedDict, total=False):
    """Medical reachability score for a location."""
    location: str
    target_capability: str
    geographic_score: float  # 0-100
    capability_score: float  # 0-100
    combined_score: float  # Weighted composite
    nearest_verified_facility: Optional[str]
    distance_km: Optional[float]
    infrastructure_gaps: List[str]


class ContradictionNode(TypedDict, total=False):
    """Node in contradiction graph."""
    facility_id: str
    contradiction_type: str
    severity: str


class ContradictionEdge(TypedDict, total=False):
    """Edge in contradiction graph."""
    source_facility: str
    target_facility: str
    shared_contradiction: str
    edge_weight: float


class ContradictionCluster(TypedDict, total=False):
    """Cluster of facilities with shared contradictions."""
    cluster_id: str
    pattern: str
    facility_ids: List[str]
    is_systemic: bool


class ContradictionGraph(TypedDict, total=False):
    """Complete contradiction graph."""
    nodes: List[ContradictionNode]
    edges: List[ContradictionEdge]
    clusters: List[ContradictionCluster]
    systemic_patterns: List[str]


class SimulatedFacility(TypedDict, total=False):
    """Simulated facility for counterfactual analysis."""
    original_id: Optional[str]
    simulation_type: str  # "upgrade" | "new_facility" | "closure"
    modified_capabilities: List[str]
    modified_equipment: List[str]
    location: Dict[str, Any]


class CounterfactualState(TypedDict, total=False):
    """State for counterfactual simulation."""
    scenario_id: str
    description: str
    simulated_facilities: List[SimulatedFacility]
    baseline_metrics: Dict[str, float]
    counterfactual_metrics: Dict[str, float]
    delta_metrics: Dict[str, float]
    is_active: bool


class DesertClassification(TypedDict, total=False):
    """Medical desert classification."""
    region: str
    desert_types: List[str]  # ["geographic", "capability", "skill"]
    severity: str  # "severe" | "moderate" | "mild"
    affected_population_estimate: int
    primary_gaps: List[str]
    recommended_interventions: List[str]


# ==================== MAIN APPLICATION STATE ====================

class AppState(TypedDict, total=False):
    """
    Enhanced state object passed between all agents in the graph.
    """
    
    # ========== EXISTING FIELDS (Core conversation) ==========
    messages: List[BaseMessage]
    intent: str
    plan: Optional[List[str]]
    
    # ========== EXISTING FIELDS (Agent results) ==========
    sql_result: Optional[Dict[str, Any]]
    vector_result: Optional[Dict[str, Any]]
    geo_result: Optional[Dict[str, Any]]
    medical_reasoning: Optional[Dict[str, Any]]
    
    # ========== EXISTING FIELDS (Metadata) ==========
    intermediate_results: Dict[str, Any]
    final_response: Optional[str]
    errors: List[str]
    citations: List[Dict[str, Any]]
    
    # ========== NEW FIELDS (Analytics pipeline) ==========
    analytics_plan: Optional[List[str]]  # Which analytics agents to run
    analytics_results: Dict[str, AnalyticsResult]  # Results keyed by agent name
    analytics_executed: List[str]  # Track which agents have run
    
    # ========== NEW FIELDS (Capability-specific results) ==========
    skill_infra_mismatches: List[SkillInfraMismatch]
    reachability_scores: Dict[str, ReachabilityScore]
    contradiction_graph: Optional[ContradictionGraph]
    counterfactual_state: Optional[CounterfactualState]
    desert_typology: Dict[str, DesertClassification]
    
    # ========== NEW FIELDS (External verification) ==========
    external_search_results: Dict[str, Any]  # Google SERP, Reddit, Tavily
    verification_needed: List[Dict[str, Any]]  # Claims requiring verification
