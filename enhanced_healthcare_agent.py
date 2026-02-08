"""
Enhanced Healthcare Agent Multi-Agent System
Complete orchestration with analytics capabilities using LangGraph
"""

from typing import Dict, Any
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from enhanced_state import AppState
from config import Config

# Import all agents
from sql_agent import SQLAgent
from vector_agent import VectorAgent
from geo_agent import GeoAgent
from skill_infra_agent import SkillInfraAgent
from reachability_agent import ReachabilityAgent
from contradiction_agent import ContradictionAgent
from counterfactual_engine import CounterfactualEngine
from desert_topology_agent import DesertTypologyAgent
from data_quality_router import DataQualityRouter


class SupervisorAgent:
    """Enhanced supervisor with analytics query routing."""
    
    def __init__(self):
        self.llm = Config.get_llm()
    
    def __call__(self, state: AppState) -> Dict:
        """Classify user intent and route to appropriate agent."""
        user_message = state["messages"][-1].content
        
        prompt = f"""You are the Supervisor Agent for the US Healthcare healthcare data system.

Your job is to ROUTE user questions to the correct downstream agents.
Choose EXACTLY ONE of these intent labels:

SQL_QUERY:
- Simple counts, filters, aggregations
- Examples: "How many hospitals have cardiology?", "Which region has most hospitals?"

VECTOR_QUERY:
- Semantic search over facility descriptions
- Examples: "What services does major medical centers offer?"

GEO_QUERY:
- Geographic analysis, proximity, distance
- Examples: "How many hospitals within 50 km of major cities?"

ANALYTICS_QUERY:
- Data quality analysis, mismatches, contradictions, reachability, deserts
- Keywords: "mismatch", "claim without", "accessible", "desert", "contradiction"
- Examples: "Which facilities claim neurosurgery without ICU?", "Medical deserts in United States?"

COUNTERFACTUAL_QUERY:
- What-if scenarios, simulations
- Keywords: "what if", "suppose we", "if we added"
- Examples: "What if we added 3 dialysis centers in underserved states?"

HYBRID_QUERY:
- Complex queries needing multiple agent types
- Medical reasoning + SQL/Geo analysis

END:
- Out of scope

User question: {user_message}

Intent:"""
        
        response = self.llm.invoke(prompt)
        intent = response.content.strip()
        
        # Validate intent
        valid_intents = {
            "SQL_QUERY", "GEO_QUERY", "VECTOR_QUERY", 
            "ANALYTICS_QUERY", "COUNTERFACTUAL_QUERY",
            "HYBRID_QUERY", "END"
        }
        
        if intent not in valid_intents:
            intent = "SQL_QUERY"  # Default fallback
        
        print(f"\n🎯 Supervisor classified intent: {intent}")
        
        return {
            "intent": intent,
            "intermediate_results": {
                **state.get("intermediate_results", {}),
                "supervisor_decision": intent
            }
        }


