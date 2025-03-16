#!/usr/bin/env python3
"""
Prompt storage utility module.
Reads prompts from a plain text file by key.
"""

import os
import re
import logging
from typing import Dict, Optional, List

# Configure logging
logger = logging.getLogger(__name__)

class PromptStorage:
    """Class for retrieving prompts from a text file by key."""
    
    def __init__(self, file_path: str = "prompts.txt"):
        """
        Initialize the prompt storage.
        
        Args:
            file_path: Path to the prompts text file (default: prompts.txt)
        """
        self.file_path = file_path
        self._prompts_cache: Dict[str, str] = {}
        self._last_modified_time = 0
        self._load_prompts()
    
    def _load_prompts(self) -> None:
        """
        Load prompts from the text file into the cache.
        Automatically called during initialization and when getting a prompt
        if the file has been modified.
        """
        try:
            if not os.path.exists(self.file_path):
                logger.warning(f"Prompts file not found: {self.file_path}")
                return
            
            # Check if file has been modified since last load
            current_mtime = os.path.getmtime(self.file_path)
            if current_mtime <= self._last_modified_time:
                return  # File hasn't changed, use cached prompts
            
            self._last_modified_time = current_mtime
            self._prompts_cache = {}
            
            logger.info(f"Loading prompts from {self.file_path}")
            
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Split by prompt keys ([KEY])
            # This regex finds all [KEY] patterns and splits the content accordingly
            pattern = r'\[([A-Z0-9_]+)\]'
            matches = list(re.finditer(pattern, content))
            
            # Skip lines that are commented out
            key_positions = []
            for m in matches:
                # Check if this key is on a commented line
                line_start = content.rfind('\n', 0, m.start())
                if line_start == -1:  # This is the first line
                    line_start = 0
                else:
                    line_start += 1  # Skip the newline character
                    
                line_before_key = content[line_start:m.start()].strip()
                if not line_before_key.startswith('#'):
                    key_positions.append((m.group(1), m.start()))
            
            # Process each key and its content
            for i, (key, pos) in enumerate(key_positions):
                # Determine the end position of this prompt
                end_pos = key_positions[i+1][1] if i < len(key_positions) - 1 else len(content)
                
                # Extract the prompt text (skip the key itself)
                start_pos = pos + len(key) + 2  # +2 for the brackets
                prompt_text = content[start_pos:end_pos].strip()
                
                # Remove comment lines
                prompt_lines = [line for line in prompt_text.split('\n') 
                               if not line.strip().startswith('#')]
                clean_prompt = '\n'.join(prompt_lines).strip()
                
                self._prompts_cache[key] = clean_prompt
                logger.debug(f"Loaded prompt with key: {key}")
            
            logger.info(f"Successfully loaded {len(self._prompts_cache)} prompts")
            
        except Exception as e:
            logger.error(f"Error loading prompts: {e}")
    
    def get_prompt(self, key: str) -> Optional[str]:
        """
        Get a prompt by its key.
        
        Args:
            key: The key of the prompt to retrieve
            
        Returns:
            The prompt text or None if not found
        """
        # Reload prompts if file has been modified
        self._load_prompts()
        
        if key not in self._prompts_cache:
            logger.warning(f"Prompt key not found: {key}")
            return None
        
        return self._prompts_cache[key]
    
    def get_all_keys(self) -> List[str]:
        """
        Get all available prompt keys.
        
        Returns:
            List of available prompt keys
        """
        # Reload prompts if file has been modified
        self._load_prompts()
        
        return list(self._prompts_cache.keys())

# Create a singleton instance
_prompt_storage = None

def get_prompt_storage(file_path: str = "prompts.txt") -> PromptStorage:
    """
    Get the singleton instance of PromptStorage.
    
    Args:
        file_path: Path to the prompts text file (default: prompts.txt)
        
    Returns:
        PromptStorage instance
    """
    global _prompt_storage
    if _prompt_storage is None:
        _prompt_storage = PromptStorage(file_path)
    return _prompt_storage

def get_prompt(key: str, file_path: str = "prompts.txt") -> Optional[str]:
    """
    Convenience function to get a prompt by key.
    
    Args:
        key: The key of the prompt to retrieve
        file_path: Path to the prompts text file (default: prompts.txt)
        
    Returns:
        The prompt text or None if not found
    """
    return get_prompt_storage(file_path).get_prompt(key)
