"""
Enhanced Healthcare Agent Multi-Agent System
Complete orchestration with analytics capabilities using LangGraph
NOW WITH EXTERNAL VERIFICATION AGENT!
"""

from typing import Dict, Any
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from enhanced_state import AppState
from config import Config

# Import all agents
from vector_agent import VectorAgent
from geo_agent import GeoAgent
from skill_infra_agent import SkillInfraAgent
from reachability_agent import ReachabilityAgent
from contradiction_agent import ContradictionAgent
from counterfactual_engine import CounterfactualEngine
from desert_topology_agent import DesertTypologyAgent
from data_quality_router import DataQualityRouter
from external_verification_agent import ExternalVerificationAgent  # 🆕 NEW!

from domain_knowledge_agent import DomainKnowledgeAgent
from enhanced_sql_agent import EnhancedSQLAgent

class SupervisorAgent:
    """Enhanced supervisor with analytics query routing."""
    
    def __init__(self):
        self.llm = Config.get_llm()
    
    def __call__(self, state: AppState) -> Dict:
        """Classify user intent and route to appropriate agent."""
        user_message = state["messages"][-1].content

        print(f"\n🧭 SupervisorAgent: Analyzing user message: {user_message}")
        
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
- Data quality analysis, mismatches, contradictions
- Examples: "Which facilities claim neurosurgery but lack ICU?", "Find data quality issues"

COUNTERFACTUAL_QUERY:
- What-if scenarios and simulations
- Examples: "What if we add 5 dialysis centers in rural Texas?"

HYBRID_QUERY:
- Requires multiple types of analysis
- Examples: "Compare cardiology coverage across regions with accessibility scores"

User question: {user_message}

Return ONLY ONE WORD (the intent label):"""
        
        try:
            response = self.llm.invoke(prompt)
            intent = response.content.strip().upper()
            
            # Validate intent
            valid_intents = ["SQL_QUERY", "VECTOR_QUERY", "GEO_QUERY", "ANALYTICS_QUERY", 
                           "COUNTERFACTUAL_QUERY", "HYBRID_QUERY"]
            
            if intent not in valid_intents:
                intent = "SQL_QUERY"  # Default
            
            print(f"🧭 Intent classified: {intent}")
            
            return {"intent": intent}
            
        except Exception as e:
            print(f"⚠️  Intent classification error: {e}")
            return {"intent": "SQL_QUERY"}


class ResponseAgent:
    """Final response synthesis with citations."""
    
    def __init__(self):
        self.llm = Config.get_llm()
    
    def __call__(self, state: AppState) -> Dict:
        """Synthesize final response from all agent results."""
        print(f"\n📝 ResponseAgent: Synthesizing final answer for intent: {state.get('intent', 'unknown')}")
        print("Response state : " , state)
        
        # Gather all results
        results_summary = self._compile_results(state)
        citations = self._format_citations(state.get("citations", []))
        
        # Use LLM to generate natural language response
        user_question = state["messages"][-1].content
        
        prompt = f"""You are a healthcare data analyst. Answer the user's question using ONLY the data provided.

User question: {user_question}

Available data:
{results_summary}

{citations}

1. Answer directly and concisely
2. Cite specific numbers and facts
3. Highlight data quality concerns if found
4. Mention systemic patterns if detected
5. Use clear, non-technical language
Generate a clear, concise answer. Include specific numbers and facts. Be direct and accurate.
If external verification was performed, mention the verification results.
If no data is available, say "No data available to answer this question."
Dont tell as if you are an AI, just answer the question as best as possible using the data
Dont tell in table, so many records are there, just summarize the key insights from the data, dont be like, based on SQL Analysis,


