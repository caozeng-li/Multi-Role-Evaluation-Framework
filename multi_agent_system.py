import asyncio
from typing import List, Dict, Any, Optional
import numpy as np
from scipy.stats import spearmanr
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

from llm_client import LLMClient
from literature_search import LiteratureSearchService
from config import ENABLE_LITERATURE_BACKGROUND
from agents import (
    ScienceProjectManagerAgent,
    EngineerAgent, 
    ResearcherAgent,
    AstronautAgent,
    SociologistAgent
)


class MultiAgentEvaluationSystem:
    """Multi-agent system for evaluating space science research topics"""
    
    def __init__(self):
        self.llm_client = LLMClient()
        self.agents = self._initialize_agents()
        self.literature_service = LiteratureSearchService(self.llm_client)
        
    def _initialize_agents(self) -> Dict[str, Any]:
        """Initialize all evaluation agents"""
        return {
            'science_project_manager': ScienceProjectManagerAgent(self.llm_client),
            'engineer': EngineerAgent(self.llm_client),
            'researcher': ResearcherAgent(self.llm_client),
            'astronaut': AstronautAgent(self.llm_client),
            'sociologist': SociologistAgent(self.llm_client)
        }
    
    def test_system(self) -> bool:
        """Test if the system is properly configured and LLM is accessible"""
        print("Testing LLM connection...")
        if not self.llm_client.test_connection():
            print("❌ LLM connection failed")
            return False
        
        print("✅ LLM connection successful")
        print(f"✅ Initialized {len(self.agents)} agents:")
        for role in self.agents.keys():
            print(f"   - {role}")
        
        return True
    
    def evaluate_topic_single_agent(self, agent_role: str, topic: str, 
                                     use_literature_background: bool = None) -> Dict[str, Any]:
        """
        Evaluate a topic using a single agent
        
        Args:
            agent_role: The role of the agent to use
            topic: The research topic to evaluate
            use_literature_background: Whether to fetch and use literature background info
        """
        if agent_role not in self.agents:
            raise ValueError(f"Unknown agent role: {agent_role}")
        
        # Use config default if not specified
        if use_literature_background is None:
            use_literature_background = ENABLE_LITERATURE_BACKGROUND
        
        background_context = None
        if use_literature_background:
            print(f"📚 Fetching topic background information...")
            background_info = self.literature_service.get_topic_background(topic)
            background_context = background_info.get("formatted_context")
        
        agent = self.agents[agent_role]
        return agent.evaluate_topic(topic, background_context=background_context)
    
    def evaluate_topic_all_agents(self, topic: str, parallel: bool = True,
                                   use_literature_background: bool = None) -> Dict[str, Any]:
        """
        Evaluate a topic using all agents
        
        Args:
            topic: The research topic to evaluate
            parallel: Whether to run evaluations in parallel
            use_literature_background: Whether to fetch and use literature background info
            
        Returns:
            Dictionary containing all agent evaluations and summary statistics
        """
        # Use config default if not specified
        if use_literature_background is None:
            use_literature_background = ENABLE_LITERATURE_BACKGROUND
        
        # Fetch background info once, shared by all agents
        background_context = None
        background_info = None
        
        if use_literature_background:
            print(f"\n📚 Fetching topic background information...")
            background_info = self.literature_service.get_topic_background(topic)
            background_context = background_info.get("formatted_context")
            print(f"✅ Background information retrieval complete\n")
        
        if parallel:
            return self._evaluate_parallel(topic, background_context, background_info)
        else:
            return self._evaluate_sequential(topic, background_context, background_info)
    
    def _evaluate_sequential(self, topic: str, background_context: str = None,
                              background_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """Evaluate topic sequentially with each agent"""
        results = {}
        agent_results = []
        
        print(f"Evaluating topic: {topic}")
        
        for role, agent in self.agents.items():
            print(f"  Getting evaluation from {role}...")
            result = agent.evaluate_topic(topic, background_context=background_context)
            results[role] = result
            agent_results.append(result)
        
        return self._compile_results(topic, agent_results, background_info)
    
    def _evaluate_parallel(self, topic: str, background_context: str = None,
                            background_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """Evaluate topic in parallel with all agents"""
        print(f"Evaluating topic: {topic}")
        
        with ThreadPoolExecutor(max_workers=len(self.agents)) as executor:
            # Submit all evaluation tasks with shared background context
            future_to_role = {
                executor.submit(agent.evaluate_topic, topic, background_context): role 
                for role, agent in self.agents.items()
            }
            
            results = {}
            agent_results = []
            
            # Collect results as they complete
            for future in as_completed(future_to_role):
                role = future_to_role[future]
                try:
                    result = future.result()
                    results[role] = result
                    agent_results.append(result)
                    print(f"  ✅ {role} evaluation completed")
                except Exception as e:
                    print(f"  ❌ {role} evaluation failed: {e}")
                    # Create a failed result
                    failed_result = {
                        "agent_role": role,
                        "topic": topic,
                        "analysis": f"Evaluation failed: {e}",
                        "score": None,
                        "raw_response": None,
                        "background_context_used": background_context is not None
                    }
                    results[role] = failed_result
                    agent_results.append(failed_result)
        
        return self._compile_results(topic, agent_results, background_info)
    
    def _compile_results(self, topic: str, agent_results: List[Dict[str, Any]],
                         background_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """Compile individual agent results into summary"""
        # Extract valid scores
        valid_scores = [r['score'] for r in agent_results if r['score'] is not None]
        
        # Calculate statistics
        if valid_scores:
            average_score = np.mean(valid_scores)
            std_score = np.std(valid_scores)
            min_score = min(valid_scores)
            max_score = max(valid_scores)
        else:
            average_score = std_score = min_score = max_score = None
        
        result = {
            'topic': topic,
            'agent_evaluations': {r['agent_role']: r for r in agent_results},
            'summary_statistics': {
                'average_score': average_score,
                'standard_deviation': std_score,
                'min_score': min_score,
                'max_score': max_score,
                'valid_evaluations': len(valid_scores),
                'total_agents': len(agent_results)
            },
            'individual_scores': {r['agent_role']: r['score'] for r in agent_results}
        }
        
        # 添加背景信息到结果中
        if background_info:
            result['literature_background'] = {
                'entities': background_info.get('entities', []),
                'entity_backgrounds': background_info.get('backgrounds', {}),
                'formatted_context': background_info.get('formatted_context', '')
            }
        
        return result
    
    def evaluate_multiple_topics(self, topics: List[str], parallel: bool = True) -> List[Dict[str, Any]]:
        """
        Evaluate multiple topics
        
        Args:
            topics: List of research topics to evaluate
            parallel: Whether to run evaluations in parallel
            
        Returns:
            List of evaluation results for each topic
        """
        results = []
        
        print(f"Evaluating {len(topics)} topics...")
        
        for i, topic in enumerate(topics, 1):
            print(f"\n--- Topic {i}/{len(topics)} ---")
            result = self.evaluate_topic_all_agents(topic, parallel=parallel)
            results.append(result)
        
        return results
    
    def calculate_correlation(self, evaluation_results: List[Dict[str, Any]], 
                            true_rankings: List[int]) -> Dict[str, Any]:
        """
        Calculate Spearman correlation between agent scores and true rankings
        
        Args:
            evaluation_results: Results from evaluate_multiple_topics
            true_rankings: True priority rankings (1=highest, 4=lowest priority)
            
        Returns:
            Correlation analysis results
        """
        if len(evaluation_results) != len(true_rankings):
            raise ValueError("Number of evaluation results must match number of true rankings")
        
        # Extract average scores
        agent_scores = []
        valid_indices = []
        
        for i, result in enumerate(evaluation_results):
            avg_score = result['summary_statistics']['average_score']
            if avg_score is not None:
                agent_scores.append(avg_score)
                valid_indices.append(i)
        
        if len(agent_scores) < 2:
            return {
                'correlation_coefficient': None,
                'p_value': None,
                'error': 'Insufficient valid scores for correlation analysis'
            }
        
        # Get corresponding true rankings
        valid_true_rankings = [true_rankings[i] for i in valid_indices]
        
        # Calculate Spearman correlation
        # Note: Higher agent scores should correspond to lower ranking numbers (higher priority)
        # So we correlate agent_scores with negative of true_rankings
        correlation_coef, p_value = spearmanr(agent_scores, [-r for r in valid_true_rankings])
        
        return {
            'correlation_coefficient': correlation_coef,
            'p_value': p_value,
            'valid_comparisons': len(agent_scores),
            'agent_scores': agent_scores,
            'true_rankings': valid_true_rankings,
            'topics_evaluated': [evaluation_results[i]['topic'] for i in valid_indices]
        }
    
    def generate_report(self, evaluation_results: List[Dict[str, Any]], 
                       true_rankings: Optional[List[int]] = None) -> str:
        """Generate a comprehensive evaluation report"""
        report = []
        report.append("=" * 80)
        report.append("SPACE SCIENCE RESEARCH TOPIC EVALUATION REPORT")
        report.append("=" * 80)
        report.append("")
        
        # Summary statistics
        total_topics = len(evaluation_results)
        successful_evaluations = sum(1 for r in evaluation_results 
                                   if r['summary_statistics']['average_score'] is not None)
        
        report.append(f"Total topics evaluated: {total_topics}")
        report.append(f"Successful evaluations: {successful_evaluations}")
        report.append("")
        
        # Individual topic results
        for i, result in enumerate(evaluation_results, 1):
            report.append(f"TOPIC {i}: {result['topic']}")
            report.append("-" * 60)
            
            # Add background information summary
            if 'literature_background' in result:
                bg = result['literature_background']
                entities = bg.get('entities', [])
                if entities:
                    report.append(f"\n📚 Key Scientific Entity Background:")
                    report.append(f"Extracted Entities: {', '.join(entities)}")
                    
                    for entity, data in bg.get('entity_backgrounds', {}).items():
                        background = data.get('background', {})
                        report.append(f"\n  【{entity}】")
                        if background.get('definition'):
                            report.append(f"    Definition: {background['definition'][:100]}...")
                        if background.get('progress'):
                            report.append(f"    Research Progress: {background['progress'][:100]}...")
                        if background.get('challenges'):
                            report.append(f"    Challenges: {background['challenges'][:100]}...")
                    report.append("")
            
            stats = result['summary_statistics']
            if stats['average_score'] is not None:
                report.append(f"Average Score: {stats['average_score']:.2f}")
                report.append(f"Standard Deviation: {stats['standard_deviation']:.2f}")
                report.append(f"Score Range: {stats['min_score']} - {stats['max_score']}")
            else:
                report.append("No valid scores obtained")
            
            report.append("\nIndividual Agent Scores:")
            for role, score in result['individual_scores'].items():
                score_str = f"{score}" if score is not None else "Failed"
                report.append(f"  {role}: {score_str}")
            
            report.append("")
        
        # Correlation analysis if true rankings provided
        if true_rankings:
            correlation_result = self.calculate_correlation(evaluation_results, true_rankings)
            report.append("CORRELATION ANALYSIS")
            report.append("-" * 40)
            
            if correlation_result['correlation_coefficient'] is not None:
                report.append(f"Spearman Correlation Coefficient: {correlation_result['correlation_coefficient']:.4f}")
                report.append(f"P-value: {correlation_result['p_value']:.4f}")
                report.append(f"Valid comparisons: {correlation_result['valid_comparisons']}")
                
                # Interpretation
                corr = abs(correlation_result['correlation_coefficient'])
                if corr >= 0.8:
                    strength = "very strong"
                elif corr >= 0.6:
                    strength = "strong"
                elif corr >= 0.4:
                    strength = "moderate"
                elif corr >= 0.2:
                    strength = "weak"
                else:
                    strength = "very weak"
                
                report.append(f"Correlation strength: {strength}")
            else:
                report.append(f"Correlation analysis failed: {correlation_result.get('error', 'Unknown error')}")
        
        return "\n".join(report) 