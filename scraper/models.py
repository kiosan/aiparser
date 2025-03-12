from dataclasses import dataclass, field
from typing import List, Dict, Optional
from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class Product:
    """Model representing a scraped product."""
    
    url: str
    name: str
    description: Optional[str] = None
    price: Optional[str] = None
    currency: Optional[str] = None
    images: List[str] = field(default_factory=list)
    specifications: Dict[str, str] = field(default_factory=dict)
    availability: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    raw_html: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert the product to a dictionary."""
        return self.to_dict()
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Product':
        """Create a product from a dictionary."""
        return cls.from_dict(data)
