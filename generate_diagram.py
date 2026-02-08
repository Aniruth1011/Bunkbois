#!/usr/bin/env python3
"""
Generate System Architecture Diagram for Healthcare Agent
Creates a visual flowchart showing all agents and their connections
"""

from graphviz import Digraph
import os


def generate_system_diagram():
    """Generate the complete system architecture diagram."""
    
    # Create a new directed graph
    dot = Digraph(comment='Healthcare Agent System Architecture')
    dot.attr(rankdir='TB', size='12,16')
    dot.attr('node', shape='box', style='rounded,filled', fontname='Arial')
    
    # Define color scheme
    colors = {
        'entry': '#E3F2FD',      # Light blue
        'routing': '#FFF9C4',    # Light yellow
        'core': '#C8E6C9',       # Light green
        'analytics': '#FFE0B2',  # Light orange
        'verification': '#F8BBD0', # Light pink
        'synthesis': '#D1C4E9'   # Light purple
    }
    
    # ==================== ENTRY POINT ====================
    dot.node('User', 'User Query', fillcolor=colors['entry'])
    
    # ==================== ROUTER ====================
    dot.node('IntentRouter', 'Intent Router\n(Classify Query Type)', fillcolor=colors['routing'])
    
    # ==================== CORE AGENTS ====================
    with dot.subgraph(name='cluster_core') as c:
        c.attr(label='Core Data Agents', style='filled', color='lightgrey')
        c.node('SQL', 'SQL Agent\n(Structured Queries)', fillcolor=colors['core'])
        c.node('Vector', 'Vector Agent\n(Semantic Search)', fillcolor=colors['core'])
        c.node('Geo', 'Geo Agent\n(Spatial Analysis)', fillcolor=colors['core'])
    
    # ==================== ANALYTICS ROUTER ====================
    dot.node('DataQualityRouter', 'Data Quality Router\n(Plan Analytics Pipeline)', fillcolor=colors['routing'])
    
    # ==================== ANALYTICS AGENTS ====================
    with dot.subgraph(name='cluster_analytics') as c:
        c.attr(label='Advanced Analytics Agents', style='filled', color='lightgrey')
        c.node('SkillInfra', 'Skill-Infrastructure Agent\n(Detect Mismatches)', fillcolor=colors['analytics'])
        c.node('Reachability', 'Reachability Agent\n(Compute Access Scores)', fillcolor=colors['analytics'])
        c.node('Contradiction', 'Contradiction Agent\n(Build Graph)', fillcolor=colors['analytics'])
        c.node('Desert', 'Desert Typology Agent\n(Classify Medical Deserts)', fillcolor=colors['analytics'])
        c.node('Counterfactual', 'Counterfactual Engine\n(What-If Scenarios)', fillcolor=colors['analytics'])
    
    # ==================== VERIFICATION AGENT ====================
    dot.node('Verification', 'External Verification Agent\n(Validate Claims via APIs)', fillcolor=colors['verification'])
    
    # ==================== SYNTHESIS ====================
    dot.node('ResponseGen', 'Response Generator\n(Synthesize Final Answer)', fillcolor=colors['synthesis'])
    dot.node('Output', 'Final Response', fillcolor=colors['entry'])
    
    # ==================== EDGES (FLOW) ====================
    
    # Entry to Router
    dot.edge('User', 'IntentRouter', label='Question')
    
    # Router to Core Agents
    dot.edge('IntentRouter', 'SQL', label='SQL Query')
    dot.edge('IntentRouter', 'Vector', label='Semantic Search')
    dot.edge('IntentRouter', 'Geo', label='Geo Analysis')
    
    # Core to Analytics Router
    dot.edge('SQL', 'DataQualityRouter', label='Results')
    dot.edge('Vector', 'DataQualityRouter', label='Results')
    dot.edge('Geo', 'DataQualityRouter', label='Results')
    
    # Analytics Router to Analytics Agents
    dot.edge('DataQualityRouter', 'SkillInfra', label='If: mismatch keywords')
    dot.edge('DataQualityRouter', 'Reachability', label='If: access keywords')
    dot.edge('DataQualityRouter', 'Contradiction', label='If: pattern keywords')
    dot.edge('DataQualityRouter', 'Desert', label='If: desert keywords')
    dot.edge('DataQualityRouter', 'Counterfactual', label='If: what-if keywords')
    
    # Analytics Dependencies
    dot.edge('SkillInfra', 'Contradiction', label='Mismatches', style='dashed')
    dot.edge('Geo', 'Reachability', label='Locations', style='dashed')
    dot.edge('Reachability', 'Desert', label='Scores', style='dashed')
    
    # Critical Findings to Verification
    dot.edge('SkillInfra', 'Verification', label='Critical Claims', color='red', style='bold')
    dot.edge('SQL', 'Verification', label='Insufficient Data', color='red', style='dashed')
    dot.edge('Vector', 'Verification', label='Insufficient Data', color='red', style='dashed')
    
    # All to Response Generator
    dot.edge('SQL', 'ResponseGen')
    dot.edge('Vector', 'ResponseGen')
    dot.edge('Geo', 'ResponseGen')
    dot.edge('SkillInfra', 'ResponseGen')
    dot.edge('Reachability', 'ResponseGen')
    dot.edge('Contradiction', 'ResponseGen')
    dot.edge('Desert', 'ResponseGen')
    dot.edge('Counterfactual', 'ResponseGen')
    dot.edge('Verification', 'ResponseGen', label='External Evidence', color='blue')
    
    # Final output
    dot.edge('ResponseGen', 'Output')
    
    # ==================== ADD LEGEND ====================
    with dot.subgraph(name='cluster_legend') as c:
        c.attr(label='Legend', style='filled', color='white')
        c.node('L1', 'Entry/Exit Points', fillcolor=colors['entry'], shape='box')
        c.node('L2', 'Routing Logic', fillcolor=colors['routing'], shape='box')
        c.node('L3', 'Core Data Agents', fillcolor=colors['core'], shape='box')
        c.node('L4', 'Analytics Agents', fillcolor=colors['analytics'], shape='box')
        c.node('L5', 'External Verification', fillcolor=colors['verification'], shape='box')
        c.node('L6', 'Response Synthesis', fillcolor=colors['synthesis'], shape='box')
        
        # Invisible edges to arrange vertically
        c.edge('L1', 'L2', style='invis')
        c.edge('L2', 'L3', style='invis')
        c.edge('L3', 'L4', style='invis')
        c.edge('L4', 'L5', style='invis')
        c.edge('L5', 'L6', style='invis')
    
    return dot


