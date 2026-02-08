"""
Integration Guide: Enhanced Domain Knowledge + SQL Agent

This shows how to integrate the improved agents into your workflow.
"""

# ============================================================
# STEP 1: Update your graph workflow
# ============================================================

# In your main graph file (e.g., enhanced_healthcare_agent2.py):

"""
from improved_domain_knowledge_agent import ImprovedDomainKnowledgeAgent
from enhanced_sql_agent import EnhancedSQLAgent

# Create agents
domain_agent = ImprovedDomainKnowledgeAgent(llm)
sql_agent = EnhancedSQLAgent()

# In your graph definition:
graph_builder.add_node("domain_knowledge", domain_agent)
graph_builder.add_node("sql", sql_agent)

# CRITICAL: Domain Knowledge MUST run BEFORE SQL
graph_builder.add_edge("domain_knowledge", "sql")
"""


# ============================================================
# STEP 2: Example usage
# ============================================================

def example_usage():
    """
    Example of how queries flow through the system.
    """
    
    # Example 1: Geographic normalization
    query_1 = "Give me doctors in gynecology in northern america"
    
    # Domain Knowledge Agent normalizes this to:
    normalized_1 = {
        "normalized_query": {
            "geography": {
                "states": ["WA", "OR", "ID", "MT", "WY", "ND", "SD", "MN", 
                          "WI", "MI", "IL", "IN", "OH", "PA", "NY", "VT", 
                          "NH", "ME", "MA", "CT", "RI"],
                "region_name": "northern_america"
            },
            "medical": {
                "specialties": ["Obstetrics & Gynecology"],
                "original_terms": ["gynecology"]
            },
            "sql_hints": {
                "state_filter": "address_stateOrRegion IN ('WA','OR','ID',...)",
                "specialty_filter": "LOWER(specialty) LIKE '%obstetrics & gynecology%'"
            }
        },
        "confidence": "high"
    }
    
    # SQL Agent then generates:
    sql_1 = """
    SELECT DISTINCT 
        d.doctor_npi,
        d.doctor_first_name,
        d.doctor_last_name,
        d.specialty,
        h.name as hospital_name,
        h.address_city,
        h.address_stateOrRegion
    FROM doctors d
    JOIN hospital_doctor_mapping m ON d.doctor_npi = m.doctor_npi
    JOIN hospitals h ON m.hospital_id = h.pk_unique_id
    WHERE h.address_stateOrRegion IN ('WA','OR','ID','MT','WY','ND','SD','MN',
                                       'WI','MI','IL','IN','OH','PA','NY','VT',
                                       'NH','ME','MA','CT','RI')
    AND LOWER(d.specialty) LIKE '%obstetrics & gynecology%'
    """
    
    # Example 2: Medical term normalization
    query_2 = "Find cardiologists in California"
    
    normalized_2 = {
        "normalized_query": {
            "geography": {
                "states": ["CA"],
                "region_name": "california"
            },
            "medical": {
                "specialties": ["Cardiology"],
                "original_terms": ["cardiologist"]
            },
            "sql_hints": {
                "state_filter": "address_stateOrRegion = 'CA'",
                "specialty_filter": "LOWER(specialty) LIKE '%cardiology%'"
            }
        },
        "confidence": "high"
    }
    
    sql_2 = """
    SELECT DISTINCT 
        d.doctor_npi,
        d.doctor_first_name,
        d.doctor_last_name,
        d.specialty,
        h.name as hospital_name,
        h.address_city
    FROM doctors d
    JOIN hospital_doctor_mapping m ON d.doctor_npi = m.doctor_npi
    JOIN hospitals h ON m.hospital_id = h.pk_unique_id
    WHERE h.address_stateOrRegion = 'CA'
    AND LOWER(d.specialty) LIKE '%cardiology%'
    """
    
    return {
        "example_1": {"query": query_1, "normalized": normalized_1, "sql": sql_1},
        "example_2": {"query": query_2, "normalized": normalized_2, "sql": sql_2}
    }


# ============================================================
# STEP 3: Testing the integration
# ============================================================

def test_integration():
    """
    Test the domain knowledge + SQL agent integration.
    """
    from config import Config
    from improved_domain_knowledge_agent import ImprovedDomainKnowledgeAgent
    from enhanced_sql_agent import EnhancedSQLAgent
    from langchain_core.messages import HumanMessage
    
    # Initialize agents
    llm = Config.get_llm()
    domain_agent = ImprovedDomainKnowledgeAgent(llm)
    sql_agent = EnhancedSQLAgent()
    
    # Test queries
    test_queries = [
        "Give me doctors in gynecology in northern america",
        "Find cardiologists in California",
        "Show me surgeons in New York",
        "List pediatricians in the midwest",
        "Emergency medicine doctors in Texas"
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"TESTING: {query}")
        print('='*60)
        
        # Step 1: Domain Knowledge normalization
        state = {"messages": [HumanMessage(content=query)]}
        norm_result = domain_agent(state)
        
        print(f"\n✓ Domain Knowledge Agent:")
        normalized = norm_result["normalized_constraints"]
        print(f"  States: {normalized['normalized_query']['geography']['states']}")
        print(f"  Specialties: {normalized['normalized_query']['medical']['specialties']}")
        print(f"  Confidence: {normalized['confidence']}")
        
        # Step 2: SQL generation with normalized constraints
        state["normalized_constraints"] = normalized
        sql_result = sql_agent(state)
        
        print(f"\n✓ SQL Agent:")
        if sql_result["sql_result"]["success"]:
            print(f"  SQL: {sql_result['sql_result']['sql'][:100]}...")
            print(f"  Rows: {sql_result['sql_result']['row_count']}")
        else:
            print(f"  ERROR: {sql_result['sql_result']['error']}")


