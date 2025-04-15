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

# Set up more detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
class FunctionArgs(BaseModel):
    url: str



class OpenAIAgent:
    """Agent for processing website content using OpenAI API."""
    # o3-mini model is used for faster processing
    # gpt-4o is used for more complex tasks
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
        logger.debug(f"Fetching HTML content from {url}")
        zyte_client = ZyteClient()
        html_content = zyte_client.get_html(url, browser=True)  # Using browser-rendered content
        if not html_content:
            logger.error("Failed to retrieve HTML content")
            return {"error": "Failed to retrieve HTML content"}
        
        
        return html_content
            
    async def run(self, url: str) -> Dict[str, Any]:
        # Initialize the agent with proper parameters
        # Get the product URLs extraction prompt from the prompts file
        prompt = get_prompt("EXTRACT_PRODUCT_URLS", self.prompts_file)
        
        # Replace the URL placeholder with the actual URL
        prompt = prompt.replace("{url}", url)
            
        agent = Agent[AgentContext](
            name="Website processor",
            instructions=prompt,
            tools=[self.get_page_content],
            model=self.model,
        )

        website_context = AgentContext(website_url=url, product_urls=[], company_info={})
        
        result = await Runner.run(
            starting_agent=agent, 
            input="Start with fetching HTML from all necessary pages of the website.",
            context=website_context,
        )
        
        # Get the product URLs extraction prompt from the prompts file
        parsed_data = json.loads(result.final_output)
        # Safely access product_urls, defaulting to empty list if key doesn't exist
        product_urls = parsed_data.get("product_urls", [])
        parsed_data["products"] = []
        logger.debug(f"Found {len(product_urls)} product URLs")
        for product_url in product_urls:
            logger.debug(f"Processing product URL: {product_url}")
            prompt = get_prompt("PRODUCT_EXTRACTION", self.prompts_file)
            prompt = prompt.replace("{url}", product_url["url"])
            prompt = prompt.replace("{name}", product_url["product_name"])

            agent = Agent[AgentContext](
                name="Product Extractor",
                instructions=prompt,
                tools=[self.get_page_content],
                model=self.model,
            )

            product_context = AgentContext(website_url=url, product_urls=[], company_info={})
       
            product_result = await Runner.run(
                starting_agent=agent, 
                input="Start with fetching HTML from a given product page URL.",
                context=product_context,
            )
            product_info = json.loads(product_result.final_output)
            
            # Add product information to the final output
            parsed_data["products"].append(product_info)
        
        return parsed_data
    
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

