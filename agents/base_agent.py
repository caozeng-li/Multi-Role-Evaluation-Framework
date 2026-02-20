from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import re
from llm_client import LLMClient


class BaseAgent(ABC):
    """Base class for all evaluation agents"""
    
    def __init__(self, role: str, llm_client: LLMClient):
        self.role = role
        self.llm_client = llm_client
        self.system_prompt = self._get_system_prompt()
    
    @abstractmethod
    def _get_system_prompt(self) -> str:
        """Get the system prompt that defines the agent's role and behavior"""
        pass
    
    @abstractmethod
    def _get_evaluation_criteria(self) -> str:
        """Get the specific evaluation criteria for this agent role"""
        pass
    
    def _extract_score(self, response: str) -> Optional[int]:
        """Extract the overall numerical score from agent response"""
        # Look for "Overall Score" pattern first
        overall_pattern = r'[Oo]verall\s+[Ss]core[:\s]*(\d+)'
        match = re.search(overall_pattern, response)
        if match:
            score = int(match.group(1))
            if 1 <= score <= 10:
                return score
        
        # Fallback patterns
        patterns = [
            r'[Ss]core[:\s]*(\d+)',
            r'[Rr]ating[:\s]*(\d+)', 
            r'(\d+)/10',
            r'(\d+)\s*out\s*of\s*10',
            r'[Gg]rade[:\s]*(\d+)',
            r'[Ee]valuation[:\s]*(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response)
            if match:
                score = int(match.group(1))
                if 1 <= score <= 10:
                    return score
        
        # If no clear pattern found, look for any single digit between 1-10
        digits = re.findall(r'\b([1-9]|10)\b', response)
        if digits:
            # Take the last digit found (often the final score)
            return int(digits[-1])
            
        return None
    
    def _extract_dimension_scores(self, response: str) -> Dict[str, int]:
        """Extract scores for each evaluation dimension from agent response"""
        dimension_scores = {}
        
        # Split response into sections by common dimension headers
        lines = response.split('\n')
        current_dimension = None
        
        # Keywords that indicate a dimension header (not summary/overall)
        dimension_keywords = [
            'FEASIBILITY', 'SIGNIFICANCE', 'METHODOLOGY', 'NOVELTY', 'INNOVATION',
            'IMPACT', 'INTEGRATION', 'ENVIRONMENT', 'HARDWARE', 'OPERATIONAL',
            'SAFETY', 'HUMAN FACTORS', 'RELEVANCE', 'ETHICAL', 'EQUITY', 'JUSTICE',
            'PUBLIC', 'RESOURCE', 'INTERNATIONAL', 'COOPERATION', 'RISK',
            'STRATEGIC', 'STAKEHOLDER', 'COMMERCIALIZATION', 'TRANSFER',
            'SPACE-SPECIFIC', 'NECESSITY', 'COMPLEXITY', 'VALUE'
        ]
        
        # Keywords to skip (not dimension headers)
        skip_keywords = ['OVERALL', 'SUMMARY', 'ASSESSMENT', 'CONCLUSION']
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            # Check if this line is a dimension header (all caps or title case with common keywords)
            if line_stripped and not line_stripped.startswith('Analysis') and not line_stripped.startswith('Score'):
                upper_line = line_stripped.upper()
                
                # Skip overall/summary sections
                if any(skip in upper_line for skip in skip_keywords):
                    current_dimension = None
                    continue
                
                # Check for dimension-like headers
                if any(keyword in upper_line for keyword in dimension_keywords):
                    # Clean up dimension name
                    current_dimension = line_stripped.strip('[]').strip(':').strip()
                    continue
            
            # Look for score in current section
            if current_dimension:
                score_match = re.search(r'[Ss]core[:\s]*(\d+)(?:/10)?', line_stripped)
                if score_match:
                    score = int(score_match.group(1))
                    if 1 <= score <= 10:
                        dimension_scores[current_dimension] = score
        
        return dimension_scores
    
    def evaluate_topic(self, topic: str, background_context: str = None) -> Dict[str, Any]:
        """
        Evaluate a space science research topic
        
        Args:
            topic: The research topic to evaluate
            background_context: 可选的背景信息上下文，包含关键科学实体的定义、研究进展和挑战
            
        Returns:
            Dictionary containing evaluation results
        """
        # Build background information section
        background_section = ""
        if background_context:
            background_section = f"""
The following is background information on key scientific entities in this topic. Use this knowledge to inform your evaluation, but do not explicitly mention or summarize this background in your response:

{background_context}

"""
        
        # Construct the user prompt with evaluation criteria
        user_prompt = f"""
{self._get_evaluation_criteria()}
{background_section}
Please evaluate the following space science research topic:

Topic: {topic}

For EACH evaluation dimension listed above, provide:
1. A brief analysis (2-3 sentences)
2. A specific score from 1 to 10

Scoring guide:
- 1-3: Low priority/value
- 4-6: Medium priority/value  
- 7-8: High priority/value
- 9-10: Critical/essential priority/value

Please structure your response as follows (use this exact format for each dimension):

[DIMENSION NAME]
Analysis: [Your analysis for this specific dimension]
Score: [X]/10

... (repeat for each dimension)

OVERALL ASSESSMENT
Summary: [Brief overall summary integrating all dimensions]
Overall Score: [X]/10

Be specific about why you give each score based on your professional background and concerns.
"""

        # Use proper message format with system and user roles
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # Get response from LLM (using config defaults for temperature and top_p)
        response = self.llm_client.generate_response(messages, preserve_thinking=True)
        
        if response is None:
            return {
                "agent_role": self.role,
                "topic": topic,
                "analysis": "Failed to generate response",
                "score": None,
                "raw_response": None
            }
        
        # Extract overall score from response
        score = self._extract_score(response)
        
        # Extract dimension-specific scores
        dimension_scores = self._extract_dimension_scores(response)
        
        result = {
            "agent_role": self.role,
            "topic": topic, 
            "analysis": response,
            "score": score,
            "dimension_scores": dimension_scores,
            "raw_response": response
        }
        
        # Add background context flag
        if background_context:
            result["background_context_used"] = True
        else:
            result["background_context_used"] = False
            
        return result 