# ============================================================
# STEP 4: Common issues and solutions
# ============================================================

COMMON_ISSUES = """
COMMON ISSUES & SOLUTIONS:

1. Issue: "Northern America" not recognized
   Solution: ✓ Domain Knowledge Agent now maps this to USPS state codes
   
2. Issue: "gynecology" vs "Obstetrics & Gynecology"  
   Solution: ✓ Domain Knowledge Agent normalizes medical terms
   
3. Issue: Full state names in SQL queries
   Solution: ✓ Domain Knowledge Agent always outputs USPS codes
   
4. Issue: Case sensitivity in specialty matching
   Solution: ✓ SQL uses LOWER() for case-insensitive search
   
5. Issue: Domain Knowledge Agent not running
   Solution: Ensure graph workflow has domain_knowledge → sql edge
   
6. Issue: Normalized constraints not found in state
   Solution: Check that Domain Knowledge Agent runs before SQL Agent

WORKFLOW VERIFICATION:

✓ Step 1: User query arrives
✓ Step 2: Domain Knowledge Agent normalizes geography + medical terms
✓ Step 3: SQL Agent uses normalized constraints to generate query
✓ Step 4: Query executes with exact database values
✓ Step 5: Results returned

KEY SUCCESS METRICS:
- Confidence = "high" means normalization succeeded
- sql_result["success"] = True means query executed
- row_count > 0 means data found
"""


# ============================================================
# STEP 5: Full workflow example
# ============================================================

def full_workflow_example():
    """
    Complete example showing the full workflow.
    """
    
    print("""
    FULL WORKFLOW EXAMPLE
    =====================
    
    User Query: "Give me doctors in gynecology in northern america"
    
    STEP 1: Domain Knowledge Agent
    -------------------------------
    Input: "Give me doctors in gynecology in northern america"
    
    Processing:
    - "northern america" → geographic_mappings["northern_america"]
    - Result: ["WA", "OR", "ID", "MT", "WY", "ND", "SD", "MN", ...]
    
    - "gynecology" → specialty_mappings["gynecology"]  
    - Result: "Obstetrics & Gynecology"
    
    Output: normalized_constraints = {
        "normalized_query": {
            "geography": {
                "states": ["WA", "OR", "ID", ...],
                "region_name": "northern_america"
            },
            "medical": {
                "specialties": ["Obstetrics & Gynecology"],
                "original_terms": ["gynecology"]
            },
            "sql_hints": {
                "state_filter": "address_stateOrRegion IN ('WA','OR',...)",
                "specialty_filter": "LOWER(specialty) LIKE '%obstetrics & gynecology%'"
            }
        },
        "confidence": "high"
    }
    
    STEP 2: Enhanced SQL Agent
    ---------------------------
    Input: normalized_constraints + original question
    
    Processing:
    - Extracts EXACT states: ["WA", "OR", "ID", ...]
    - Extracts EXACT specialties: ["Obstetrics & Gynecology"]
    - Generates SQL with these exact values
    
    Output: SQL = '''
    SELECT DISTINCT 
        d.doctor_npi,
        d.doctor_first_name,
        d.doctor_last_name,
        d.specialty,
        h.name as hospital_name,
        h.address_city,
        h.address_stateOrRegion
    FROM doctors d
    JOIN hospital_doctor_mapping m ON d.doctor_npi = m.doctor_npi
    JOIN hospitals h ON m.hospital_id = h.pk_unique_id
    WHERE h.address_stateOrRegion IN ('WA','OR','ID','MT','WY','ND','SD','MN',
                                       'WI','MI','IL','IN','OH','PA','NY','VT',
                                       'NH','ME','MA','CT','RI')
    AND LOWER(d.specialty) LIKE '%obstetrics & gynecology%'
    '''
    
    STEP 3: Execution
    -----------------
    - SQL executes against SQLite database
    - Returns doctors matching EXACT criteria
    - Results formatted for user
    
    SUCCESS! ✓
    """)


if __name__ == "__main__":
    print("="*60)
    print("ENHANCED DOMAIN KNOWLEDGE + SQL AGENT INTEGRATION")
    print("="*60)
    
    print("\n" + COMMON_ISSUES)
    
    # Show examples
    examples = example_usage()
    print(f"\nEXAMPLES LOADED: {len(examples)} query patterns")
    
    # Show full workflow
    full_workflow_example()
    
    print("\n" + "="*60)
    print("TO TEST: Run test_integration() function")
    print("="*60)