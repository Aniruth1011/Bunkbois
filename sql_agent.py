"""
Enhanced SQL Agent for US Healthcare Data with medical domain knowledge.
"""

import os
import sqlite3
import json
from typing import Dict, Any, List
import pandas as pd
from config import Config
from langchain_community.utilities import SQLDatabase


class SQLAgent:
    """
    SQL Agent that converts natural language questions to SQL queries
    with medical domain awareness for US healthcare data.
    """
    
    def __init__(self):
        self.db_path = Config.DB_PATH
        self.llm = Config.get_llm()
        
        # Load data into SQLite
        self._load_data_to_sqlite()
        self.db = SQLDatabase.from_uri(f"sqlite:///{self.db_path}")
        
        # Medical domain knowledge
        self.medical_specialties = self._load_medical_knowledge()
    
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
    
    def _load_medical_knowledge(self) -> Dict[str, List[str]]:
        """Load medical domain knowledge for query enhancement."""
        return {
            "cardiology_procedures": [
                "echocardiogram", "angioplasty", "cardiac catheterization",
                "stress test", "holter monitor", "pacemaker"
            ],
            "cardiology_equipment": [
                "ECG machine", "echocardiography", "cardiac monitor",
                "defibrillator", "holter monitor"
            ],
            "surgery_equipment": [
                "operating table", "anesthesia machine", "surgical instruments",
                "operating microscope", "surgical lights", "autoclave"
            ],
            "imaging_equipment": [
                "X-ray", "CT scan", "MRI", "ultrasound", "mammography"
            ],
            "ophthalmology_procedures": [
                "cataract surgery", "glaucoma surgery", "LASIK",
                "retinal surgery", "corneal transplant"
            ],
            "ophthalmology_equipment": [
                "operating microscope", "phacoemulsification machine",
                "slit lamp", "tonometer", "fundus camera"
            ]
        }
    
    def generate_sql(self, question: str) -> str:
        """Generate SQL query from natural language question."""
        schema = self.db.get_table_info()
        
        prompt = f"""You are a Healthcare Data SQL Agent - an expert at converting natural language questions about US healthcare facilities into precise SQL queries.

DATABASE SCHEMA:
{schema}

TABLES AVAILABLE:
1. hospitals - Healthcare facilities/organizations
   - Key columns: name, pk_unique_id, capability, specialties, equipment, procedure
   - Location: address_city, address_stateOrRegion, address_country
   - Type: facilityTypeId, operatorTypeId, organization_type
   
2. doctors - Healthcare providers
   - Key columns: doctor_npi, doctor_first_name, doctor_last_name, specialty, department
   - Location: practice_city, practice_state
   
3. hospital_doctor_mapping - Links doctors to hospitals
   - Key columns: hospital_id, hospital_name, doctor_npi, doctor_full_name, department, specialty
   
4. department_summary - Aggregated department statistics
   - Key columns: affiliated_hospital_name, department, doctor_count

CRITICAL COLUMNS (hospitals table):
- specialties_text: Searchable text version of specialties JSON
- procedure_text: Searchable text version of procedures JSON  
- equipment_text: Searchable text version of equipment JSON
- capability_text: Searchable text version of capabilities JSON
- address_stateOrRegion: State location (CA, NY, TX, etc.)
- address_city: City location

DATA INTERPRETATION RULES:
1. All data represents CLAIMED capabilities by facilities
2. Do NOT infer medical truth - report what facilities claim
3. Text fields contain mentions, not verified facts
4. Use case-insensitive LIKE searches: LOWER(column) LIKE LOWER('%term%')

QUERY CONSTRUCTION RULES:
1. Return ONLY valid SQL - no explanations or markdown
2. Use COUNT(DISTINCT pk_unique_id) for counting hospitals
3. Use COUNT(DISTINCT doctor_npi) for counting doctors
4. For specialty/equipment searches, use the _text columns with LIKE
5. Exclude NULL and empty values in WHERE clauses
6. For state/regional queries, use address_stateOrRegion
7. For city queries, use address_city
8. Use GROUP BY for aggregations by state/city/department
9. ORDER BY counts DESC for "which state has most" questions
10. When joining tables, use pk_unique_id/unique_id with hospital_id
11. NEVER use full US state names in SQL.
12. Always normalize state references to USPS codes.
13. When unsure, prefer USPS code over full name.


EXAMPLES:
Question: "How many hospitals in California?"
SQL: SELECT COUNT(DISTINCT pk_unique_id) FROM hospitals 
WHERE address_stateOrRegion = 'CA'

Question: "Which state has the most hospitals?"
SQL: SELECT address_stateOrRegion, COUNT(DISTINCT pk_unique_id) as hospital_count 
FROM hospitals 
WHERE address_stateOrRegion IS NOT NULL 
AND address_stateOrRegion != '' 
GROUP BY address_stateOrRegion 
ORDER BY hospital_count DESC

Question: "List hospitals offering cardiology in California"
SQL: SELECT name, address_city, address_stateOrRegion, capability_text 
FROM hospitals 
WHERE address_stateOrRegion = 'CA'
AND (LOWER(specialties_text) LIKE '%cardiology%' 
     OR LOWER(capability_text) LIKE '%cardiology%')

Question: "How many cardiologists work in Texas hospitals?"
SQL: SELECT COUNT(DISTINCT d.doctor_npi) 
FROM doctors d 
JOIN hospital_doctor_mapping m ON d.doctor_npi = m.doctor_npi 
JOIN hospitals h ON m.hospital_id = h.pk_unique_id 
WHERE h.address_stateOrRegion = 'TX' 
AND LOWER(d.specialty) LIKE '%cardiology%'

USER QUESTION:
{question}

Return ONLY the SQL query:"""
        
        response = self.llm.invoke(prompt)
        sql = response.content.strip()
        
        # Clean up SQL
        sql = sql.replace("```sql", "").replace("```", "").strip()
        if sql.endswith(";"):
            sql = sql[:-1]
        
        return sql
    
    def execute_query(self, sql: str) -> Dict[str, Any]:
        """Execute SQL query and return results."""
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query(sql, conn)
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
            state: AppState dictionary
            
        Returns:
            Partial state update
        """
        user_question = state["messages"][-1].content
        
        # Generate SQL
        sql = self.generate_sql(user_question)
        
        # Execute query
        result = self.execute_query(sql)
        
        # Prepare citations
        citations = []
        if result["success"] and result["row_count"] > 0:
            citations.append({
                "agent": "SQLAgent",
                "source": "US Gov Dataset",
                "query": sql,
                "rows_analyzed": result["row_count"]
            })
        
        return {
            "sql_result": result,
            "citations": state.get("citations", []) + citations,
            "errors": state.get("errors", []) + (
                [f"SQL Error: {result['error']}"] if not result["success"] else []
            )
        }
