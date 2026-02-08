"""
GeoAgent - Geospatial analysis agent for US healthcare facilities
"""

import math
import pandas as pd
from typing import Dict, Any, List
from enhanced_state import AppState
from config import Config


class GeoAgent:
    """Geospatial analysis for US healthcare facilities.
    GEOGRAPHIC DATA RULES:

    - address_stateOrRegion stores USPS 2-letter codes ONLY.
    - All geographic comparisons MUST use USPS codes.
    - If a user mentions a full state name, convert it to USPS before filtering.
    - Do not assume city → state mappings unless explicitly stated.
    - For proximity analysis, use city and state together when possible.
    - Never use full state names in outputs or internal reasoning.
    - Always normalize state references to USPS codes in SQL queries.
    - When unsure, prefer USPS code over full name for consistency.

    """
    
    def __init__(self):
        self.llm = Config.get_llm()
        
        # US state abbreviations for parsing
        self.us_states = {
            'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas',
            'CA': 'California', 'CO': 'Colorado', 'CT': 'Connecticut',
            'DE': 'Delaware', 'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii',
            'ID': 'Idaho', 'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa',
            'KS': 'Kansas', 'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine',
            'MD': 'Maryland', 'MA': 'Massachusetts', 'MI': 'Michigan',
            'MN': 'Minnesota', 'MS': 'Mississippi', 'MO': 'Missouri',
            'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada',
            'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico',
            'NY': 'New York', 'NC': 'North Carolina', 'ND': 'North Dakota',
            'OH': 'Ohio', 'OK': 'Oklahoma', 'OR': 'Oregon', 'PA': 'Pennsylvania',
            'RI': 'Rhode Island', 'SC': 'South Carolina', 'SD': 'South Dakota',
            'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah', 'VT': 'Vermont',
            'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia',
            'WI': 'Wisconsin', 'WY': 'Wyoming', 'DC': 'District of Columbia'
        }
    
    def __call__(self, state: AppState) -> Dict:
        """
        Perform geospatial analysis.
        
        Args:
            state: Current application state
            
        Returns:
            Partial state update with geo results
        """
        print("\n🗺️  GeoAgent: Performing geospatial analysis...")
        
        # Validate state
        if state is None:
            print("⚠️  State is None - initializing empty state")
            state = {}
        
        # Load facility data
        try:
            facilities_df = self._load_facilities(state)
        except Exception as e:
            print(f"❌ Error loading facilities: {e}")
            return {
                "geo_result": {"success": False, "error": f"Failed to load data: {str(e)}"},
                "analytics_executed": state.get("analytics_executed", []) + ["GeoAgent"]
            }
        
        if facilities_df is None or len(facilities_df) == 0:
            print("⚠️  No facility data available")
            return {
                "geo_result": {"success": False, "error": "No facility data"},
                "analytics_executed": state.get("analytics_executed", []) + ["GeoAgent"]
            }
        
        # Determine analysis type from question
        messages = state.get("messages", [])
        if not messages:
            print("⚠️  No messages in state")
            return {
                "geo_result": {"success": False, "error": "No user question"},
                "analytics_executed": state.get("analytics_executed", []) + ["GeoAgent"]
            }
        
        user_question = messages[-1].content.lower()
        
        if "within" in user_question and ("km" in user_question or "miles" in user_question):
            result = self._proximity_analysis(user_question, facilities_df)
        elif "cold spot" in user_question or "gap" in user_question or "underserved" in user_question:
            result = self._cold_spot_analysis(user_question, facilities_df)
        else:
            result = self._general_distribution(facilities_df)
        
        print(f"✓ Geospatial analysis complete")
        
        # Update citations
        citations = state.get("citations", []).copy() if state.get("citations") else []
        if result.get("success"):
            citations.append({
                "agent": "GeoAgent",
                "source": "US Gov Dataset",
                "locations_analyzed": result.get("count", 0),
                "analysis_type": result.get("type")
            })
        
        return {
            "geo_result": result,
            "citations": citations,
            "analytics_executed": state.get("analytics_executed", []) + ["GeoAgent"]
        }
    
    def _load_facilities(self, state: AppState) -> pd.DataFrame:
        """Load facility data from state or database."""
        
        # Handle None state
        if state is None:
            state = {}
        
        # Check for counterfactual simulation
        counterfactual = state.get("counterfactual_state")
        if counterfactual and isinstance(counterfactual, dict) and counterfactual.get("is_active"):
            # Merge real and simulated facilities
            return self._merge_simulated_facilities(state)
        
        # Try SQL result
        sql_result = state.get("sql_result")
        if sql_result and isinstance(sql_result, dict) and sql_result.get("success"):
            data = sql_result.get("data")
            if data is not None:
                return data
        
        # Load from CSV
        try:
            import os
            csv_path = Config.HOSPITALS_CSV
            if os.path.exists(csv_path):
                return pd.read_csv(csv_path)
        except Exception as e:
            print(f"⚠️  Could not load facility data: {e}")
        
        return None
    
    def _merge_simulated_facilities(self, state: AppState) -> pd.DataFrame:
        """Merge real facilities with simulated ones."""
        # Load real facilities
        real_df = self._load_facilities({**state, "counterfactual_state": {"is_active": False}})
        
        # For now, just return real facilities
        # Full implementation would add simulated facilities to the dataframe
        return real_df
    
    def _proximity_analysis(self, question: str, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze facilities within a radius of a location."""
        
        # Extract location (state or city)
        target_state = self._extract_state(question)
        target_city = self._extract_city(question)
        
        # Filter facilities by location
        if target_state:
            nearby = df[df["address_stateOrRegion"] == target_state]
        elif target_city:
            nearby = df[df["address_city"].str.contains(target_city, case=False, na=False)]
        else:
            # Default to all facilities
            nearby = df.head(50)
        
        facilities = []
        for _, row in nearby.head(20).iterrows():
            facilities.append({
                "unique_id": row.get("pk_unique_id"),
                "name": row.get("name"),
                "city": row.get("address_city"),
                "state": row.get("address_stateOrRegion"),
                "specialties": row.get("capability_text", ""),
                "equipment": row.get("equipment_text", "")
            })
        
        location_desc = target_city if target_city else (self.us_states.get(target_state, target_state) if target_state else "specified location")
        
        return {
            "success": True,
            "type": "proximity",
            "center": location_desc,
            "count": len(facilities),
            "facilities": facilities
        }
    
    def _cold_spot_analysis(self, question: str, df: pd.DataFrame) -> Dict[str, Any]:
        """Identify geographic cold spots (areas without services)."""
        
        # Get all states
        states = df["address_stateOrRegion"].value_counts()
        
        # Identify states with few facilities
        cold_spots = []
        threshold = states.median() * 0.5  # States with <50% of median
        
        for state, count in states.items():
            if count < threshold and pd.notna(state) and state != '':
                state_name = self.us_states.get(state, state)
                cold_spots.append({
                    "state": state,
                    "state_name": state_name,
                    "facility_count": int(count),
                    "severity": "high" if count < threshold * 0.5 else "moderate"
                })
        
        return {
            "success": True,
            "type": "cold_spots",
            "count": len(cold_spots),
            "cold_spots": cold_spots,
            "threshold": threshold
        }
    
    def _general_distribution(self, df: pd.DataFrame) -> Dict[str, Any]:
        """General geographic distribution analysis."""
        
        state_counts = df["address_stateOrRegion"].value_counts().to_dict()
        
        # Convert state codes to full names
        state_distribution = {}
        for state_code, count in state_counts.items():
            if pd.notna(state_code) and state_code != '':
                state_name = self.us_states.get(state_code, state_code)
                state_distribution[state_name] = int(count)
        
        facilities = []
        for _, row in df.head(20).iterrows():
            state_code = row.get("address_stateOrRegion", "")
            facilities.append({
                "unique_id": row.get("pk_unique_id"),
                "name": row.get("name"),
                "city": row.get("address_city"),
                "state": self.us_states.get(state_code, state_code)
            })
        
        return {
            "success": True,
            "type": "distribution",
            "count": len(df),
            "state_distribution": state_distribution,
            "facilities": facilities
        }
    
    def _extract_state(self, question: str) -> str:
        """Extract US state from question."""
        question_upper = question.upper()
        
        # Check for state codes
        for code in self.us_states.keys():
            if f" {code} " in f" {question_upper} " or f" {code}," in f" {question_upper} ":
                return code
        
        # Check for state names
        for code, name in self.us_states.items():
            if name.lower() in question.lower():
                return code
        
        return None
    
    def _extract_city(self, question: str) -> str:
        """Extract city name from question (simple heuristic)."""
        # Common US cities
        cities = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix", 
                 "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose",
                 "Austin", "Jacksonville", "San Francisco", "Seattle", "Denver",
                 "Boston", "Portland", "Las Vegas", "Miami", "Atlanta"]
        
        for city in cities:
            if city.lower() in question.lower():
                return city
        
        return None