# US Healthcare Agent System

An advanced multi-agent system for analyzing US healthcare facility data using LangChain and LangGraph. This system provides intelligent querying, data quality analysis, and healthcare accessibility insights.

## Features

### Core Capabilities
- **SQL Agent**: Natural language to SQL conversion for healthcare data queries
- **Vector Agent**: Semantic search over facility descriptions and services
- **Geo Agent**: Geospatial analysis of healthcare facility distribution
- **Response Agent**: Intelligent synthesis of multi-agent results

### Advanced Analytics
- **Skill-Infrastructure Mismatch Detection**: Identifies facilities claiming medical capabilities without required equipment
- **Reachability Scoring**: Combines geographic access with capability verification
- **Contradiction Analysis**: Detects systemic data quality patterns
- **Desert Typology**: Classifies medical deserts (geographic, capability, skill-based)
- **Counterfactual Engine**: "What-if" scenario simulations

### Data Sources
Uses official US Government healthcare datasets including:
- Hospital/facility information
- Healthcare provider (doctor) data
- Hospital-doctor affiliations
- Department summaries

All data sourced from **US Gov Dataset** (CMS Provider Data).

## Quick Start

### 1. Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your API key
# Minimum required: OPENAI_API_KEY
nano .env
```

### 3. Run Tests

```bash
# Test the system
python test_system.py
```

### 4. Generate System Graph

```bash
# Visualize the agent architecture
python generate_graph.py
```

## Usage Examples

```python
from enhanced_healthcare_agent import run_query

# Simple SQL query
response = run_query("How many hospitals are in California?")

# Geospatial analysis
response = run_query("Which states have the fewest healthcare facilities?")

# Data quality analysis
response = run_query("Which facilities claim neurosurgery but might lack ICU?")

# Accessibility analysis
response = run_query("How accessible is cardiology in rural Texas?")

# Complex analytics
response = run_query("Identify systemic data quality issues in ophthalmology claims")
```

## System Architecture

### Agent Flow

```
User Query
    ↓
Supervisor Agent (Intent Classification)
    ↓
┌───────────────┬─────────────┬──────────────┬────────────────────┐
│   SQL Agent   │ Vector Agent│  Geo Agent   │ Analytics Pipeline │
└───────────────┴─────────────┴──────────────┴────────────────────┘
                                    ↓
                          ┌─────────────────────┐
                          │ Data Quality Router │
                          └─────────────────────┘
                                    ↓
        ┌───────────────┬──────────────────┬──────────────────┬─────────────────┐
        │ SkillInfra    │  Reachability    │ Contradiction    │ Desert Typology │
        │ Agent         │  Agent           │ Agent            │ Agent           │
        └───────────────┴──────────────────┴──────────────────┴─────────────────┘
                                    ↓
                          ┌─────────────────┐
                          │ Response Agent  │
                          └─────────────────┘
                                    ↓
                              Final Answer
