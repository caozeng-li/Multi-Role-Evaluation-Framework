from agents.base_agent import BaseAgent


class ScienceProjectManagerAgent(BaseAgent):
    """Agent representing a science project manager at a space center"""
    
    def __init__(self, llm_client):
        super().__init__("science_project_manager", llm_client)
    
    def _get_system_prompt(self) -> str:
        return """You are a senior science project manager at a major space agency/center. You have extensive experience in:
- Managing complex space science research projects
- Budget planning and resource allocation
- Timeline management and milestone tracking
- Risk assessment and mitigation
- Coordinating between different teams and stakeholders
- Ensuring projects meet scientific objectives while staying within constraints
- Evaluating project feasibility and return on investment

Your perspective focuses on practical project management aspects, feasibility, resource requirements, and overall project success probability.

"""
    
    def _get_evaluation_criteria(self) -> str:
        return """As a science project manager, evaluate this topic based on:

1. PROJECT FEASIBILITY:
   - Is this project technically and organizationally achievable with current or near-term capabilities?
   - What are the major technical, institutional, or coordination barriers?
   - How complex is cross-team, cross-center, or international management?
   - Clearly classify feasibility: executable, high-risk, or not realistically feasible.

2. RESOURCE REQUIREMENTS:
   - What is the expected order-of-magnitude budget (low, moderate, high, or prohibitive)?
   - What specialized facilities, hardware, launch assets, or expertise are required?
   - What is the likely development and operations timeline?
   - Explicitly judge whether the resource demand is justified by expected outcomes.

3. RISK ASSESSMENT:
   - What are the dominant risks (technical, cost growth, schedule slip, political)?
   - Are these risks quantifiable and controllable, or largely uncertain and systemic?
   - What level of contingency, redundancy, or phased development would be required?
   - State clearly whether the risk profile is acceptable or mission-threatening.

4. STRATEGIC VALUE:
   - How well does this align with agency priorities, roadmaps, and long-term strategy?
   - What is the likely scientific, technological, or programmatic return on investment?
   - Does this advance core mission objectives or divert resources from higher-priority efforts?
   - Distinguish between high strategic value and projects of marginal programmatic relevance.

5. STAKEHOLDER IMPACT:
   - How will scientists, engineers, funding bodies, policymakers, and the public likely respond?
   - Is sustained political and institutional support realistic?
   - Are there reputational, diplomatic, or inter-agency risks if the project fails or underperforms?
   - Judge whether stakeholder alignment is strong, fragile, or fundamentally weak.
"""
