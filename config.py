"""
Enhanced Configuration for Healthcare Agent System
Supports multiple LLM providers and external search APIs
Adapted for US Healthcare Dataset
"""

import os
from dotenv import load_dotenv
from typing import Optional

# Load environment variables
load_dotenv()


class Config:
    """Centralized configuration for Healthcare Agent system."""
    
    # ==================== LLM CONFIGURATION ====================
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()
    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o")
    LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0"))
    
    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    
    # ==================== EMBEDDING CONFIGURATION ====================
    EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "openai").lower()
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    
    # ==================== EXTERNAL SEARCH APIs ====================
    SERP_API_KEY = os.getenv("SERP_API_KEY")  # Google SERP API
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")  # Tavily Search API
    
    # ==================== DATA PATHS ====================
    HOSPITALS_CSV = os.getenv("HOSPITALS_CSV", "/mnt/user-data/uploads/us_healthcare_data_hospitals.csv")
    DOCTORS_CSV = os.getenv("DOCTORS_CSV", "/mnt/user-data/uploads/us_healthcare_data_doctors.csv")
    MAPPING_CSV = os.getenv("MAPPING_CSV", "/mnt/user-data/uploads/us_healthcare_data_hospital_doctor_mapping.csv")
    DEPT_SUMMARY_CSV = os.getenv("DEPT_SUMMARY_CSV", "/mnt/user-data/uploads/us_healthcare_data_department_summary.csv")
    DB_PATH = os.getenv("DB_PATH", "/home/claude/us_healthcare.db")
    
    # ==================== ANALYTICS CONFIGURATION ====================
    ENABLE_EXTERNAL_VERIFICATION = os.getenv("ENABLE_EXTERNAL_VERIFICATION", "false").lower() == "true"
    CONTRADICTION_CLUSTER_THRESHOLD = int(os.getenv("CONTRADICTION_CLUSTER_THRESHOLD", "10"))
    REACHABILITY_WEIGHT_GEOGRAPHIC = float(os.getenv("REACHABILITY_WEIGHT_GEOGRAPHIC", "0.5"))
    REACHABILITY_WEIGHT_CAPABILITY = float(os.getenv("REACHABILITY_WEIGHT_CAPABILITY", "0.5"))
    
    @classmethod
    def get_llm(cls):
        """Get configured LLM instance."""
        provider = cls.LLM_PROVIDER
        
        if provider == "openai":
            from langchain_openai import ChatOpenAI
            if not cls.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY not set")
            return ChatOpenAI(
                model=cls.LLM_MODEL,
                temperature=cls.LLM_TEMPERATURE,
                api_key=cls.OPENAI_API_KEY
            )
        
        elif provider in ["google", "gemini"]:
            from langchain_google_genai import ChatGoogleGenerativeAI
            if not cls.GOOGLE_API_KEY:
                raise ValueError("GOOGLE_API_KEY not set")
            return ChatGoogleGenerativeAI(
                model=cls.LLM_MODEL,
                temperature=cls.LLM_TEMPERATURE,
                google_api_key=cls.GOOGLE_API_KEY
            )
        
        elif provider == "groq":
            from langchain_groq import ChatGroq
            if not cls.GROQ_API_KEY:
                raise ValueError("GROQ_API_KEY not set")
            return ChatGroq(
                model=cls.LLM_MODEL,
                temperature=cls.LLM_TEMPERATURE,
                api_key=cls.GROQ_API_KEY
            )
        
        elif provider == "anthropic":
            from langchain_anthropic import ChatAnthropic
            if not cls.ANTHROPIC_API_KEY:
                raise ValueError("ANTHROPIC_API_KEY not set")
            return ChatAnthropic(
                model=cls.LLM_MODEL,
                temperature=cls.LLM_TEMPERATURE,
                api_key=cls.ANTHROPIC_API_KEY
            )
        
        else:
            raise ValueError(f"Unknown LLM provider: {provider}")
    
    @classmethod
    def validate_config(cls):
        """Validate configuration."""
        print("\n" + "="*60)
        print("HEALTHCARE AGENT - CONFIGURATION VALIDATION")
        print("="*60)
        
        # Check LLM provider
        provider = cls.LLM_PROVIDER
        print(f"\nLLM Provider: {provider}")
        print(f"LLM Model: {cls.LLM_MODEL}")
        
        # Check API keys
        if provider == "openai" and not cls.OPENAI_API_KEY:
            raise ValueError("❌ OPENAI_API_KEY not set")
        elif provider in ["google", "gemini"] and not cls.GOOGLE_API_KEY:
            raise ValueError("❌ GOOGLE_API_KEY not set")
        elif provider == "groq" and not cls.GROQ_API_KEY:
            raise ValueError("❌ GROQ_API_KEY not set")
        elif provider == "anthropic" and not cls.ANTHROPIC_API_KEY:
            raise ValueError("❌ ANTHROPIC_API_KEY not set")
        
        print(f"✓ API key configured for {provider}")
        
        # Check embedding configuration
        print(f"\nEmbedding Provider: {cls.EMBEDDING_PROVIDER}")
        print(f"Embedding Model: {cls.EMBEDDING_MODEL}")
        
        # Check data paths
        for csv_name, csv_path in [
            ("Hospitals", cls.HOSPITALS_CSV),
            ("Doctors", cls.DOCTORS_CSV),
            ("Mapping", cls.MAPPING_CSV),
            ("Department Summary", cls.DEPT_SUMMARY_CSV)
        ]:
            if os.path.exists(csv_path):
                print(f"✓ {csv_name} CSV: {csv_path}")
            else:
                print(f"⚠️  {csv_name} CSV not found: {csv_path}")
        
        # Check external search APIs (optional)
        if cls.ENABLE_EXTERNAL_VERIFICATION:
            if cls.SERP_API_KEY:
                print("✓ SERP API key configured")
            if cls.TAVILY_API_KEY:
                print("✓ Tavily API key configured")
            if not cls.SERP_API_KEY and not cls.TAVILY_API_KEY:
                print("⚠️  External verification enabled but no search API keys found")
        
        print("\n" + "="*60 + "\n")