```

### Database Schema

**hospitals** table:
- Facility information (name, location, type)
- Medical capabilities and specialties
- Equipment and procedures
- Contact information

**doctors** table:
- Provider information (NPI, name, credentials)
- Specialty and department
- Practice location

**hospital_doctor_mapping** table:
- Links doctors to facilities
- Department affiliations

**department_summary** table:
- Aggregated department statistics

## Configuration Options

### LLM Providers
- **OpenAI** (default): GPT-4, GPT-3.5
- **Google**: Gemini Pro
- **Groq**: Llama models
- **Anthropic**: Claude models

### Analytics Settings
```python
CONTRADICTION_CLUSTER_THRESHOLD = 10  # Min facilities for systemic issue
REACHABILITY_WEIGHT_GEOGRAPHIC = 0.5  # Weight for distance
REACHABILITY_WEIGHT_CAPABILITY = 0.5  # Weight for verified capabilities
```

## Data Quality Features

### Skill-Infrastructure Validation
Validates medical claims against required equipment:
- **Critical equipment**: Must have for the procedure (e.g., ICU for neurosurgery)
- **Required equipment**: Necessary for standard operations
- **Recommended equipment**: Enhances service quality

### Citation and Transparency
Every response includes:
- Data sources (always cites "US Gov Dataset")
- Number of facilities/records analyzed
- Agent execution trail
- Data quality caveats

## File Structure

```
.
├── config.py                      # Configuration management
├── enhanced_state.py              # State definitions
├── medical_knowledge.py           # Medical domain rules
├── enhanced_healthcare_agent.py   # Main orchestration
│
├── Agents:
│   ├── sql_agent.py              # SQL query generation
│   ├── vector_agent.py           # Semantic search
│   ├── geo_agent.py              # Geospatial analysis
│   ├── skill_infra_agent.py      # Mismatch detection
│   ├── reachability_agent.py     # Accessibility scoring
│   ├── contradiction_agent.py    # Pattern analysis
│   ├── desert_typology_agent.py  # Medical desert classification
│   ├── counterfactual_engine.py  # What-if simulations
│   └── data_quality_router.py    # Analytics routing
│
├── Data:
│   ├── us_healthcare_data_hospitals.csv
│   ├── us_healthcare_data_doctors.csv
│   ├── us_healthcare_data_hospital_doctor_mapping.csv
│   └── us_healthcare_data_department_summary.csv
│
├── Utilities:
│   ├── test_system.py            # Test suite
│   ├── generate_graph.py         # Graph visualization
│   ├── requirements.txt          # Dependencies
│   └── .env.example              # Config template
│
└── README.md                      # This file
```

## Advanced Usage

### Custom Analytics Pipeline

```python
from enhanced_healthcare_agent import build_enhanced_graph
from enhanced_state import AppState
from langchain_core.messages import HumanMessage

# Build graph
app = build_enhanced_graph()

# Custom state
state = {
    "messages": [HumanMessage(content="Your question")],
    "analytics_plan": ["SkillInfraAgent", "ContradictionAgent"],
    # ... other state fields
}

# Execute
result = app.invoke(state)
```

### Accessing Raw Results

```python
# After running a query, access intermediate results:
final_state = app.invoke(initial_state)

# SQL results
sql_data = final_state["sql_result"]["data"]  # Pandas DataFrame

# Skill-infrastructure mismatches
mismatches = final_state["skill_infra_mismatches"]

# Reachability scores
scores = final_state["reachability_scores"]

# Contradiction graph
graph = final_state["contradiction_graph"]
```

## Troubleshooting

### Common Issues

1. **API Key Error**
   ```
   Solution: Ensure OPENAI_API_KEY is set in .env file
   ```

2. **Database Not Found**
   ```
   Solution: Check CSV paths in .env, run system once to create DB
   ```

3. **Import Errors**
   ```
   Solution: Install all requirements: pip install -r requirements.txt
   ```

4. **Graph Generation Fails**
   ```
   Solution: Mermaid format will be used instead of PNG
   ```

## Performance Optimization

- **Vector indexing**: First run indexes all facilities (may take 2-3 minutes)
- **Subsequent queries**: Fast (<5 seconds for most queries)
- **Large analytics**: May take 10-30 seconds depending on complexity

## Citation Format

All responses cite sources as:
```
Data Sources:
• SQL analysis of X facilities (US Gov Dataset)
• Infrastructure mismatch detection (US Gov Dataset)
• Reachability scoring (US Gov Dataset)
```

## Contributing

This system is designed to be extensible:
- Add new agents by extending base agent pattern
- Add medical knowledge rules in `medical_knowledge.py`
- Customize routing logic in supervisors

## License

This system uses publicly available US Government healthcare data.

## Support

For issues or questions:
1. Check this README
2. Review test_system.py for examples
3. Check configuration in .env file
4. Verify all dependencies are installed

---

**Built with LangChain & LangGraph | Powered by US Government Healthcare Data**
