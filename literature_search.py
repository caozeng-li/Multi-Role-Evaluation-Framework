"""
Literature Search Module

This module fetches background information for key scientific entities in research topics
using academic literature APIs before evaluation. Background includes definition, 
research progress, and challenges.
"""

import requests
import json
import re
import time
from typing import Dict, Any, List, Optional
from config import CORE_API_KEY, CORE_API_BASE_URL, REQUEST_TIMEOUT, MAX_RETRIES


class LiteratureSearchService:
    """Academic literature search service using CORE API to fetch background information"""
    
    def __init__(self, llm_client):
        """
        Initialize the literature search service
        
        Args:
            llm_client: LLM client for extracting key entities and generating summaries
        """
        self.llm_client = llm_client
        self.api_key = CORE_API_KEY
        self.base_url = CORE_API_BASE_URL
        self.timeout = REQUEST_TIMEOUT
    
    def extract_key_entities(self, topic: str) -> List[str]:
        """
        Use LLM to extract 2-3 key scientific entities from the research topic
        
        Args:
            topic: Research topic description
            
        Returns:
            List of key scientific entities
        """
        prompt = f"""Extract 2-3 key scientific entities/concepts from the following space science research topic.
These entities should be core concepts that require background knowledge to properly evaluate this topic.

Research Topic: {topic}

Return only the entity names, one per line, without numbering or other formatting.
Example output:
Microgravity Environment
Bone Loss
Muscle Atrophy"""

        messages = [
            {"role": "user", "content": prompt}
        ]
        
        response = self.llm_client.generate_response(messages, temperature=0.3)
        
        if response is None:
            return []
        
        # Parse response and extract entity list
        entities = []
        for line in response.strip().split('\n'):
            line = line.strip()
            # Remove possible numbering prefixes
            if line and not line.startswith('#'):
                # Remove "1." "2." etc. numbering
                cleaned = re.sub(r'^[\d]+[\.\)]\s*', '', line)
                cleaned = re.sub(r'^[-•]\s*', '', cleaned)
                if cleaned:
                    entities.append(cleaned)
        
        # Keep only 2-3 entities
        return entities[:3]
    
    def search_literature(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search academic literature using CORE API
        
        Args:
            query: Search query term
            limit: Maximum number of results to return
            
        Returns:
            List of literature items
        """
        if not self.api_key:
            print("Warning: CORE_API_KEY not set, using mock data")
            return self._get_mock_results(query)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # CORE API v3 search endpoint
        # Reference: https://api.core.ac.uk/docs/v3
        url = f"{self.base_url}/search/works"
        
        params = {
            "q": query,
            "limit": limit,
            "scroll": "false"
        }
        
        # Retry logic with exponential backoff for transient errors
        for attempt in range(MAX_RETRIES):
            try:
                response = requests.get(
                    url,
                    headers=headers,
                    params=params,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get("results", [])
                    return self._parse_core_results(results)
                elif response.status_code >= 500:
                    # Server error - retry with backoff
                    wait_time = (2 ** attempt) + 1  # 2, 3, 5 seconds
                    print(f"CORE API server error ({response.status_code}), retrying in {wait_time}s... (attempt {attempt + 1}/{MAX_RETRIES})")
                    time.sleep(wait_time)
                    continue
                else:
                    # Client error - don't retry
                    print(f"CORE API request failed: {response.status_code} - {response.text[:200]}")
                    return []
                    
            except requests.exceptions.RequestException as e:
                print(f"CORE API request error (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)
                    continue
                return []
        
        print(f"CORE API request failed after {MAX_RETRIES} attempts")
        return []
    
    def _parse_core_results(self, results: List[Dict]) -> List[Dict[str, Any]]:
        """Parse results returned by CORE API"""
        parsed = []
        for item in results:
            # Extract various URL fields from CORE API response
            doi = item.get("doi", "")
            download_url = item.get("downloadUrl", "")
            source_urls = item.get("sourceFulltextUrls", [])
            core_id = item.get("id", "")
            
            # Build links list
            links = []
            
            # DOI link (preferred for citation)
            if doi:
                links.append({
                    "type": "doi",
                    "url": f"https://doi.org/{doi}"
                })
            
            # Direct download URL from CORE
            if download_url:
                links.append({
                    "type": "download",
                    "url": download_url
                })
            
            # Source fulltext URLs
            if source_urls and isinstance(source_urls, list):
                for url in source_urls[:2]:  # Limit to first 2
                    if url:
                        links.append({
                            "type": "fulltext",
                            "url": url
                        })
            
            # CORE page link
            if core_id:
                links.append({
                    "type": "core",
                    "url": f"https://core.ac.uk/works/{core_id}"
                })
            
            parsed.append({
                "title": item.get("title", ""),
                "abstract": item.get("abstract", ""),
                "authors": [a.get("name", "") for a in item.get("authors", [])],
                "year": item.get("yearPublished", ""),
                "doi": doi,
                "links": links,
                "source": "CORE"
            })
        return parsed
    
    def _get_mock_results(self, query: str) -> List[Dict[str, Any]]:
        """Return mock data when API is unavailable"""
        return [
            {
                "title": f"Research on {query}",
                "abstract": f"This is a simulated abstract about {query}. No actual API data available.",
                "authors": ["Simulated Author"],
                "year": "2024",
                "doi": "",
                "links": [],
                "source": "Mock"
            }
        ]
    
    def synthesize_background(self, entity: str, literature: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Use LLM to synthesize literature information and generate background for the entity
        
        Args:
            entity: Scientific entity name
            literature: List of related literature
            
        Returns:
            Dictionary containing definition, progress, and challenges
        """
        # Build literature context
        lit_context = ""
        for i, lit in enumerate(literature[:5], 1):
            lit_context += f"\nPaper {i}: {lit['title']}"
            if lit.get('abstract'):
                # Truncate abstract to first 500 characters
                abstract = lit['abstract'][:500] + "..." if len(lit.get('abstract', '')) > 500 else lit.get('abstract', '')
                lit_context += f"\nAbstract: {abstract}"
            lit_context += "\n"
        
        prompt = f"""Based on the following academic literature information, generate background information for the scientific entity "{entity}".
Organize the content into the following three sections, with 2-3 sentences each:

1. Definition: What is this concept/entity
2. Research Progress: Major research achievements and current state in this field
3. Challenges: Main challenges and unresolved problems in this field

Related Literature:
{lit_context if lit_context.strip() else "No related literature found. Please answer based on your knowledge."}

Please respond in concise, professional language using the following format:
Definition: [content]
Research Progress: [content]
Challenges: [content]"""

        messages = [
            {"role": "user", "content": prompt}
        ]
        
        response = self.llm_client.generate_response(messages, temperature=0.5)
        
        if response is None:
            return {
                "definition": f"Unable to retrieve definition for {entity}",
                "progress": f"Unable to retrieve research progress for {entity}",
                "challenges": f"Unable to retrieve challenges for {entity}"
            }
        
        # Parse response
        return self._parse_background_response(response, entity)
    
    def _parse_background_response(self, response: str, entity: str) -> Dict[str, str]:
        """Parse LLM-generated background information response"""
        result = {
            "definition": "",
            "progress": "",
            "challenges": ""
        }
        
        lines = response.strip().split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            lower_line = line.lower()
            
            if 'definition' in lower_line and ':' in line:
                if current_section and current_content:
                    result[current_section] = ' '.join(current_content)
                current_section = 'definition'
                # Extract content after colon
                content = line.split(':', 1)[1].strip() if ':' in line else ''
                current_content = [content] if content else []
            elif 'research progress' in lower_line or 'progress' in lower_line:
                if current_section and current_content:
                    result[current_section] = ' '.join(current_content)
                current_section = 'progress'
                content = line.split(':', 1)[1].strip() if ':' in line else ''
                current_content = [content] if content else []
            elif 'challenge' in lower_line:
                if current_section and current_content:
                    result[current_section] = ' '.join(current_content)
                current_section = 'challenges'
                content = line.split(':', 1)[1].strip() if ':' in line else ''
                current_content = [content] if content else []
            elif current_section:
                current_content.append(line)
        
        # Process the last section
        if current_section and current_content:
            result[current_section] = ' '.join(current_content)
        
        # If parsing fails, use original response
        if not any(result.values()):
            result = {
                "definition": response[:200] if len(response) > 200 else response,
                "progress": "",
                "challenges": ""
            }
        
        return result
    
    def get_topic_background(self, topic: str) -> Dict[str, Any]:
        """
        Get complete background information for a research topic
        
        This is the main external interface that completes the following steps:
        1. Extract key scientific entities (2-3)
        2. Search related literature for each entity
        3. Synthesize background information (definition, progress, challenges)
        
        Args:
            topic: Research topic description
            
        Returns:
            Dictionary containing all entity background information
        """
        print(f"  📚 Extracting key scientific entities...")
        entities = self.extract_key_entities(topic)
        
        if not entities:
            print("  ⚠️ Failed to extract key entities")
            return {
                "entities": [],
                "backgrounds": {},
                "formatted_context": "Failed to extract key scientific entity background information."
            }
        
        print(f"  📚 Extracted {len(entities)} key entities: {', '.join(entities)}")
        
        backgrounds = {}
        for entity in entities:
            print(f"    🔍 Searching literature for '{entity}'...")
            literature = self.search_literature(entity)
            
            print(f"    📝 Synthesizing background for '{entity}'...")
            background = self.synthesize_background(entity, literature)
            
            # Build literature references with links
            literature_refs = []
            for lit in literature[:5]:  # Keep top 5 references
                ref = {
                    "title": lit.get("title", ""),
                    "authors": lit.get("authors", []),
                    "year": lit.get("year", ""),
                    "doi": lit.get("doi", ""),
                    "links": lit.get("links", [])
                }
                literature_refs.append(ref)
            
            backgrounds[entity] = {
                "background": background,
                "literature_count": len(literature),
                "literature_sources": [lit.get("title", "") for lit in literature[:3]],
                "literature_references": literature_refs
            }
        
        # Generate formatted context information
        formatted_context = self._format_background_context(topic, entities, backgrounds)
        
        return {
            "entities": entities,
            "backgrounds": backgrounds,
            "formatted_context": formatted_context
        }
    
    def _format_background_context(self, topic: str, entities: List[str], 
                                   backgrounds: Dict[str, Any]) -> str:
        """Format background information into context string"""
        context_parts = [
            "=" * 50,
            "📚 Research Topic Background Information (Auto-retrieved via Academic Literature API)",
            "=" * 50,
            f"\nTopic: {topic}\n",
            f"Extracted Key Scientific Entities: {', '.join(entities)}\n"
        ]
        
        for entity, data in backgrounds.items():
            bg = data.get("background", {})
            context_parts.append(f"\n【{entity}】")
            context_parts.append("-" * 30)
            
            if bg.get("definition"):
                context_parts.append(f"• Definition: {bg['definition']}")
            if bg.get("progress"):
                context_parts.append(f"• Research Progress: {bg['progress']}")
            if bg.get("challenges"):
                context_parts.append(f"• Challenges: {bg['challenges']}")
            
            lit_count = data.get("literature_count", 0)
            context_parts.append(f"\n  [Reference Count: {lit_count}]")
        
        context_parts.append("\n" + "=" * 50)
        
        return "\n".join(context_parts)
