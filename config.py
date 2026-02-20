# Configuration file for the Space Science Research Topic Evaluation Multi-Agent System

API_URL = ""
LLM_MODEL_NAME = ""
OPENAI_API_KEY = ""
CORE_API_KEY = ""
CORE_API_BASE_URL = ""

# Literature Background Feature Toggle
# Set to False to disable literature background retrieval
ENABLE_LITERATURE_BACKGROUND = True

# LLM Sampling Parameters (set low for deterministic and consistent results)
LLM_TEMPERATURE = 0.7
LLM_TOP_P = 0.7
LLM_MAX_TOKENS = 10000

# Agent Configuration
AGENT_ROLES = [
    "science_project_manager",
    "engineer", 
    "researcher",
    "astronaut",
    "sociologist"
]

# Agent Weights for Weighted Total Score
AGENT_WEIGHTS = {
    'science_project_manager': 0.13,
    'engineer': 0.05,
    'researcher': 0.37,
    'astronaut': 0.04,
    'sociologist': 0.41
}

# Evaluation Configuration
MIN_SCORE = 1
MAX_SCORE = 10

# Topic Priority Levels (for validation)
PRIORITY_LEVELS = {
    1: "test",
    2: "test",
    3: "test", 
    4: "test"
}

# Request timeout settings
REQUEST_TIMEOUT = 300
MAX_RETRIES = 3 