Answer:"""
        
        try:
            response = self.llm.invoke(prompt)
            final_answer = response.content.strip()
            
            # Append citations
            if citations:
                final_answer += "\n\n" + citations
            
            print("✓ Response generated")
            
            return {
                "final_response": final_answer,
                "messages": state["messages"] + [AIMessage(content=final_answer)]
            }
            
        except Exception as e:
            error_msg = f"Error generating response: {str(e)}"
            print(f"⚠️  {error_msg}")
            return {
                "final_response": error_msg,
                "messages": state["messages"] + [AIMessage(content=error_msg)]
            }
    
    def _compile_results(self, state: AppState) -> str:
        """Compile all agent results into summary."""
        parts = []
        
        # SQL results
        sql_result = state.get("sql_result")
        if sql_result and sql_result.get("success"):
            parts.append(f"SQL Analysis: {sql_result.get('row_count', 0)} records found")
            data = sql_result.get("data")
            if data is not None and len(data) > 0:
                parts.append(f"Sample data:\n{data.head(10).to_string()}")
        
        # Vector results
        vector_result = state.get("vector_result")
        if vector_result and vector_result.get("success"):
            parts.append(f"\nSemantic Search: {vector_result.get('count', 0)} relevant facilities")
        
        # Geo results
        geo_result = state.get("geo_result")
        if geo_result and geo_result.get("success"):
            parts.append(f"\nGeographic Analysis: {geo_result.get('count', 0)} locations analyzed")
        
        # Analytics results
        analytics = state.get("analytics_results", {})
        
        # Skill-infrastructure mismatches
        if "skill_infra" in analytics:
            si = analytics["skill_infra"]
            parts.append(f"\nData Quality Issues:")
            parts.append(f"  • {si.get('mismatches_found', 0)} mismatches detected")
            parts.append(f"  • {si.get('critical_mismatches', 0)} critical cases")
        
        # Reachability scores
        if "reachability" in analytics:
            reach = analytics["reachability"]
            parts.append(f"\nAccessibility Analysis:")
            parts.append(f"  • Average reachability: {reach.get('average_reachability_score', 0)}/100")
            parts.append(f"  • Low access areas: {reach.get('low_reachability_count', 0)}")
        
        # Contradiction analysis
        if "contradictions" in analytics:
            contra = analytics["contradictions"]
            parts.append(f"\nContradiction Analysis:")
            parts.append(f"  • {contra.get('systemic_clusters', 0)} systemic patterns")
            parts.append(f"  • {contra.get('isolated_clusters', 0)} isolated cases")
        
        # Desert classification
        desert_typology = state.get("desert_typology", {})
        if desert_typology:
            parts.append(f"\nMedical Deserts Identified:")
            for key, desert in desert_typology.items():
                types_str = ", ".join(desert.get("desert_types", []))
                parts.append(
                    f"  • {desert['region']}: {types_str} desert ({desert['severity']})"
                )
        
        # 🆕 External verification results
        external_results = state.get("external_search_results", {})
        if external_results:
            parts.append(f"\n🔍 External Verification Results:")
            for claim_id, verification in external_results.items():
                if isinstance(verification, dict):
                    verified = verification.get("verified")
                    if verified is True:
                        parts.append(f"  ✅ VERIFIED: {verification.get('evidence', 'No details')}")
                    elif verified is False:
                        parts.append(f"  ❌ REFUTED: {verification.get('evidence', 'No details')}")
                    else:
                        parts.append(f"  ⚠️ INCONCLUSIVE: {verification.get('evidence', 'Insufficient evidence')}")
        
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
            elif agent == "ExternalVerificationAgent":  # 🆕 NEW!
                parts.append(f"• 🔍 External verification via {cite.get('sources', 'web search')} ({cite.get('claims_verified', 0)} claims)")
        
        return "\n".join(parts)


def build_enhanced_graph() -> StateGraph:
    """Build the complete enhanced Healthcare Agent graph with analytics capabilities."""
    
    print("\n🏗️  Building enhanced Healthcare Agent graph...")
    
    # Initialize all agents
    supervisor = SupervisorAgent()
    sql_agent = EnhancedSQLAgent()
    vector_agent = VectorAgent()
    geo_agent = GeoAgent()
    
    # Analytics agents
    data_quality_router = DataQualityRouter()
    domain_knowledge_agent = DomainKnowledgeAgent(llm=Config.get_llm())
    skill_infra_agent = SkillInfraAgent()
    reachability_agent = ReachabilityAgent()
    contradiction_agent = ContradictionAgent()
    desert_typology_agent = DesertTypologyAgent()
    counterfactual_engine = CounterfactualEngine()
    
    # 🆕 External verification agent
    external_verification_agent = ExternalVerificationAgent()
    
    response_agent = ResponseAgent()
    
    # Create graph
    graph = StateGraph(AppState)
    
    # Add nodes
    graph.add_node("Supervisor", supervisor)
    graph.add_node("DomainKnowledgeAgent", domain_knowledge_agent)
    graph.add_node("SQLAgent", sql_agent)
    graph.add_node("VectorAgent", vector_agent)
    graph.add_node("GeoAgent", geo_agent)
    graph.add_node("DataQualityRouter", data_quality_router)
    graph.add_node("SkillInfraAgent", skill_infra_agent)
    graph.add_node("ReachabilityAgent", reachability_agent)
    graph.add_node("ContradictionAgent", contradiction_agent)
    graph.add_node("DesertTypologyAgent", desert_typology_agent)
    graph.add_node("CounterfactualEngine", counterfactual_engine)
    graph.add_node("ExternalVerificationAgent", external_verification_agent)  # 🆕 NEW!
    graph.add_node("ResponseAgent", response_agent)
    
    # Set entry point
    graph.set_entry_point("Supervisor")
    
    # Routing from Supervisor
    def route_from_supervisor(state: AppState) -> str:
        intent = state.get("intent", "SQL_QUERY")
        
        if intent == "SQL_QUERY":
            return "DomainKnowledgeAgent"  # CHANGED: Route to normalization first!
        elif intent == "VECTOR_QUERY":
            return "VectorAgent"
        elif intent == "GEO_QUERY":
            return "GeoAgent"
        elif intent == "ANALYTICS_QUERY":
            return "DataQualityRouter"
        elif intent == "COUNTERFACTUAL_QUERY":
            return "CounterfactualEngine"
        elif intent == "HYBRID_QUERY":
            return "DomainKnowledgeAgent"  # CHANGED: Hybrid also needs normalization
        else:
            return "ResponseAgent"
    
    graph.add_conditional_edges(
        "Supervisor",
        route_from_supervisor,
        {
            "DomainKnowledgeAgent": "DomainKnowledgeAgent",  # CHANGED: Added this route
            "SQLAgent": "SQLAgent",
            "VectorAgent": "VectorAgent",
            "GeoAgent": "GeoAgent",
            "DataQualityRouter": "DataQualityRouter",
            "CounterfactualEngine": "CounterfactualEngine",
            "ResponseAgent": "ResponseAgent"
        }
    )
    
    # 🆕 NEW: Route to verification if needed
    def route_from_core_agents(state: AppState) -> str:
        """Check if external verification is needed after core agents."""
        
        # Check if verification is enabled
        if not Config.ENABLE_EXTERNAL_VERIFICATION:
            return "ResponseAgent"
        
        # Check if verification is needed
        verification_needed = state.get("verification_needed", [])
        
        # Check if results are insufficient
        sql_result = state.get("sql_result", {})
        vector_result = state.get("vector_result", {})
        
        sql_insufficient = sql_result.get("success") and sql_result.get("row_count", 0) == 0
        vector_insufficient = vector_result.get("success") and vector_result.get("count", 0) == 0
        
        if verification_needed or sql_insufficient or vector_insufficient:
            return "ExternalVerificationAgent"
        
        return "ResponseAgent"
    
    # Analytics pipeline routing
    def route_analytics_pipeline(state: AppState) -> str:
        """Execute analytics agents in sequence."""
        plan = state.get("analytics_plan", [])
        executed = state.get("analytics_executed", [])
        
        # Find next agent
        for agent_name in plan:
            if agent_name not in executed:
                return agent_name
        
        # 🆕 After analytics, check if verification needed
        if Config.ENABLE_EXTERNAL_VERIFICATION:
            verification_needed = state.get("verification_needed", [])
            if verification_needed and "ExternalVerificationAgent" not in executed:
                return "ExternalVerificationAgent"
        
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
            "ExternalVerificationAgent": "ExternalVerificationAgent",  # 🆕 NEW!
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
                "ExternalVerificationAgent": "ExternalVerificationAgent",  # 🆕 NEW!
                "ResponseAgent": "ResponseAgent"
            }
        )
    
    # 🆕 NEW: Core agents route through verification check
    graph.add_conditional_edges(
        "SQLAgent",
        route_from_core_agents,
        {
            "ExternalVerificationAgent": "ExternalVerificationAgent",
            "ResponseAgent": "ResponseAgent"
        }
    )
    
    graph.add_conditional_edges(
        "VectorAgent",
        route_from_core_agents,
        {
            "ExternalVerificationAgent": "ExternalVerificationAgent",
            "ResponseAgent": "ResponseAgent"
        }
    )
    
    # CRITICAL: DomainKnowledgeAgent always routes to SQLAgent for normalization
    graph.add_edge("DomainKnowledgeAgent", "SQLAgent")
    graph.add_edge("ExternalVerificationAgent", "ResponseAgent")
    
    # Other standard edges
    graph.add_edge("GeoAgent", "ResponseAgent")
    graph.add_edge("CounterfactualEngine", "GeoAgent")  # Re-run geo with simulation
    graph.add_edge("ResponseAgent", END)



    
    print("✓ Graph built successfully with External Verification Agent!")
    
    # Compile graph
    app = graph.compile()
    graph_ = app.get_graph()

    png_bytes = graph_.draw_mermaid_png()

    with open("HealthcareAgentGraph.png", "wb") as f:
        f.write(png_bytes)


    return app


def run_query(question: str) -> Dict[str, Any]:
    """
    Main entry point - run a query through the healthcare agent system.
    
    Args:
        question: User's natural language question
        
    Returns:
        Complete state with all agent results
    """
    
    # Build graph
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
        # 🆕 External verification fields
        "external_search_results": {},
        "verification_needed": [],
        # 🆕 Normalization fields
        "normalized_constraints": {}  # NEW: For domain knowledge normalization
    }
    
    # Run graph
    print(f"\n{'='*70}")
    print(f"PROCESSING QUERY: {question}")
    print('='*70)
    
    final_state = app.invoke(initial_state)
    
    print(f"\n{'='*70}")
    print("QUERY COMPLETE")
    print('='*70)
    
    # Print final response
    if final_state.get("final_response"):
        print(f"\n{final_state['final_response']}\n")
    
    return final_state


if __name__ == "__main__":
    # Test queries
    test_queries = [
        "How many hospitals are in California?",
        "Which facilities claim neurosurgery but lack ICU infrastructure?",
    ]
    
    for query in test_queries:
        result = run_query(query)
        print("\n" + "="*70 + "\n")