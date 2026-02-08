#!/usr/bin/env python3
"""
Interactive Demo for US Healthcare Agent System
"""

import os
import sys

# Check for .env file
if not os.path.exists('.env'):
    print("⚠️  No .env file found!")
    print("\nTo run this demo, you need to:")
    print("1. Copy .env.example to .env")
    print("2. Add your OPENAI_API_KEY to the .env file")
    print("\nRun: cp .env.example .env")
    print("Then edit .env and add your API key\n")
    sys.exit(1)

from config import Config
from enhanced_healthcare_agent3 import run_query


def print_header():
    """Print demo header."""
    print("\n" + "="*70)
    print("           US HEALTHCARE AGENT - INTERACTIVE DEMO")
    print("="*70)
    print("\nThis system analyzes US healthcare facility data from government")
    print("datasets using advanced AI agents.\n")
    print("Available Query Types:")
    print("  • Basic counts and filters (SQL)")
    print("  • Semantic search (Vector)")
    print("  • Geographic analysis (Geo)")
    print("  • Data quality analysis (Analytics)")
    print("  • Accessibility scoring (Reachability)")
    print("="*70 + "\n")


def demo_queries():
    """Run demo queries."""
    
    queries = [
        {
            "question": "How many hospitals are in California?",
            "type": "SQL Query",
            "description": "Simple count query using SQL Agent"
        },
        {
            "question": "Which state has the most healthcare facilities?",
            "type": "SQL Aggregation",
            "description": "Aggregation query with grouping"
        },
        {
            "question": "Which facilities claim neurosurgery but might lack ICU?",
            "type": "Data Quality Analysis",
            "description": "Skill-infrastructure mismatch detection"
        },
        {
            "question": "Show me the distribution of hospitals across states",
            "type": "Geographic Analysis",
            "description": "Geospatial distribution analysis"
        }
    ]
    
    for i, query_info in enumerate(queries, 1):
        print(f"\n{'='*70}")
        print(f"DEMO QUERY {i}: {query_info['type']}")
        print('='*70)
        print(f"Question: {query_info['question']}")
        print(f"Description: {query_info['description']}")
        print('─'*70 + "\n")
        
        try:
            response = run_query(query_info['question'])
            print(f"\n{'─'*70}")
            print("✅ Query completed successfully")
            
        except KeyboardInterrupt:
            print("\n\n⚠️  Demo interrupted by user")
            sys.exit(0)
            
        except Exception as e:
            print(f"\n❌ Query failed: {e}")
            import traceback
            traceback.print_exc()
        
        if i < len(queries):
            input("\n\nPress Enter to continue to next query...")


def interactive_mode():
    """Run interactive query mode."""
    print("\n" + "="*70)
    print("INTERACTIVE MODE")
    print("="*70)
    print("\nEnter your questions about US healthcare facilities.")
    print("Type 'quit' or 'exit' to end the session.\n")
    print("Example questions:")
    print("  • How many cardiologists work in Texas hospitals?")
    print("  • List hospitals offering emergency services in New York")
    print("  • Which states have the poorest cardiology coverage?")
    print("  • Identify data quality issues in surgical claims")
    print("="*70 + "\n")
    
    while True:
        try:
            question = input("\n💭 Your question: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!\n")
                break
            
            if not question:
                continue
            
            print()
            response = run_query(question)
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!\n")
            break
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()


def main():
    """Main demo function."""
    
    print_header()
    
    # Validate configuration
    try:
        Config.validate_config()
    except ValueError as e:
        print(f"\n❌ Configuration Error: {e}")
        print("\nPlease ensure:")
        print("1. .env file exists (copy from .env.example)")
        print("2. OPENAI_API_KEY is set in .env")
        print("3. Data files are in the correct location\n")
        sys.exit(1)
    
    # Ask user for mode
    print("Choose mode:")
    print("  1. Run demo queries (4 pre-configured examples)")
    print("  2. Interactive mode (ask your own questions)")
    print("  3. Exit")
    
    while True:
        choice = input("\nYour choice (1/2/3): ").strip()
        
        if choice == '1':
            demo_queries()
            print("\n" + "="*70)
            print("DEMO COMPLETE")
            print("="*70)
            print("\nYou can now:")
            print("  • Try interactive mode (run demo again and choose option 2)")
            print("  • View the system graph: python generate_graph.py")
            print("  • Read the README.md for more information\n")
            break
            
        elif choice == '2':
            interactive_mode()
            break
            
        elif choice == '3':
            print("\n👋 Goodbye!\n")
            sys.exit(0)
            
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!\n")
        sys.exit(0)
