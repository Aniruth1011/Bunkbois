"""
ExternalVerificationAgent - Verifies critical medical claims using external search APIs
Uses SERP API and Tavily API to validate facility claims and fill data gaps
"""

import requests
from typing import Dict, Any, List, Optional
from enhanced_state import AppState, AnalyticsResult    
from config import Config


class ExternalVerificationAgent:
    """
    Verifies critical medical claims using external search APIs.
    Handles two scenarios:
    1. Verification of critical mismatches (does X really require Y?)
    2. Filling data gaps when internal data is insufficient
VERIFICATION CONTEXT:

- Internal facility data uses USPS state codes.
- External sources may use full names; normalize before comparison.
- Do not reject claims due to naming format differences alone.


    """
    
    def __init__(self):
        self.llm = Config.get_llm()
        self.serp_api_key = Config.SERP_API_KEY
        self.tavily_api_key = Config.TAVILY_API_KEY
        self.enable_verification = Config.ENABLE_EXTERNAL_VERIFICATION
        
        # Determine which API to use
        self.use_serp = bool(self.serp_api_key)
        self.use_tavily = bool(self.tavily_api_key)
    
    def __call__(self, state: AppState) -> Dict:
        """
        Verify critical claims using external search.
        
        Args:
            state: Current application state
            
        Returns:
            Partial state update with verification results
        """
        print("\n🔍 ExternalVerificationAgent: Verifying claims with external sources...")
        
        # Check if verification is enabled
        if not self.enable_verification:
            print("⚠️  External verification is disabled in config")
            return {
                "external_search_results": {},
                "analytics_executed": state.get("analytics_executed", []) + ["ExternalVerificationAgent"]
            }
        
        if not self.use_serp and not self.use_tavily:
            print("⚠️  No external search API keys configured")
            return {
                "external_search_results": {},
                "analytics_executed": state.get("analytics_executed", []) + ["ExternalVerificationAgent"]
            }
        
        # Get items needing verification
        verification_needed = state.get("verification_needed", [])
        
        # Check if SQL/Vector results have insufficient data
        insufficient_data = self._check_insufficient_data(state)
        
        if not verification_needed and not insufficient_data:
            print("✓ No verification needed - internal data is sufficient")
            return {
                "external_search_results": {},
                "analytics_executed": state.get("analytics_executed", []) + ["ExternalVerificationAgent"]
            }
        
        # Perform verifications
        verification_results = {}
        
        # Verify critical mismatches
        for item in verification_needed[:5]:  # Limit to top 5 to avoid excessive API calls
            result = self._verify_claim(
                procedure=item["procedure"],
                missing_infrastructure=item["missing_infra"]
            )
            verification_results[item["id"]] = result
        
        # Fill data gaps if needed
        if insufficient_data:
            gap_results = self._fill_data_gaps(state)
            verification_results["data_gap_filling"] = gap_results
        
        # Generate summary
        verified_count = sum(1 for r in verification_results.values() 
                           if isinstance(r, dict) and r.get("verified"))
        refuted_count = sum(1 for r in verification_results.values() 
                          if isinstance(r, dict) and r.get("refuted"))
        
        summary = (
            f"Verified {len(verification_results)} claims using external sources. "
            f"{verified_count} confirmed, {refuted_count} refuted."
        )
        
        print(f"✓ Verification complete: {summary}")
        
        # Update citations
        citations = state.get("citations", []).copy()
        citations.append({
            "agent": "ExternalVerificationAgent",
            "claims_verified": len(verification_results),
            "sources": "SERP API" if self.use_serp else "Tavily API"
        })
        
        return {
            "external_search_results": verification_results,
            "analytics_results": {
                **state.get("analytics_results", {}),
                "external_verification": {
                    "agent": "ExternalVerificationAgent",
                    "claims_verified": len(verification_results),
                    "confirmed": verified_count,
                    "refuted": refuted_count,
                    "summary": summary,
                    "metadata": {
                        "api_used": "SERP" if self.use_serp else "Tavily"
                    }
                }
            },
            "citations": citations,
            "analytics_executed": state.get("analytics_executed", []) + ["ExternalVerificationAgent"]
        }
    
    def _verify_claim(
        self, 
        procedure: str, 
        missing_infrastructure: List[str]
    ) -> Dict[str, Any]:
        """
        Verify if a medical procedure really requires certain infrastructure.
        
        Args:
            procedure: Medical procedure/capability
            missing_infrastructure: Infrastructure claimed to be missing
            
        Returns:
            Verification result with evidence
        """
        # Construct search query
        infra_items = ", ".join(missing_infrastructure[:3])  # Limit to top 3
        query = f"Does {procedure} require {infra_items} medical equipment standards"
        
        print(f"  🔍 Verifying: {query}")
        
        # Perform search
        if self.use_tavily:
            search_results = self._search_tavily(query)
        else:
            search_results = self._search_serp(query)
        
        if not search_results:
            return {
                "verified": None,
                "evidence": "No external evidence found",
                "confidence": "low"
            }
        
        # Use LLM to analyze search results
        analysis = self._analyze_search_results(
            query=query,
            results=search_results,
            procedure=procedure,
            missing_infrastructure=missing_infrastructure
        )
        
        return analysis
    
    def _check_insufficient_data(self, state: AppState) -> bool:
        """
        Check if internal data sources returned insufficient information.
        
        Args:
            state: Current application state
            
        Returns:
            True if data is insufficient
        """
        sql_result = state.get("sql_result", {})
        vector_result = state.get("vector_result", {})
        geo_result = state.get("geo_result", {})
        
        # Check SQL result
        if sql_result.get("success"):
            if sql_result.get("row_count", 0) == 0:
                return True
        
        # Check vector result
        if vector_result.get("success"):
            if vector_result.get("count", 0) == 0:
                return True
        
        # Check geo result
        if geo_result.get("success"):
            if geo_result.get("count", 0) == 0:
                return True
        
        # All queries returned some data
        return False
    
    def _fill_data_gaps(self, state: AppState) -> Dict[str, Any]:
        """
        Use external search to fill gaps in internal data.
        
        Args:
            state: Current application state
            
        Returns:
            Additional information from external sources
        """
        user_question = state["messages"][-1].content
        
        # Create search query to fill gaps
        query = f"{user_question} healthcare facilities United States statistics"
        
        print(f"  🔍 Filling data gaps: {query}")
        
        # Perform search
        if self.use_tavily:
            search_results = self._search_tavily(query)
        else:
            search_results = self._search_serp(query)
        
        if not search_results:
            return {
                "success": False,
                "message": "No external data found to fill gaps"
            }
        
        # Extract relevant information
        gap_fill_info = {
            "success": True,
            "sources": [],
            "key_findings": []
        }
        
        for result in search_results[:3]:  # Top 3 results
            gap_fill_info["sources"].append({
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "snippet": result.get("snippet", "")
            })
            
            if result.get("snippet"):
                gap_fill_info["key_findings"].append(result["snippet"])
        
        return gap_fill_info
    
    def _search_serp(self, query: str) -> List[Dict[str, Any]]:
        """
        Search using SERP API (Google Search).
        
        Args:
            query: Search query
            
        Returns:
            List of search results
        """
        try:
            url = "https://serpapi.com/search"
            params = {
                "q": query,
                "api_key": self.serp_api_key,
                "num": 5,  # Get top 5 results
                "engine": "google"
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            organic_results = data.get("organic_results", [])
            
            results = []
            for item in organic_results:
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "snippet": item.get("snippet", "")
                })
            
            return results
            
        except Exception as e:
            print(f"  ⚠️  SERP API error: {e}")
            return []
    
    def _search_tavily(self, query: str) -> List[Dict[str, Any]]:
        """
        Search using Tavily API (AI-optimized search).
        
        Args:
            query: Search query
            
        Returns:
            List of search results
        """
        try:
            url = "https://api.tavily.com/search"
            headers = {
                "Content-Type": "application/json"
            }
            payload = {
                "api_key": self.tavily_api_key,
                "query": query,
                "search_depth": "basic",
                "max_results": 5,
                "include_domains": [
                    "nih.gov", "cdc.gov", "cms.gov", "who.int", 
                    "mayoclinic.org", "hopkinsmedicine.org"
                ]  # Prefer authoritative medical sources
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            search_results = data.get("results", [])
            
            results = []
            for item in search_results:
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "snippet": item.get("content", "")
                })
            
            return results
            
        except Exception as e:
            print(f"  ⚠️  Tavily API error: {e}")
            return []
    
    def _analyze_search_results(
        self,
        query: str,
        results: List[Dict[str, Any]],
        procedure: str,
        missing_infrastructure: List[str]
    ) -> Dict[str, Any]:
        """
        Use LLM to analyze search results and determine verification status.
        
        Args:
            query: Original search query
            results: Search results from external API
            procedure: Medical procedure being verified
            missing_infrastructure: Infrastructure claimed to be missing
            
        Returns:
            Verification analysis
        """
        # Compile search results into context
        context = "\n\n".join([
            f"Source: {r['title']}\nURL: {r['url']}\nContent: {r['snippet']}"
            for r in results
        ])
        
        prompt = f"""You are a medical verification expert. Analyze these search results to verify a medical claim.

CLAIM TO VERIFY:
The procedure "{procedure}" requires the following infrastructure: {', '.join(missing_infrastructure)}

SEARCH RESULTS:
{context}

Based on these authoritative sources, determine:
1. Is the claim VERIFIED (the procedure does require this infrastructure)?
2. Is the claim REFUTED (the procedure does NOT require this infrastructure)?
3. Is there INSUFFICIENT evidence to determine?

Provide your analysis in this JSON format:
{{
    "verified": true/false/null,
    "refuted": true/false,
    "confidence": "high/medium/low",
    "evidence": "Brief summary of evidence from sources",
    "recommendation": "What this means for the facility"
}}

Return ONLY the JSON, no other text.

JSON:"""
        
        try:
            response = self.llm.invoke(prompt)
            content = response.content.strip()
            
            # Clean JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            import json
            analysis = json.loads(content)
            
            return analysis
            
        except Exception as e:
            print(f"  ⚠️  LLM analysis error: {e}")
            return {
                "verified": None,
                "refuted": False,
                "confidence": "low",
                "evidence": f"Error analyzing results: {str(e)}",
                "recommendation": "Manual review recommended"
            }