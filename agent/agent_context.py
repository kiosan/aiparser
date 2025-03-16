from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class AgentContext:
    website_url: str
    product_urls: List[str]
    company_info: Dict[str, Any]
    is_producer: bool = False
    is_distributor: bool = False
    is_wholesaler: bool = False