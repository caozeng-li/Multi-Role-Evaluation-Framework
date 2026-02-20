# Multi-Role Evaluation System

A **FastAPI-based multi-agent system** for evaluating space science research topics.
The system employs **five categories of expert agents** to provide comprehensive evaluations, including **dimension-based scoring** and **academic literature background information**.

---

## Project Structure

```
space-bio-agent/
├── agents/                  # Agent modules
│   ├── base_agent.py        # Base agent class
│   ├── science_project_manager.py
│   ├── engineer.py
│   ├── researcher.py
│   ├── astronaut.py
│   └── sociologist.py
├── config.py                # Configuration file
├── llm_client.py            # LLM API client
├── literature_search.py     # Academic literature background module
├── multi_agent_system.py    # Multi-agent coordination system
├── web_service.py           # FastAPI web service
└── requirements.txt         # Dependencies
```

---

## Installation

```bash
pip install -r requirements.txt
```

---

## Configuration

Edit `config.py` to configure the system:

```python
# LLM API configuration
API_URL = "https://api.openai.com/v1/chat/completions"
LLM_MODEL_NAME = "gpt-4o-mini"
OPENAI_API_KEY = "your_openai_api_key"

# CORE academic literature API (optional)
CORE_API_KEY = "your_core_api_key"  # Obtain from https://core.ac.uk/services/api
CORE_API_BASE_URL = "https://api.core.ac.uk/v3"

# Literature background feature toggle
ENABLE_LITERATURE_BACKGROUND = True  # Set to False to disable
```

---

## Running the Service

### Development Environment

```bash
uvicorn web_service:app --host 0.0.0.0 --port 8000
```

### Production Environment (Run in Background)

```bash
nohup uvicorn web_service:app --host 0.0.0.0 --port 8000 > app.log 2>&1 &
```

---

## API Endpoints

### `POST /evaluate`

Evaluate a space science research topic using five categories of expert agents.

#### Request

```json
{
  "topic": "Study of bone density loss mechanisms in microgravity and protective strategies",
  "use_literature_background": true
}
```

#### Response

```json
{
  "agent_scores": {
    "researcher": {
      "agent_role": "researcher",
      "analysis": "...",
      "score": 9.0,
      "dimension_scores": {
        "SCIENTIFIC SIGNIFICANCE": 9,
        "RESEARCH METHODOLOGY": 8,
        "NOVELTY AND INNOVATION": 8,
        "SPACE-SPECIFIC NECESSITY": 10,
        "SCIENTIFIC IMPACT": 9
      },
      "background_context_used": true
    },
    "engineer": {
      "agent_role": "engineer",
      "score": 7.0,
      "dimension_scores": {
        "TECHNICAL FEASIBILITY": 7,
        "SYSTEM INTEGRATION": 6,
        "SPACE ENVIRONMENT CONSIDERATIONS": 8,
        "HARDWARE AND INSTRUMENTATION": 7,
        "OPERATIONAL COMPLEXITY": 6,
        "ENGINEERING VALUE": 8
      }
    }
  },
  "weighted_total_score": 7.61,
  "literature_background": {
    "entities": ["Microgravity Environment", "Bone Density Loss", "Protective Strategies"],
    "entity_backgrounds": {
      "Bone Density Loss": {
        "background": {
          "definition": "Bone density loss refers to the reduction in mineral content and structural integrity of bone tissue...",
          "progress": "Significant advancements have been made in understanding the mechanisms underlying bone density loss...",
          "challenges": "Key issues include the complexity of replicating microgravity conditions..."
        },
        "literature_count": 5,
        "literature_references": [
          {
            "title": "Changes in mineral metabolism with immobilization/space flight",
            "authors": ["Gallagher, J. C."],
            "year": 2023,
            "doi": "10.1234/example",
            "links": [
              {"type": "doi", "url": "https://doi.org/10.1234/example"},
              {"type": "download", "url": "https://core.ac.uk/download/..."},
              {"type": "core", "url": "https://core.ac.uk/works/12345"}
            ]
          }
        ]
      }
    }
  }
}
```

---

## Features

### 1. Five Categories of Expert Agents

| Role                        | Evaluation Dimensions                                                                                |
| --------------------------- | ---------------------------------------------------------------------------------------------------- |
| **Researcher**              | Scientific significance, research methodology, innovation, space necessity, scientific impact        |
| **Engineer**                | Technical feasibility, system integration, hardware and instrumentation, operational complexity      |
| **Astronaut**               | Operational feasibility, crew safety, human factors, space environment                               |
| **Science Project Manager** | Project feasibility, resource requirements, risk assessment, strategic value, stakeholders           |
| **Sociologist**             | Social relevance, ethical considerations, equity and justice, public engagement, technology transfer |

---

### 2. Dimension-Based Scoring

Each agent assigns **scores (1–10)** to each evaluation dimension and provides an **overall score**.

---

### 3. Academic Literature Background Information

Before evaluation, the system automatically performs:

1. **Key entity extraction** – Uses an LLM to identify 2–3 key scientific concepts
2. **Literature search** – Retrieves relevant academic papers via the CORE API
3. **Background synthesis** – Generates definitions, research progress, and challenges
4. **Shared context** – All five expert agents use the same background information

---

### 4. Citation Links

Each referenced paper includes multiple link types:

* `doi`: DOI link (e.g., [https://doi.org/10.1234/](https://doi.org/10.1234/)...)
* `download`: Direct PDF download from CORE
* `fulltext`: Full-text source link
* `core`: CORE platform page

---

## Testing

```bash
# Basic evaluation
curl -X POST "http://localhost:8000/evaluate" \
     -H "Content-Type: application/json" \
     -d '{"topic": "Effects of long-duration spaceflight on human cardiovascular system"}'

# Disable literature background
curl -X POST "http://localhost:8000/evaluate" \
     -H "Content-Type: application/json" \
     -d '{"topic": "Mars soil analysis for astrobiology", "use_literature_background": false}'

# View API documentation
# Swagger UI: http://localhost:8000/docs
# ReDoc: http://localhost:8000/redoc
```

---

### Weighted Total Score Calculation

| Agent                   | Weight |
| ----------------------- | ------ |
| Sociologist             | 0.41   |
| Researcher              | 0.37   |
| Science Project Manager | 0.13   |
| Engineer                | 0.05   |
| Astronaut               | 0.04   |

---

## Notes

1. Ensure that valid LLM API credentials are configured in `config.py`
2. The CORE API key is optional; mock data will be used if not provided
3. Set `ENABLE_LITERATURE_BACKGROUND = False` to disable literature search
4. CORS settings can be modified in `web_service.py`
