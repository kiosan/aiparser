#!/usr/bin/env python3
"""
OpenAI Agent implementation for web scraping.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv
from agents import Agent, Runner, RunContextWrapper, FunctionTool, function_tool
from agent.agent_context import AgentContext

# Import other necessary modules
from scraper.html_processor import HtmlProcessor
from scraper.zyte_client import ZyteClient
from pydantic import BaseModel, ConfigDict


# Add parent directory to path for imports
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import prompt storage
from utils.prompt_storage import get_prompt

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

class FunctionArgs(BaseModel):
    url: str



class OpenAIAgent:
    """Agent for processing website content using OpenAI API."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "o3-mini", prompts_file: str = "prompts.txt", browser: bool = False):
        """
        Initialize the OpenAI Agent.
        
        Args:
            api_key: OpenAI API key. If None, it will be loaded from the OPENAI_API_KEY environment variable.
            model: OpenAI model to use (default: gpt-4o)
            prompts_file: Path to the prompts file (default: prompts.txt)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set it via OPENAI_API_KEY environment variable or constructor parameter.")
        
        self.model = model
        self.browser = browser
        self.prompts_file = prompts_file
        logger.debug(f"Initializing OpenAI client with model: {self.model}")
        
        # Initialize OpenAI client
        self.client = OpenAI(api_key=self.api_key)

        

        logger.debug("OpenAI Agent initialized successfully")
    
    @function_tool(name_override="get_page_content")
    def get_page_content(ctx: RunContextWrapper[Any], url: str) -> str:
        logger.error(f"Fetching HTML content from {url}")
        zyte_client = ZyteClient()
        html_content = zyte_client.get_html(url, browser=True)  # Using browser-rendered content
        if not html_content:
            logger.error("Failed to retrieve HTML content")
            return {"error": "Failed to retrieve HTML content"}
        
        # Process HTML content
        processed_html = HtmlProcessor.minimize_html(html_content)
        return processed_html
            
    async def run(self, url: str) -> Dict[str, Any]:
        # Initialize the agent with proper parameters
        # Get the product URLs extraction prompt from the prompts file
        prompt = get_prompt("EXTRACT_PRODUCT_URLS", self.prompts_file)
        if not prompt:
            logger.warning("Product URLs extraction prompt not found, using default prompt")
            prompt = f"Extract product URLs in JSON format from the website at {url}.\n\nReturn a list of all product page URLs found on the site in JSON format without any additional text."
        else:
            # Replace the URL placeholder with the actual URL
            prompt = prompt.replace("{url}", url)
            
        agent = Agent[AgentContext](
            name="Website processor",
            instructions=prompt,
            tools=[self.get_page_content],
            model="o3-mini",
        )

        website_context = AgentContext(website_url=url, product_urls=[], company_info={})
        
        result = await Runner.run(
            starting_agent=agent, 
            input="Start with fetching HTML from all necessary pages of the website.",
            context=website_context,
        )
        

        return result.final_output

    def summarize_webpage(self, html_content: str) -> str:
        """
        Generate a summary of the webpage content using OpenAI.
        
        Args:
            html_content: HTML content of the webpage
            
        Returns:
            Summary of the webpage content
        """
        logger.info("Generating webpage summary")
        
        # Get the webpage summary prompt from the prompts file
        prompt = get_prompt("WEBPAGE_SUMMARY", self.prompts_file)
        if not prompt:
            logger.warning("Webpage summary prompt not found, using default prompt")
            prompt = "Provide a concise summary of the webpage content in 200 words or less."
        
        try:
            # Create a chat completion request with the prompt and HTML content
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": f"HTML Content: {html_content[:50000]}..."}
                ]
            )
            
            # Extract the response
            summary = response.choices[0].message.content
            logger.info(f"Successfully generated webpage summary ({len(summary)} chars)")
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating webpage summary: {e}")
            return f"Failed to generate summary: {str(e)}"


    def extract_product_info(self, html_content: str) -> Dict[str, Any]:
        """
        Extract product information from HTML content using OpenAI.
        
        Args:
            html_content: HTML content of the product page
            
        Returns:
            Dictionary containing extracted product information
        """
        logger.info("Extracting product information from HTML content")
        
        # Get the product extraction prompt from the prompts file
        prompt = get_prompt("PRODUCT_EXTRACTION", self.prompts_file)
        if not prompt:
            logger.warning("Product extraction prompt not found, using default prompt")
            prompt = "Extract all product information from the HTML and return as JSON."
        
        try:
            # Create a chat completion request with the prompt and HTML content
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": f"HTML Content: {html_content[:50000]}..."}
                ],
                response_format={"type": "json_object"}
            )
            
            # Extract the JSON response
            result_text = response.choices[0].message.content
            logger.debug(f"Received response from OpenAI: {result_text[:500]}...")
            
            # Parse the JSON response
            result = json.loads(result_text)
            logger.info(f"Successfully extracted product information with {len(result)} fields")
            
            return result
            
        except Exception as e:
            logger.error(f"Error extracting product information: {e}")
            
            # Try to use the error handling prompt
            error_prompt = get_prompt("ERROR_HANDLING", self.prompts_file)
            if error_prompt:
                return {"error": error_prompt}
            else:
                return {"error": f"Failed to extract product information: {str(e)}"}
    
    def extract_company_info(self, html_content: str) -> Dict[str, Any]:
        """
        Extract company information from HTML content using OpenAI.
        
        Args:
            html_content: HTML content of the company page
            
        Returns:
            Dictionary containing extracted company information
        """
        logger.info("Extracting company information from HTML content")
        
        # Get the company extraction prompt from the prompts file
        prompt = get_prompt("COMPANY_EXTRACTION", self.prompts_file)
        if not prompt:
            logger.warning("Company extraction prompt not found, using default prompt")
            prompt = "Extract all company information from the HTML and return as JSON."
        
        try:
            # Create a chat completion request with the prompt and HTML content
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": f"HTML Content: {html_content[:50000]}..."}
                ],
                response_format={"type": "json_object"}
            )
            
            # Extract the JSON response
            result_text = response.choices[0].message.content
            logger.debug(f"Received response from OpenAI: {result_text[:500]}...")
            
            # Parse the JSON response
            result = json.loads(result_text)
            logger.info(f"Successfully extracted company information with {len(result)} fields")
            
            return result
            
        except Exception as e:
            logger.error(f"Error extracting company information: {e}")
            
            # Try to use the error handling prompt
            error_prompt = get_prompt("ERROR_HANDLING", self.prompts_file)
            if error_prompt:
                return {"error": error_prompt}
            else:
                return {"error": f"Failed to extract company information: {str(e)}"}
    
    def save_to_json(self, data: Dict[str, Any], output_file: str) -> None:
        """
        Save extracted data to a JSON file.
        
        Args:
            data: Data to save
            output_file: Path to the output file
        """
        logger.info(f"Saving data to {output_file}")
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Data saved successfully to {output_file}")

