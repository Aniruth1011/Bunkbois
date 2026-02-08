#!/usr/bin/env python3
"""
Test script for US Healthcare Agent System
"""

import os
import sys

# Set up environment
if not os.path.exists('.env'):
    print("⚠️  No .env file found. Creating from template...")
    if os.path.exists('.env.example'):
        import shutil
        shutil.copy('.env.example', '.env')
        print("✓ Created .env file. Please edit it and add your OPENAI_API_KEY")
        print("\nAfter adding your API key, run this script again.\n")
        sys.exit(0)
    else:
        print("❌ No .env.example found!")
        sys.exit(1)

from config import Config
from enhanced_healthcare_agent import run_query

def main():
    """Run test queries."""
    
    print("\n" + "="*70)
    print("US HEALTHCARE AGENT - TEST SUITE")
    print("="*70)
    
    # Validate configuration
    try:
        Config.validate_config()
    except ValueError as e:
        print(f"\n❌ Configuration Error: {e}")
        print("\nPlease check your .env file and ensure:")
        print("1. OPENAI_API_KEY is set (or appropriate key for your LLM_PROVIDER)")
        print("2. Data file paths are correct")
        sys.exit(1)
    
    # Test queries
    test_queries = [
        "How many hospitals are in California?",
        "Which state has the most healthcare facilities?",
        "List hospitals offering cardiology services in Texas",
        "Which facilities claim neurosurgery but might lack ICU?",
        "Show me the distribution of hospitals across states"
    ]
    
    print("\nRunning test queries...\n")
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*70}")
        print(f"TEST QUERY {i}/{len(test_queries)}")
        print('='*70)
        
        try:
            response = run_query(query)
            print(f"\n✅ Query {i} completed successfully")
        except Exception as e:
            print(f"\n❌ Query {i} failed: {e}")
            import traceback
            traceback.print_exc()
        
        if i < len(test_queries):
            print(f"\n{'─'*70}\n")
    
    print("\n" + "="*70)
    print("TEST SUITE COMPLETE")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
