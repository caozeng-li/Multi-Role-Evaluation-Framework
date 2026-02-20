from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from multi_agent_system import MultiAgentEvaluationSystem
from config import ENABLE_LITERATURE_BACKGROUND, AGENT_WEIGHTS
from typing import Dict, Any, List, Optional
from fastapi.middleware.cors import CORSMiddleware

class TopicRequest(BaseModel):
    topic: str
    use_literature_background: Optional[bool] = None  # Uses config.ENABLE_LITERATURE_BACKGROUND if not specified

class AgentScore(BaseModel):
    agent_role: str
    analysis: str
    score: float
    dimension_scores: Dict[str, int] = {}  # Scores for each evaluation dimension
    background_context_used: bool = False

class LiteratureLink(BaseModel):
    type: str  # "doi", "download", "fulltext", "core"
    url: str

class LiteratureReference(BaseModel):
    title: str
    authors: List[str] = []
    year: str = ""
    doi: str = ""
    links: List[LiteratureLink] = []

class EntityBackgroundInfo(BaseModel):
    definition: str = ""
    progress: str = ""
    challenges: str = ""

class EntityBackgroundData(BaseModel):
    background: EntityBackgroundInfo
    literature_count: int = 0
    literature_sources: List[str] = []
    literature_references: List[LiteratureReference] = []

class LiteratureBackground(BaseModel):
    entities: List[str]
    entity_backgrounds: Dict[str, Dict[str, Any]]  # Flexible for compatibility

class EvaluationResponse(BaseModel):
    agent_scores: Dict[str, AgentScore]
    weighted_total_score: float
    literature_background: Optional[LiteratureBackground] = None

app = FastAPI()

# 允许的前端地址
origins = [
    "http://43.130.39.35:3000",
    "http://127.0.0.1:5500",
    "http://localhost:5500",
    # 如果有其他前端地址，也可以加在这里
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # 允许的源
    allow_credentials=True,
    allow_methods=["*"],    # 允许所有方法
    allow_headers=["*"],    # 允许所有头
)

system = MultiAgentEvaluationSystem()

@app.post("/evaluate", response_model=EvaluationResponse)
def evaluate_topic(request: TopicRequest):
    topic = request.topic
    # Use config default if not specified in request
    use_literature_background = request.use_literature_background
    if use_literature_background is None:
        use_literature_background = ENABLE_LITERATURE_BACKGROUND
    try:
        # Get evaluations from all agents (with optional literature background)
        result = system.evaluate_topic_all_agents(
            topic, 
            parallel=True,
            use_literature_background=use_literature_background
        )
        agent_evaluations = result['agent_evaluations']
        agent_scores = {}
        weighted_total = 0.0
        for role, agent_result in agent_evaluations.items():
            score = agent_result['score']
            analysis = agent_result['analysis']
            dimension_scores = agent_result.get('dimension_scores', {})
            background_used = agent_result.get('background_context_used', False)
            agent_scores[role] = AgentScore(
                agent_role=role, 
                analysis=analysis, 
                score=score,
                dimension_scores=dimension_scores,
                background_context_used=background_used
            )
            if score is not None and role in AGENT_WEIGHTS:
                weighted_total += score * AGENT_WEIGHTS[role]
        
        # 构建响应，包含文献背景信息
        response_data = {
            "agent_scores": agent_scores,
            "weighted_total_score": weighted_total
        }
        
        # 添加背景信息（如果存在）
        if 'literature_background' in result:
            lit_bg = result['literature_background']
            response_data["literature_background"] = LiteratureBackground(
                entities=lit_bg.get('entities', []),
                entity_backgrounds=lit_bg.get('entity_backgrounds', {})
            )
        
        return EvaluationResponse(**response_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 