class ResponseAgent:
    """Enhanced response agent with analytics synthesis."""
    
    def __init__(self):
        self.llm = Config.get_llm()
    
    def __call__(self, state: AppState) -> Dict:
        """Generate final user-facing response."""
        user_question = state["messages"][-1].content
        
        # Build context from all results
        context = self._build_context(state)
        
        prompt = f"""You are the Healthcare Agent response generator.

Synthesize a clear, accurate answer using the provided data.

USER QUESTION:
{user_question}

AVAILABLE DATA:
{context}

GUIDELINES:
1. Answer directly and concisely
2. Cite specific numbers and facts
3. Highlight data quality concerns if found
4. Mention systemic patterns if detected
5. Use clear, non-technical language

Generate response (2-4 paragraphs):"""
        
        response = self.llm.invoke(prompt)
        final_answer = response.content.strip()
        
        # Add citations
        citations_summary = self._format_citations(state.get("citations", []))
        if citations_summary:
            final_answer += f"\n\n{citations_summary}"
        
        print(f"\n✅ Response generated")
        
        return {
            "final_response": final_answer,
            "messages": state["messages"] + [AIMessage(content=final_answer)]
        }
    
    def _build_context(self, state: AppState) -> str:
        """Build context from all agent results."""
        parts = []
        
        # SQL results
        if state.get("sql_result") and state["sql_result"].get("success"):
            sql_data = state["sql_result"]["data"]
            parts.append(f"SQL Results ({len(sql_data)} rows):")
            parts.append(sql_data.head(10).to_string())
        
        # Analytics results summary
        analytics = state.get("analytics_results", {})
        if analytics:
            parts.append("\nAnalytics Results:")
            for agent_name, result in analytics.items():
                parts.append(f"\n{agent_name}: {result.get('summary', 'N/A')}")
        
        # Skill-infrastructure mismatches
        mismatches = state.get("skill_infra_mismatches", [])
        if mismatches:
            parts.append(f"\nSkill-Infrastructure Mismatches ({len(mismatches)} found):")
            for m in mismatches[:5]:
                parts.append(
                    f"  • {m['facility_name']}: claims {m['claimed_capability']} "
                    f"but missing {', '.join(m['missing_infrastructure'][:2])} "
                    f"({m['severity']} severity)"
                )
        
        # Reachability scores
        reachability = state.get("reachability_scores", {})
        if reachability:
            parts.append(f"\nReachability Scores:")
            for key, score in list(reachability.items())[:5]:
                parts.append(
                    f"  • {score['location']} - {score['target_capability']}: "
                    f"{score['combined_score']}/100 "
                    f"(geo: {score['geographic_score']}, capability: {score['capability_score']})"
                )
        
        # Contradiction graph
        contradiction_graph = state.get("contradiction_graph")
        if contradiction_graph:
            parts.append(f"\nContradiction Analysis:")
            parts.append(f"  • {len(contradiction_graph['nodes'])} contradictions detected")
            parts.append(f"  • {len(contradiction_graph['clusters'])} patterns identified")
            if contradiction_graph.get("systemic_patterns"):
                parts.append("  • Systemic issues:")
                for pattern in contradiction_graph["systemic_patterns"][:3]:
                    parts.append(f"    - {pattern}")
        
        # Desert typology
        deserts = state.get("desert_typology", {})
        if deserts:
            parts.append(f"\nMedical Desert Classification:")
            for key, desert in list(deserts.items())[:3]:
                types_str = ", ".join(desert['desert_types'])
                parts.append(
                    f"  • {desert['region']}: {types_str} desert ({desert['severity']})"
                )
        
        # Counterfactual results
        counterfactual = state.get("counterfactual_state")
        if counterfactual and counterfactual.get("is_active"):
            parts.append(f"\nCounterfactual Simulation:")
            parts.append(f"  Scenario: {counterfactual['description']}")
            if counterfactual.get("delta_metrics"):
                parts.append(f"  Impact: {counterfactual['delta_metrics']}")
        
        return "\n".join(parts) if parts else "No data available"
    
    def _format_citations(self, citations: list) -> str:
        """Format citations for transparency."""
        if not citations:
            return ""
        
        parts = ["---", "Data Sources:"]
        for cite in citations:
            agent = cite.get("agent", "Unknown")
            if agent == "SQLAgent":
                parts.append(f"• SQL analysis of {cite.get('rows_analyzed', 0)} facilities")
            elif agent == "SkillInfraAgent":
                parts.append(f"• Infrastructure mismatch detection ({cite.get('facilities_analyzed', 0)} facilities)")
            elif agent == "ReachabilityAgent":
                parts.append(f"• Reachability scoring ({cite.get('locations_analyzed', 0)} locations)")
            elif agent == "ContradictionAgent":
                parts.append(f"• Contradiction pattern analysis ({cite.get('nodes_analyzed', 0)} cases)")
            elif agent == "DesertTypologyAgent":
                parts.append(f"• Medical desert classification ({cite.get('deserts_classified', 0)} regions)")
            elif agent == "GeoAgent":
                parts.append(f"• Geospatial analysis ({cite.get('locations_analyzed', 0)} locations)")
        
        return "\n".join(parts)


