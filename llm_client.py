import requests
import json
import re
from typing import Dict, Any, Optional
from config import API_URL, LLM_MODEL_NAME, REQUEST_TIMEOUT, MAX_RETRIES, LLM_TEMPERATURE, LLM_TOP_P, LLM_MAX_TOKENS, OPENAI_API_KEY
import os


class LLMClient:
    """Client for communicating with the local LLM API"""
    
    def __init__(self):
        self.api_url = API_URL
        self.model_name = LLM_MODEL_NAME
        self.timeout = REQUEST_TIMEOUT
        self.max_retries = MAX_RETRIES
        self.default_temperature = LLM_TEMPERATURE
        self.default_top_p = LLM_TOP_P
        self.max_tokens = LLM_MAX_TOKENS
    
    def _filter_thinking_process(self, text: str) -> str:
        """Filter out thinking process wrapped in <think></think> tags"""
        # Remove content between <think> and </think> tags
        filtered_text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
        return filtered_text.strip()
    
    def generate_response(self, messages: list, temperature: float = None, top_p: float = None, preserve_thinking: bool = False) -> Optional[str]:
        """
        Generate response from LLM
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Sampling temperature (uses config default if None)
            top_p: Nucleus sampling parameter (uses config default if None)
            preserve_thinking: Whether to preserve thinking process in <think></think> tags
            
        Returns:
            Generated response text or None if failed
        """
        # Use config defaults if not specified
        if temperature is None:
            temperature = self.default_temperature
        if top_p is None:
            top_p = self.default_top_p
            
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": self.max_tokens
        }
        
        for attempt in range(self.max_retries):
            try:
                headers = {"Content-Type": "application/json"}
                # Add Authorization header for OpenAI API
                if "openai.com" in self.api_url:
                    if not OPENAI_API_KEY:
                        raise RuntimeError("OPENAI_API_KEY not set in config.py")
                    headers["Authorization"] = f"Bearer {OPENAI_API_KEY}"
                response = requests.post(
                    self.api_url,
                    json=payload,
                    timeout=self.timeout,
                    headers=headers
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if 'choices' in result and len(result['choices']) > 0:
                        content = result['choices'][0]['message']['content']
                        
                        # Filter thinking process only if preserve_thinking is False
                        if preserve_thinking:
                            return content
                        else:
                            filtered_content = self._filter_thinking_process(content)
                            return filtered_content
                    else:
                        print(f"Unexpected response format: {result}")
                        
                else:
                    print(f"API request failed with status {response.status_code}: {response.text}")
                    
            except requests.exceptions.RequestException as e:
                print(f"Request failed (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt == self.max_retries - 1:
                    return None
                    
        return None
    
    def test_connection(self) -> bool:
        """Test if the LLM API is accessible"""
        test_messages = [
            {"role": "user", "content": "Hello, please respond with 'Connection successful'"}
        ]
        
        response = self.generate_response(test_messages)
        return response is not None 