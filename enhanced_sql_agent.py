"""
Enhanced SQL Agent that works with Domain Knowledge Agent normalization.
"""

import os
import sqlite3
import json
from typing import Dict, Any, List
import pandas as pd
from config import Config
from langchain_community.utilities import SQLDatabase


class EnhancedSQLAgent:
    """
    SQL Agent that uses normalized constraints from Domain Knowledge Agent
    to generate accurate queries.
    """
    
    def __init__(self):
        self.db_path = Config.DB_PATH
        self.llm = Config.get_llm()
        
        # Load data into SQLite
        self._load_data_to_sqlite()
        self.db = SQLDatabase.from_uri(f"sqlite:///{self.db_path}")
    
    def _load_data_to_sqlite(self):
        """Load CSV data into SQLite database."""
        print("📊 Loading US healthcare data into SQLite...")
        
        conn = sqlite3.connect(self.db_path)
        
        # Load hospitals
        if os.path.exists(Config.HOSPITALS_CSV):
            hospitals_df = pd.read_csv(Config.HOSPITALS_CSV)
            hospitals_df = self._clean_dataframe(hospitals_df)
            hospitals_df.to_sql("hospitals", conn, if_exists="replace", index=False)
            print(f"  ✓ Loaded {len(hospitals_df)} hospitals")
        
        # Load doctors
        if os.path.exists(Config.DOCTORS_CSV):
            doctors_df = pd.read_csv(Config.DOCTORS_CSV)
            doctors_df.to_sql("doctors", conn, if_exists="replace", index=False)
            print(f"  ✓ Loaded {len(doctors_df)} doctors")
        
        # Load mapping
        if os.path.exists(Config.MAPPING_CSV):
            mapping_df = pd.read_csv(Config.MAPPING_CSV)
            mapping_df.to_sql("hospital_doctor_mapping", conn, if_exists="replace", index=False)
            print(f"  ✓ Loaded {len(mapping_df)} hospital-doctor mappings")
        
        # Load department summary
        if os.path.exists(Config.DEPT_SUMMARY_CSV):
            dept_df = pd.read_csv(Config.DEPT_SUMMARY_CSV)
            dept_df.to_sql("department_summary", conn, if_exists="replace", index=False)
            print(f"  ✓ Loaded {len(dept_df)} department summaries")
        
        conn.close()
        print("✓ Database loaded successfully\n")
    
    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and prepare dataframe for SQL operations."""
        # Convert JSON string columns to searchable text
        json_columns = ['specialties', 'procedure', 'equipment', 'capability']
        
        for col in json_columns:
            if col in df.columns:
                df[f'{col}_text'] = df[col].apply(
                    lambda x: self._extract_text_from_json(x) if pd.notna(x) else ''
                )
        
        return df
    
    def _extract_text_from_json(self, json_str: str) -> str:
        """Extract searchable text from JSON string."""
        try:
            if isinstance(json_str, str):
                data = json.loads(json_str)
                if isinstance(data, list):
                    return ' | '.join(str(item) for item in data)
                return str(data)
        except:
            pass
        return str(json_str) if json_str else ''

    def generate_sql_with_normalization(
        self, 
        question: str, 
        normalized_constraints: Dict[str, Any]
    ) -> str:
        """
        Generate SQL query using normalized constraints.
        
        Args:
            question: Original user question
            normalized_constraints: Output from Domain Knowledge Agent
            
        Returns:
            SQL query string
        """
        schema = self.db.get_table_info()
        
        # Extract normalized data
        norm_query = normalized_constraints.get("normalized_query", {})
        geography = normalized_constraints.get("geography", {})
        medical = normalized_constraints.get("medical", {})
        sql_hints = normalized_constraints.get("sql_hints", {})
        
        # Build context for LLM
        constraints_context = self._build_constraints_context(
            geography, medical, sql_hints
        )
        
        prompt = f"""You are a Healthcare Data SQL Agent. Generate a SQL query using NORMALIZED constraints.

DATABASE SCHEMA:
{schema}

TABLES:
1. hospitals - Healthcare facilities
   - Key: pk_unique_id
   - Location: address_city, address_stateOrRegion (USPS codes)
   - Searchable text: specialties_text, capability_text, equipment_text

2. doctors - Healthcare providers  
   - Key: doctor_npi
   - specialty, department
   - Location: practice_city, practice_state

3. hospital_doctor_mapping - Links doctors to hospitals
   - hospital_id, doctor_npi, specialty, department

NORMALIZED CONSTRAINTS (PRE-PROCESSED):
{constraints_context}

RULES:
1. Return ONLY valid SQL - no markdown, no explanations
2. Use the EXACT state codes provided: {geography.get('states', [])}
3. Use the EXACT specialty names provided: {medical.get('specialties', [])}
4. For multiple states: WHERE d.practice_state IN ({','.join(repr(s) for s in geography.get('states', []))})
5. For specialty searches: WHERE LOWER(d.specialty) = LOWER('{medical.get('specialties', [''])[0] if medical.get('specialties') else ''}')
6. Always use doctors table when counting neurologists/doctors/physicians
7. Use COUNT(DISTINCT d.doctor_npi) for counting doctors
8. Use COUNT(DISTINCT h.pk_unique_id) for counting hospitals
9. Join syntax: FROM doctors d [optional: JOIN hospital_doctor_mapping m ON d.doctor_npi = m.doctor_npi]
10. For "How many X in Y" questions about doctors, use: SELECT COUNT(DISTINCT d.doctor_npi) FROM doctors d WHERE ...