def build_enhanced_graph() -> StateGraph:
    """Build the complete enhanced Healthcare Agent graph with analytics capabilities."""
    
    print("\n🏗️  Building enhanced Healthcare Agent graph...")
    
    # Initialize all agents
    supervisor = SupervisorAgent()
    sql_agent = SQLAgent()
    vector_agent = VectorAgent()
    geo_agent = GeoAgent()
    
    # Analytics agents
    data_quality_router = DataQualityRouter()
    skill_infra_agent = SkillInfraAgent()
    reachability_agent = ReachabilityAgent()
    contradiction_agent = ContradictionAgent()
    desert_typology_agent = DesertTypologyAgent()
    counterfactual_engine = CounterfactualEngine()
    
    response_agent = ResponseAgent()
    
    # Create graph
    graph = StateGraph(AppState)
    
    # Add nodes
    graph.add_node("Supervisor", supervisor)
    graph.add_node("SQLAgent", sql_agent)
    graph.add_node("VectorAgent", vector_agent)
    graph.add_node("GeoAgent", geo_agent)
    graph.add_node("DataQualityRouter", data_quality_router)
    graph.add_node("SkillInfraAgent", skill_infra_agent)
    graph.add_node("ReachabilityAgent", reachability_agent)
    graph.add_node("ContradictionAgent", contradiction_agent)
    graph.add_node("DesertTypologyAgent", desert_typology_agent)
    graph.add_node("CounterfactualEngine", counterfactual_engine)
    graph.add_node("ResponseAgent", response_agent)
    
    # Set entry point
    graph.set_entry_point("Supervisor")
    
    # Routing from Supervisor
    def route_from_supervisor(state: AppState) -> str:
        intent = state.get("intent", "SQL_QUERY")
        
        if intent == "SQL_QUERY":
            return "SQLAgent"
        elif intent == "VECTOR_QUERY":
            return "VectorAgent"
        elif intent == "GEO_QUERY":
            return "GeoAgent"
        elif intent == "ANALYTICS_QUERY":
            return "DataQualityRouter"
        elif intent == "COUNTERFACTUAL_QUERY":
            return "CounterfactualEngine"
        elif intent == "HYBRID_QUERY":
            return "SQLAgent"  # Start with SQL for hybrid
        else:
            return "ResponseAgent"
    
    graph.add_conditional_edges(
        "Supervisor",
        route_from_supervisor,
        {
            "SQLAgent": "SQLAgent",
            "VectorAgent": "VectorAgent",
            "GeoAgent": "GeoAgent",
            "DataQualityRouter": "DataQualityRouter",
            "CounterfactualEngine": "CounterfactualEngine",
            "ResponseAgent": "ResponseAgent"
        }
    )
    
    # Analytics pipeline routing
    def route_analytics_pipeline(state: AppState) -> str:
        """Execute analytics agents in sequence."""
        plan = state.get("analytics_plan", [])
        executed = state.get("analytics_executed", [])
        
        # Find next agent
        for agent_name in plan:
            if agent_name not in executed:
                return agent_name
        
        # All done
        return "ResponseAgent"
    
    # DataQualityRouter edges
    graph.add_conditional_edges(
        "DataQualityRouter",
        route_analytics_pipeline,
        {
            "SkillInfraAgent": "SkillInfraAgent",
            "GeoAgent": "GeoAgent",
            "ReachabilityAgent": "ReachabilityAgent",
            "ContradictionAgent": "ContradictionAgent",
            "DesertTypologyAgent": "DesertTypologyAgent",
            "ResponseAgent": "ResponseAgent"
        }
    )
    
    # Analytics agents loop back
    for agent in ["SkillInfraAgent", "ReachabilityAgent", "ContradictionAgent", "DesertTypologyAgent"]:
        graph.add_conditional_edges(
            agent,
            route_analytics_pipeline,
            {
                "SkillInfraAgent": "SkillInfraAgent",
                "GeoAgent": "GeoAgent",
                "ReachabilityAgent": "ReachabilityAgent",
                "ContradictionAgent": "ContradictionAgent",
                "DesertTypologyAgent": "DesertTypologyAgent",
                "ResponseAgent": "ResponseAgent"
            }
        )
    
    # Standard agent edges
    graph.add_edge("SQLAgent", "ResponseAgent")
    graph.add_edge("VectorAgent", "ResponseAgent")
    graph.add_edge("GeoAgent", "ResponseAgent")
    graph.add_edge("CounterfactualEngine", "GeoAgent")  # Re-run geo with simulation
    graph.add_edge("ResponseAgent", END)
    
    print("✓ Graph built successfully")
    
    return graph.compile()


def run_query(question: str) -> str:
    """
    Run a query through the enhanced Healthcare Agent system.
    
    Args:
        question: Natural language question
        
    Returns:
        Final response string
    """
    print("\n" + "="*70)
    print("Healthcare AGENT - ENHANCED SYSTEM")
    print("="*70)
    print(f"\nQuestion: {question}")
    print("-"*70)
    
    app = build_enhanced_graph()
    
    # Initialize state
    initial_state: AppState = {
        "messages": [HumanMessage(content=question)],
        "intent": "",
        "plan": None,
        "sql_result": None,
        "vector_result": None,
        "geo_result": None,
        "medical_reasoning": None,
        "intermediate_results": {},
        "final_response": None,
        "errors": [],
        "citations": [],
        # Analytics fields
        "analytics_plan": None,
        "analytics_results": {},
        "analytics_executed": [],
        "skill_infra_mismatches": [],
        "reachability_scores": {},
        "contradiction_graph": None,
        "counterfactual_state": None,
        "desert_typology": {},
        "external_search_results": {},
        "verification_needed": []
    }
    
    # Run graph
    try:
        final_state = app.invoke(initial_state)
        response = final_state.get("final_response", "No response generated")
        
        print("\n" + "="*70)
        print("RESPONSE:")
        print("="*70)
        print(response)
        print("\n" + "="*70)
        
        return response
    
    except Exception as e:
        error_msg = f"Error processing query: {str(e)}"
        print(f"\n❌ {error_msg}")
        import traceback
        traceback.print_exc()
        return error_msg


if __name__ == "__main__":
    # Validate configuration
    Config.validate_config()
    
    # Test queries
    test_queries = [
        "Which facilities claim neurosurgery but lack ICU?",
        "How accessible is dialysis in underserved states?",
        "Are there systemic data quality issues in ophthalmology claims?",
        "Which regions are medical deserts for cardiology?",
        "What if we added 5 dialysis centers in rural areas?"
    ]
    
    print("\n" + "="*70)
    print("Healthcare AGENT - TEST RUN")
    print("="*70)
    
    for query in test_queries[:2]:  # Run first 2 queries as demo
        run_query(query)
        print("\n")
