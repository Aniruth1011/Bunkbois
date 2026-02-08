"""
Vector Agent for semantic search over facility descriptions and services.
OPTIMIZED VERSION - API-based embeddings only (no local models).
"""

import os
import json
from typing import Dict, Any, List
import pandas as pd
import chromadb
from chromadb.config import Settings
from config import Config


class VectorAgent:
    """
    Vector search agent for semantic queries over facility text fields.
    Uses ChromaDB with API-based embeddings ONLY (OpenAI or Google).
    """
    
    def __init__(self, csv_path: str = None):
        self.csv_path = csv_path or Config.HOSPITALS_CSV
        self.llm = Config.get_llm()
        
        # Initialize embedding function based on config (API ONLY)
        self.embedding_function = self._get_embedding_function()
        
        # Initialize ChromaDB
        self.chroma_client = chromadb.Client(Settings(
            anonymized_telemetry=False,
            allow_reset=True
        ))
        
        # Load or create vector store
        self._initialize_vector_store()
    
    def _get_embedding_function(self):
        """Get API-based embedding function (no local models)."""
        embedding_provider = Config.EMBEDDING_PROVIDER
        
        if embedding_provider == "openai" or embedding_provider == "groq":
            # OpenAI embeddings (also used when Groq LLM is selected)
            if not Config.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY required for embeddings")
            
            from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
            print(f"✓ Using OpenAI embeddings: {Config.EMBEDDING_MODEL}")
            return OpenAIEmbeddingFunction(
                api_key=Config.OPENAI_API_KEY,
                model_name=Config.EMBEDDING_MODEL
            )
        
        elif embedding_provider in ["google", "gemini"]:
            # Google Generative AI embeddings
            if not Config.GOOGLE_API_KEY:
                raise ValueError("GOOGLE_API_KEY required for embeddings")
            
            from chromadb.utils.embedding_functions import GoogleGenerativeAiEmbeddingFunction
            print(f"✓ Using Google embeddings: {Config.EMBEDDING_MODEL}")
            return GoogleGenerativeAiEmbeddingFunction(
                api_key=Config.GOOGLE_API_KEY,
                model_name=Config.EMBEDDING_MODEL
            )
        
        else:
            raise ValueError(
                f"Unknown embedding provider: {embedding_provider}. "
                f"Must be 'openai' or 'google'. "
                f"Local embeddings (sentence-transformers) are not supported in this optimized version."
            )
    
    def _initialize_vector_store(self):
        """Initialize or load the vector store with facility data."""
        collection_name = "facilities"
        
        try:
            # Try to get existing collection
            self.collection = self.chroma_client.get_collection(
                name=collection_name,
                embedding_function=self.embedding_function
            )
            print(f"✓ Loaded existing vector store with {self.collection.count()} documents")
        except:
            # Create new collection
            self.collection = self.chroma_client.create_collection(
                name=collection_name,
                embedding_function=self.embedding_function,
                metadata={"hnsw:space": "cosine"}
            )
            
            # Load and index data
            self._index_facilities()
    
    def _index_facilities(self):
        """Index facility data into vector store."""
        print("📦 Indexing facilities (this may take a moment with API embeddings)...")
        df = pd.read_csv(self.csv_path)
        
        documents = []
        metadatas = []
        ids = []
        
        for idx, row in df.iterrows():
            # Create rich text representation
            doc_text = self._create_document_text(row)
            
            if doc_text.strip():
                documents.append(doc_text)
                
                # Store metadata
                metadatas.append({
                    "facility_id": str(row.get("unique_id", idx)),
                    "name": str(row.get("name", "Unknown")),
                    "city": str(row.get("address_city", "")),
                    "region": str(row.get("address_stateOrRegion", "")),
                    "facility_type": str(row.get("facilityTypeId", "")),
                    "operator_type": str(row.get("operatorTypeId", ""))
                })
                
                ids.append(f"facility_{idx}")
        
        # Add to collection in batches (smaller batches for API calls)
        batch_size = 50  # Smaller batches for API rate limits
        total_batches = (len(documents) + batch_size - 1) // batch_size
        
        for i in range(0, len(documents), batch_size):
            batch_num = (i // batch_size) + 1
            print(f"  Processing batch {batch_num}/{total_batches}...")
            
            batch_docs = documents[i:i+batch_size]
            batch_meta = metadatas[i:i+batch_size]
            batch_ids = ids[i:i+batch_size]
            
            try:
                self.collection.add(
                    documents=batch_docs,
                    metadatas=batch_meta,
                    ids=batch_ids
                )
            except Exception as e:
                print(f"  ⚠️  Batch {batch_num} failed: {e}")
                # Continue with next batch
                continue
        
        print(f"✓ Indexed {len(documents)} facilities into vector store")
    
    def _create_document_text(self, row: pd.Series) -> str:
        """Create searchable text document from facility row."""
        parts = []
        
        # Facility name and type
        if pd.notna(row.get("name")):
            parts.append(f"Facility: {row['name']}")
        
        if pd.notna(row.get("facilityTypeId")):
            parts.append(f"Type: {row['facilityTypeId']}")
        
        # Location
        location_parts = []
        for col in ["address_city", "address_stateOrRegion", "address_country"]:
            if pd.notna(row.get(col)) and str(row[col]).strip():
                location_parts.append(str(row[col]))
        if location_parts:
            parts.append(f"Location: {', '.join(location_parts)}")
        
        # Specialties
        if pd.notna(row.get("specialties")):
            specialties = self._extract_json_list(row["specialties"])
            if specialties:
                parts.append(f"Specialties: {', '.join(specialties)}")
        
        # Procedures
        if pd.notna(row.get("procedure")):
            procedures = self._extract_json_list(row["procedure"])
            if procedures:
                parts.append(f"Procedures: {', '.join(procedures)}")
        
        # Equipment
        if pd.notna(row.get("equipment")):
            equipment = self._extract_json_list(row["equipment"])
            if equipment:
                parts.append(f"Equipment: {', '.join(equipment)}")
        
        # Capabilities
        if pd.notna(row.get("capability")):
            capabilities = self._extract_json_list(row["capability"])
            if capabilities:
                parts.append(f"Capabilities: {', '.join(capabilities)}")
        
        # Description
        if pd.notna(row.get("description")) and str(row["description"]).strip():
            parts.append(f"Description: {row['description']}")
        
        return "\n".join(parts)
    
    def _extract_json_list(self, json_str: str) -> List[str]:
        """Extract list from JSON string."""
        try:
            if isinstance(json_str, str):
                data = json.loads(json_str)
                if isinstance(data, list):
                    return [str(item) for item in data if item]
        except:
            pass
        return []
    
    def search(self, query: str, n_results: int = 10, filters: Dict = None) -> Dict[str, Any]:
        """
        Perform semantic search over facility documents.
        
        Args:
            query: Natural language search query
            n_results: Number of results to return
            filters: Optional metadata filters
            
        Returns:
            Dictionary with search results
        """
        try:
            # Enhance query with LLM (optional - can be disabled for speed)
            # enhanced_query = self._enhance_query(query)
            enhanced_query = query  # Skip enhancement for speed
            
            # Prepare where clause for filtering
            where = self._build_where_clause(filters) if filters else None
            
            # Perform search
            results = self.collection.query(
                query_texts=[enhanced_query],
                n_results=n_results,
                where=where
            )
            
            # Format results
            formatted_results = []
            if results and results['documents'] and results['documents'][0]:
                for i in range(len(results['documents'][0])):
                    formatted_results.append({
                        "document": results['documents'][0][i],
                        "metadata": results['metadatas'][0][i],
                        "distance": results['distances'][0][i] if 'distances' in results else None
                    })
            
            return {
                "success": True,
                "query": query,
                "enhanced_query": enhanced_query,
                "results": formatted_results,
                "count": len(formatted_results)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "query": query
            }
    
    def _enhance_query(self, query: str) -> str:
        """Use LLM to enhance search query with medical context."""
        prompt = f"""Given this healthcare facility search query, expand it with relevant medical synonyms and related terms.

Query: {query}

Return ONLY the enhanced search query with synonyms and related terms.
Keep it concise (1-2 sentences max).

Examples:
Query: "dialysis services"
Enhanced: "dialysis hemodialysis peritoneal dialysis kidney treatment renal care"

Query: "eye surgery"
Enhanced: "ophthalmology eye surgery cataract glaucoma retinal surgery LASIK corneal procedures"

Enhanced query:"""
        
        try:
            response = self.llm.invoke(prompt)
            enhanced = response.content.strip()
            # If enhancement is too long or looks wrong, use original
            if len(enhanced) > 200 or '\n' in enhanced:
                return query
            return enhanced
        except:
            return query
    
    def _build_where_clause(self, filters: Dict) -> Dict:
        """Build ChromaDB where clause from filters."""
        where_conditions = {}
        
        if "facility_type" in filters:
            where_conditions["facility_type"] = filters["facility_type"]
        
        if "city" in filters:
            where_conditions["city"] = filters["city"]
        
        if "region" in filters:
            where_conditions["region"] = filters["region"]
        
        return where_conditions if where_conditions else None
    
    def __call__(self, state: Dict) -> Dict:
        """
        LangGraph node interface.
        
        Args:
            state: AppState dictionary
            
        Returns:
            Partial state update
        """
        user_question = state["messages"][-1].content
        
        # Extract filters from question if needed
        filters = self._extract_filters_from_question(user_question)
        
        # Perform search
        result = self.search(user_question, n_results=10, filters=filters)
        
        # Prepare citations
        citations = []
        if result["success"] and result["count"] > 0:
            citations.append({
                "agent": "VectorAgent",
                "query": result["enhanced_query"],
                "documents_found": result["count"]
            })
        
        return {
            "vector_result": result,
            "citations": state.get("citations", []) + citations,
            "errors": state.get("errors", []) + (
                [f"Vector Search Error: {result['error']}"] if not result["success"] else []
            )
        }
    
    def _extract_filters_from_question(self, question: str) -> Dict:
        """Extract location/type filters from natural language question."""
        filters = {}
        question_lower = question.lower()
        
        # Check for facility type mentions
        if "hospital" in question_lower:
            filters["facility_type"] = "hospital"
        elif "clinic" in question_lower:
            filters["facility_type"] = "clinic"
        
        # Could add more sophisticated location extraction here
        
        return filters
