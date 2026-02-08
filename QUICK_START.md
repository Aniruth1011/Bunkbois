# US Healthcare Agent - Quick Start Guide

Get started with the US Healthcare Agent system in 5 minutes!

## Prerequisites

- Python 3.9 or higher
- OpenAI API key (or another supported LLM provider)
- 2GB free disk space

## Installation

### Step 1: Install Dependencies

```bash
pip install langchain langgraph langchain-openai langchain-core langchain-community pandas chromadb python-dotenv
```

Or use the requirements file:
```bash
pip install -r requirements.txt
```

### Step 2: Configure API Key

The system needs an API key to function. Edit the `.env` file:

```bash
# Open .env in your editor
nano .env

# Replace the placeholder with your actual OpenAI API key
OPENAI_API_KEY=sk-your-actual-openai-key-here
```

**Don't have an API key?** Get one at: https://platform.openai.com/api-keys

### Step 3: Verify Setup

```bash
python test_system.py
```

This will:
- ✓ Validate your configuration
- ✓ Load the US healthcare datasets
- ✓ Create the SQLite database
- ✓ Run sample queries
- ✓ Display results

## Usage

### Option 1: Interactive Demo

```bash
python demo.py
```

Choose from:
1. **Demo Mode**: Run 4 pre-configured example queries
2. **Interactive Mode**: Ask your own questions
3. **Exit**

### Option 2: Programmatic Usage

```python
from enhanced_healthcare_agent import run_query

# Ask a question
response = run_query("How many hospitals are in California?")
print(response)
```

### Option 3: Custom Integration

```python
from enhanced_healthcare_agent import build_enhanced_graph
from enhanced_state import AppState
from langchain_core.messages import HumanMessage

# Build the agent graph
app = build_enhanced_graph()

# Create initial state
state = {
    "messages": [HumanMessage(content="Your question here")],
    # ... other state fields
}

# Execute
result = app.invoke(state)
print(result["final_response"])
```

## Example Queries

### Basic Queries (SQL Agent)
```
How many hospitals are in Texas?
Which state has the most healthcare facilities?
List hospitals in New York offering emergency services
How many cardiologists work in California hospitals?
```

### Geographic Analysis (Geo Agent)
```
Show me the distribution of hospitals across states
Which states have the fewest healthcare facilities?
Identify underserved areas for cardiology
```

### Data Quality Analysis (Analytics Agents)
```
Which facilities claim neurosurgery but might lack ICU?
Identify systemic data quality issues
Find contradictions in ophthalmology claims
```

### Accessibility Analysis (Reachability Agent)
```
How accessible is dialysis in rural areas?
Score healthcare reachability for each state
Which regions have poor cardiology access?
```

### Complex Analytics (Multiple Agents)
```
Identify medical deserts for emergency services
Which states are medical deserts for specialized care?
Analyze data quality patterns across the country
```

## Understanding the Output

Every response includes:

1. **Direct Answer**: Clear, concise response to your question
2. **Supporting Data**: Numbers, statistics, and facts
3. **Data Quality Notes**: Any issues or caveats found
4. **Citations**: Always cites "US Gov Dataset" as the source

Example output:
```
California has 1,247 healthcare facilities in the database.

The distribution breaks down as follows:
• Los Angeles: 423 facilities
• San Francisco: 189 facilities
• San Diego: 156 facilities
...

---
Data Sources:
• SQL analysis of 1,247 facilities (US Gov Dataset)
```

## Common Issues & Solutions

### Issue: "OPENAI_API_KEY not set"
**Solution**: Edit `.env` file and add your actual API key

### Issue: "CSV file not found"
**Solution**: Ensure data files are in `/mnt/user-data/uploads/` or update paths in `.env`

### Issue: "Import error"
**Solution**: Install missing dependencies: `pip install -r requirements.txt`

### Issue: Slow first run
**Solution**: Normal! First run indexes all facilities (takes 2-3 minutes). Subsequent runs are fast.

## What's Happening Under the Hood?

When you ask a question:

1. **Supervisor Agent** classifies your intent
2. **Appropriate agents** are invoked:
   - SQL Agent for counts/filters
   - Vector Agent for semantic search
   - Geo Agent for location analysis
   - Analytics agents for quality checks
3. **Results are synthesized** into a coherent answer
4. **Citations are added** for transparency

## Next Steps

- **Read the README.md** for comprehensive documentation
- **View the architecture** in SYSTEM_ARCHITECTURE.md
- **Explore the code** to understand agent logic
- **Try custom queries** tailored to your needs
- **Extend the system** by adding new agents

## System Requirements

- **Memory**: 4GB RAM minimum (8GB recommended)
- **Storage**: 2GB for database and vector index
- **Network**: Internet connection for API calls
- **OS**: Any (Linux, macOS, Windows)

## Performance Tips

1. **First Run**: Allow 2-3 minutes for initial indexing
2. **Subsequent Runs**: Queries complete in 3-10 seconds
3. **Complex Analytics**: May take 15-30 seconds
4. **Vector Search**: Faster with smaller datasets

## Data Information

### Datasets Used
- **Hospitals**: 1,000+ US healthcare facilities
- **Doctors**: 40,000+ healthcare providers
- **Mappings**: Hospital-doctor affiliations
- **Departments**: Department-level statistics

### Data Source
All data from **US Government** (Centers for Medicare & Medicaid Services)
- Official CMS Provider Data
- Publicly available
- Regularly updated

### Data Citation
All responses cite: **"US Gov Dataset"**

## Getting Help

1. Check this guide
2. Read README.md
3. Review example queries in demo.py
4. Check error messages carefully
5. Verify .env configuration

## Advanced Features

### Custom LLM Provider

Change LLM provider in `.env`:
```bash
# Use Google Gemini
LLM_PROVIDER=google
GOOGLE_API_KEY=your-google-key

# Use Groq (fast inference)
LLM_PROVIDER=groq
GROQ_API_KEY=your-groq-key

# Use Anthropic Claude
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your-anthropic-key
```

### Custom Analytics Settings

Adjust thresholds in `.env`:
```bash
CONTRADICTION_CLUSTER_THRESHOLD=10  # Min facilities for systemic issue
REACHABILITY_WEIGHT_GEOGRAPHIC=0.5  # Weight for distance
REACHABILITY_WEIGHT_CAPABILITY=0.5  # Weight for capabilities
```

## Contributing

Want to extend the system?

1. **Add medical knowledge**: Edit `medical_knowledge.py`
2. **Create new agent**: Follow pattern in existing agents
3. **Modify routing**: Update `SupervisorAgent` or `DataQualityRouter`
4. **Add data sources**: Extend database schema

## Support

For issues:
- Check configuration (.env file)
- Verify dependencies installed
- Review error messages
- Test with simple queries first

---

**Ready to start? Run `python demo.py` now!**

*Built with LangChain & LangGraph | Powered by US Government Data*
