"""
ContradictionAgent - Builds logical contradiction graph
Identifies systemic vs isolated data quality issues
"""

from typing import Dict, Any, List, Set
from collections import defaultdict
from enhanced_state import (
    AppState, ContradictionGraph, ContradictionNode, 
    ContradictionEdge, ContradictionCluster, AnalyticsResult
)
from config import Config


class ContradictionAgent:
    """
    Builds contradiction graph to detect systemic data quality patterns.
CONTRADICTION GRAPH RULES:

- Nodes are grouped by facility_id (pk_unique_id), not name.
- Geographic similarity does NOT imply contradiction.
- Shared contradiction types must match exactly.
- State or city differences do not affect contradiction linkage.

- Severity levels (critical/moderate) are based on potential patient impact, not just missing infrastructure.
- Clusters are defined by shared contradiction types, not geographic proximity.
- Systemic patterns require both cluster size and regional concentration criteria.
- Avoid overgeneralizing patterns from small clusters.
    """
    
    def __init__(self):
        self.llm = Config.get_llm()
        self.cluster_threshold = Config.CONTRADICTION_CLUSTER_THRESHOLD
    
    def __call__(self, state: AppState) -> Dict:
        """
        Build contradiction graph from skill-infrastructure mismatches.
        
        Args:
            state: Current application state
            
        Returns:
            Partial state update with contradiction graph
        """
        print("\n🕸️  ContradictionAgent: Building contradiction graph...")
        
        # Get skill-infrastructure mismatches
        mismatches = state.get("skill_infra_mismatches", [])
        
        if not mismatches:
            print("⚠️  No mismatches available for contradiction analysis")
            return {
                "contradiction_graph": None,
                "analytics_results": {
                    **state.get("analytics_results", {}),
                    "contradictions": {
                        "agent": "ContradictionAgent",
                        "summary": "No mismatches to analyze",
                        "metadata": {}
                    }
                },
                "analytics_executed": state.get("analytics_executed", []) + ["ContradictionAgent"]
            }
        
        # Build graph
        graph = self._build_graph(mismatches)
        
        # Generate summary
        systemic_count = sum(1 for c in graph["clusters"] if c["is_systemic"])
        isolated_count = len(graph["clusters"]) - systemic_count
        
        summary = (
            f"Built contradiction graph: {len(graph['nodes'])} nodes, "
            f"{len(graph['edges'])} edges, {len(graph['clusters'])} clusters "
            f"({systemic_count} systemic, {isolated_count} isolated)"
        )
        
        print(f"✓ Graph analysis complete: {summary}")
        
        # Update citations
        citations = state.get("citations", []).copy()
        citations.append({
            "agent": "ContradictionAgent",
            "nodes_analyzed": len(graph["nodes"]),
            "systemic_patterns": systemic_count
        })
        
        return {
            "contradiction_graph": graph,
            "analytics_results": {
                **state.get("analytics_results", {}),
                "contradictions": {
                    "agent": "ContradictionAgent",
                    "total_contradictions": len(graph["nodes"]),
                    "systemic_clusters": systemic_count,
                    "isolated_clusters": isolated_count,
                    "summary": summary,
                    "metadata": {
                        "cluster_threshold": self.cluster_threshold
                    }
                }
            },
            "citations": citations,
            "analytics_executed": state.get("analytics_executed", []) + ["ContradictionAgent"]
        }
    
    def _build_graph(self, mismatches: List[Dict[str, Any]]) -> ContradictionGraph:
        """Build complete contradiction graph."""
        
        # Create nodes (one per facility-mismatch pair)
        nodes: List[ContradictionNode] = []
        for mismatch in mismatches:
            # Create contradiction type identifier
            contradiction_type = self._get_contradiction_type(mismatch)
            
            node: ContradictionNode = {
                "facility_id": mismatch["facility_id"],
                "contradiction_type": contradiction_type,
                "severity": mismatch["severity"]
            }
            nodes.append(node)
        
        # Create edges (connect facilities with shared contradiction types)
        edges: List[ContradictionEdge] = []
        for i, node1 in enumerate(nodes):
            for node2 in nodes[i+1:]:
                if self._should_connect(node1, node2):
                    edge: ContradictionEdge = {
                        "source_facility": node1["facility_id"],
                        "target_facility": node2["facility_id"],
                        "shared_contradiction": node1["contradiction_type"],
                        "edge_weight": self._compute_edge_weight(node1, node2)
                    }
                    edges.append(edge)
        
        # Find clusters using connected components
        clusters = self._find_clusters(nodes, edges, mismatches)
        
        # Identify systemic patterns
        systemic_patterns = self._identify_systemic_patterns(clusters, mismatches)
        
        graph: ContradictionGraph = {
            "nodes": nodes,
            "edges": edges,
            "clusters": clusters,
            "systemic_patterns": systemic_patterns
        }
        
        return graph
    
    def _get_contradiction_type(self, mismatch: Dict[str, Any]) -> str:
        """Generate contradiction type identifier."""
        capability = mismatch["claimed_capability"]
        # Use first missing critical infrastructure as key differentiator
        missing = mismatch["missing_infrastructure"]
        if missing:
            return f"{capability}_without_{missing[0].replace(' ', '_')}"
        return f"{capability}_infrastructure_gap"
    
    def _should_connect(self, node1: ContradictionNode, node2: ContradictionNode) -> bool:
        """Determine if two nodes should be connected."""
        # Connect if they share the same contradiction type
        return node1["contradiction_type"] == node2["contradiction_type"]
    
    def _compute_edge_weight(self, node1: ContradictionNode, node2: ContradictionNode) -> float:
        """Compute edge weight based on similarity."""
        # Weight based on severity match
        weight = 0.5
        
        if node1["severity"] == node2["severity"]:
            weight += 0.5
        
        return weight
    
    def _find_clusters(
        self, 
        nodes: List[ContradictionNode], 
        edges: List[ContradictionEdge],
        mismatches: List[Dict[str, Any]]
    ) -> List[ContradictionCluster]:
        """Find connected components (clusters) in the graph."""
        
        # Build adjacency list
        adjacency: Dict[str, Set[str]] = defaultdict(set)
        for edge in edges:
            adjacency[edge["source_facility"]].add(edge["target_facility"])
            adjacency[edge["target_facility"]].add(edge["source_facility"])
        
        # Find connected components using DFS
        visited: Set[str] = set()
        clusters: List[ContradictionCluster] = []
        
        for node in nodes:
            facility_id = node["facility_id"]
            
            if facility_id not in visited:
                # Start new cluster
                cluster_facilities = self._dfs(facility_id, adjacency, visited)
                
                if cluster_facilities:
                    # Get pattern description
                    pattern = self._describe_cluster_pattern(
                        cluster_facilities, nodes, mismatches
                    )
                    
                    # Determine if systemic
                    is_systemic = self._is_systemic_cluster(
                        cluster_facilities, mismatches
                    )
                    
                    cluster: ContradictionCluster = {
                        "cluster_id": f"CLUSTER_{len(clusters) + 1}",
                        "pattern": pattern,
                        "facility_ids": list(cluster_facilities),
                        "is_systemic": is_systemic
                    }
                    clusters.append(cluster)
        
        return clusters
    
    def _dfs(
        self, 
        start: str, 
        adjacency: Dict[str, Set[str]], 
        visited: Set[str]
    ) -> List[str]:
        """Depth-first search to find connected component."""
        stack = [start]
        component = []
        
        while stack:
            node = stack.pop()
            if node not in visited:
                visited.add(node)
                component.append(node)
                stack.extend(adjacency[node] - visited)
        
        return component
    
    def _describe_cluster_pattern(
        self,
        cluster_facilities: List[str],
        nodes: List[ContradictionNode],
        mismatches: List[Dict[str, Any]]
    ) -> str:
        """Generate human-readable description of cluster pattern."""
        
        # Get nodes in this cluster
        cluster_nodes = [n for n in nodes if n["facility_id"] in cluster_facilities]
        
        if not cluster_nodes:
            return "Unknown pattern"
        
        # Get common contradiction type
        contradiction_type = cluster_nodes[0]["contradiction_type"]
        
        # Get regions
        regions = set()
        for facility_id in cluster_facilities:
            for mismatch in mismatches:
                if mismatch["facility_id"] == facility_id:
                    region = mismatch["location"].get("region", "Unknown")
                    regions.add(region)
        
        # Generate description
        region_str = ", ".join(sorted(regions)) if regions else "multiple regions"
        
        # Decode contradiction type
        capability = contradiction_type.split("_without_")[0].replace("_", " ")
        
        pattern = (
            f"{len(cluster_facilities)} facilities in {region_str} "
            f"claim {capability} with infrastructure gaps"
        )
        
        return pattern
    
    def _is_systemic_cluster(
        self, 
        cluster_facilities: List[str],
        mismatches: List[Dict[str, Any]]
    ) -> bool:
        """Determine if cluster represents systemic issue."""
        
        # Systemic if cluster size exceeds threshold
        if len(cluster_facilities) >= self.cluster_threshold:
            return True
        
        # Or if cluster represents >50% of facilities in a region
        regions_count: Dict[str, int] = defaultdict(int)
        region_totals: Dict[str, Set[str]] = defaultdict(set)
        
        for mismatch in mismatches:
            region = mismatch["location"].get("region", "Unknown")
            facility_id = mismatch["facility_id"]
            
            region_totals[region].add(facility_id)
            
            if facility_id in cluster_facilities:
                regions_count[region] += 1
        
        # Check if any region has >50% of facilities in this cluster
        for region, count in regions_count.items():
            total = len(region_totals[region])
            if total > 0 and count / total > 0.5:
                return True
        
        return False
    
    def _identify_systemic_patterns(
        self,
        clusters: List[ContradictionCluster],
        mismatches: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate list of systemic pattern descriptions."""
        patterns = []
        
        for cluster in clusters:
            if cluster["is_systemic"]:
                # Get regions in this cluster
                regions = set()
                for facility_id in cluster["facility_ids"]:
                    for mismatch in mismatches:
                        if mismatch["facility_id"] == facility_id:
                            region = mismatch["location"].get("region", "Unknown")
                            regions.add(region)
                
                region_str = ", ".join(sorted(regions))
                pattern_desc = (
                    f"{region_str}: {cluster['pattern']} "
                    f"(SYSTEMIC - {len(cluster['facility_ids'])} facilities)"
                )
                patterns.append(pattern_desc)
            else:
                # Isolated issue
                regions = set()
                for facility_id in cluster["facility_ids"]:
                    for mismatch in mismatches:
                        if mismatch["facility_id"] == facility_id:
                            region = mismatch["location"].get("region", "Unknown")
                            regions.add(region)
                
                region_str = ", ".join(sorted(regions))
                pattern_desc = (
                    f"{region_str}: {cluster['pattern']} "
                    f"(Isolated - {len(cluster['facility_ids'])} facilities)"
                )
                patterns.append(pattern_desc)
        
        return patterns