ORIGINAL QUESTION: {question}

Generate SQL query:"""
        
        response = self.llm.invoke(prompt)
        print(f"   LLM Response: {response.content}")
        sql = response.content.strip()
        
        # Clean up SQL
        sql = sql.replace("```sql", "").replace("```", "").strip()
        if sql.endswith(";"):
            sql = sql[:-1]
        
        return sql
    
    def _build_constraints_context(
        self,
        geography: Dict[str, Any],
        medical: Dict[str, Any],
        sql_hints: Dict[str, Any]
    ) -> str:
        """Build human-readable constraints context."""
        context_parts = []
        
        # Geography
        if geography.get("states"):
            states_str = ", ".join(geography["states"])
            context_parts.append(f"Geographic Filter: States = {states_str}")
            if geography.get("region_name"):
                context_parts.append(f"  (Region: {geography['region_name']})")
        
        if geography.get("cities"):
            cities_str = ", ".join(geography["cities"])
            context_parts.append(f"Cities: {cities_str}")
        
        # Medical
        if medical.get("specialties"):
            spec_str = ", ".join(medical["specialties"])
            context_parts.append(f"Specialties (EXACT database values): {spec_str}")
        
        if medical.get("departments"):
            dept_str = ", ".join(medical["departments"])
            context_parts.append(f"Departments: {dept_str}")
        
        if medical.get("original_terms"):
            orig_str = ", ".join(medical["original_terms"])
            context_parts.append(f"  (User said: {orig_str})")
        
        # SQL hints
        if sql_hints.get("state_filter"):
            context_parts.append(f"\nSQL State Filter: {sql_hints['state_filter']}")
        
        if sql_hints.get("specialty_filter"):
            context_parts.append(f"SQL Specialty Filter: {sql_hints['specialty_filter']}")
        
        if sql_hints.get("suggested_joins"):
            joins_str = ", ".join(sql_hints["suggested_joins"])
            context_parts.append(f"Suggested Joins: {joins_str}")
        
        return "\n".join(context_parts) if context_parts else "No specific constraints"

    def execute_query(self, sql: str) -> Dict[str, Any]:
        """Execute SQL query and return results."""
        try:
            conn = sqlite3.connect(self.db_path)
            print("   Executing SQL query..." , conn)
            df = pd.read_sql_query(sql, conn)
            print(df)
            conn.close()
            
            return {
                "success": True,
                "sql": sql,
                "data": df,
                "row_count": len(df),
                "columns": df.columns.tolist()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "sql": sql
            }
    
    def __call__(self, state: Dict) -> Dict:
        """
        LangGraph node interface.
        
        Args:
            state: AppState dictionary with normalized_constraints
            
        Returns:
            Partial state update with SQL results
        """
        user_question = state["messages"][-1].content

        print(f"\n🔍 SQL Agent received state: {state}")
        # Get normalized constraints from Domain Knowledge Agent
        normalized_constraints = state.get("normalized_constraints")
        print("in enhanced sql agent" , normalized_constraints  )
        print("state in sql agent after nor" , state)
        if not normalized_constraints:
            print("⚠️ No normalized constraints found - Domain Knowledge Agent may not have run")
            # Fall back to basic query generation
            return self._fallback_query(state, user_question)
        
        # Generate SQL using normalized constraints
        print(f"\n💾 SQL Agent: Generating query with normalized constraints...")
        sql = self.generate_sql_with_normalization(user_question, normalized_constraints)
        print(f"   Generated SQL: {sql[:100]}...")
        
        # Execute query
        result = self.execute_query(sql)
        
        if result["success"]:
            print(f"   ✓ Query returned {result['row_count']} rows")
        else:
            print(f"   ✗ Query failed: {result['error']}")
        
        # Prepare citations
        citations = []
        if result["success"] and result["row_count"] > 0:
            citations.append({
                "agent": "EnhancedSQLAgent",
                "source": "US Gov Dataset",
                "query": sql,
                "rows_analyzed": result["row_count"],
                "normalization_used": True
            })
        
        return {
            "sql_result": result,
            "citations": state.get("citations", []) + citations,
            "errors": state.get("errors", []) + (
                [f"SQL Error: {result['error']}"] if not result["success"] else []
            )
        }
    
    def _fallback_query(self, state: Dict, question: str) -> Dict:
        """Fallback to basic SQL generation without normalization."""
        print("⚠️ Using fallback SQL generation (no normalization)")
        
        # Use the original SQL agent logic as fallback
        from sql_agent import SQLAgent
        fallback_agent = SQLAgent()
        return fallback_agent(state)