def generate_data_flow_diagram():
    """Generate data flow diagram showing state transformations."""
    
    dot = Digraph(comment='Data Flow Diagram')
    dot.attr(rankdir='LR', size='14,10')
    dot.attr('node', shape='cylinder', style='filled', fillcolor='#E1F5FE')
    
    # Data sources
    dot.node('CSV', 'CSV Files\n(Hospitals, Doctors,\nMapping, Departments)')
    dot.node('SQLite', 'SQLite Database')
    dot.node('ChromaDB', 'Vector Store\n(ChromaDB)')
    
    # Processing nodes
    dot.node('State', 'Application State\n(TypedDict)', shape='box', fillcolor='#FFF9C4')
    
    # Result stores
    dot.node('SQLResult', 'SQL Results', shape='note', fillcolor='#C8E6C9')
    dot.node('VectorResult', 'Vector Results', shape='note', fillcolor='#C8E6C9')
    dot.node('GeoResult', 'Geo Results', shape='note', fillcolor='#C8E6C9')
    dot.node('AnalyticsResults', 'Analytics Results', shape='note', fillcolor='#FFE0B2')
    dot.node('ExternalResults', 'External Search\nResults', shape='note', fillcolor='#F8BBD0')
    
    # Edges
    dot.edge('CSV', 'SQLite', label='Load on init')
    dot.edge('CSV', 'ChromaDB', label='Index on init')
    
    dot.edge('SQLite', 'SQLResult', label='Query')
    dot.edge('ChromaDB', 'VectorResult', label='Semantic search')
    
    dot.edge('SQLResult', 'State', label='Update')
    dot.edge('VectorResult', 'State', label='Update')
    dot.edge('GeoResult', 'State', label='Update')
    
    dot.edge('State', 'AnalyticsResults', label='Analytics\nPipeline')
    dot.edge('State', 'ExternalResults', label='External\nVerification')
    
    dot.edge('AnalyticsResults', 'State', label='Merge')
    dot.edge('ExternalResults', 'State', label='Merge')
    
    dot.edge('State', 'Response', label='Final synthesis', shape='box', fillcolor='#D1C4E9')
    
    return dot


def main():
    """Generate all diagrams."""
    
    output_dir = "/mnt/user-data/outputs"
    os.makedirs(output_dir, exist_ok=True)
    
    print("🎨 Generating Healthcare Agent System Diagrams...\n")
    
    # Generate main system architecture diagram
    print("📊 Creating system architecture diagram...")
    system_diagram = generate_system_diagram()
    
    # Save in multiple formats
    system_diagram.render(
        f'{output_dir}/system_architecture',
        format='png',
        cleanup=True
    )
    system_diagram.render(
        f'{output_dir}/system_architecture',
        format='pdf',
        cleanup=True
    )
    
    # Also save the source .dot file
    system_diagram.save(f'{output_dir}/system_architecture.dot')
    
    print(f"  ✅ Saved: {output_dir}/system_architecture.png")
    print(f"  ✅ Saved: {output_dir}/system_architecture.pdf")
    print(f"  ✅ Saved: {output_dir}/system_architecture.dot")
    
    # Generate data flow diagram
    print("\n📊 Creating data flow diagram...")
    data_flow = generate_data_flow_diagram()
    
    data_flow.render(
        f'{output_dir}/data_flow',
        format='png',
        cleanup=True
    )
    data_flow.render(
        f'{output_dir}/data_flow',
        format='pdf',
        cleanup=True
    )
    data_flow.save(f'{output_dir}/data_flow.dot')
    
    print(f"  ✅ Saved: {output_dir}/data_flow.png")
    print(f"  ✅ Saved: {output_dir}/data_flow.pdf")
    print(f"  ✅ Saved: {output_dir}/data_flow.dot")
    
    print("\n" + "="*60)
    print("✅ DIAGRAMS GENERATED SUCCESSFULLY!")
    print("="*60)
    print(f"\nOutput files in: {output_dir}/")
    print("  • system_architecture.png - Main system flow")
    print("  • system_architecture.pdf - Main system flow (PDF)")
    print("  • data_flow.png - Data transformations")
    print("  • data_flow.pdf - Data transformations (PDF)")
    print("  • *.dot files - Source GraphViz files")
    print("\nYou can view the PNG files or open the PDFs for high resolution.\n")


if __name__ == "__main__":
    try:
        main()
    except ImportError:
        print("\n❌ Error: graphviz package not installed")
        print("\nTo install:")
        print("  pip install graphviz")
        print("\nAlso ensure Graphviz system package is installed:")
        print("  Ubuntu/Debian: sudo apt-get install graphviz")
        print("  macOS: brew install graphviz")
        print("  Windows: Download from https://graphviz.org/download/\n")
    except Exception as e:
        print(f"\n❌ Error generating diagrams: {e}")
        import traceback
        traceback.print_exc()