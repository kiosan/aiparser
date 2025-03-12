import re
from typing import Optional
from bs4 import BeautifulSoup

class HtmlProcessor:
    """Class for processing and minimizing HTML content."""
    
    @staticmethod
    def minimize_html(html: str) -> str:
        """
        Minimize HTML content by removing unnecessary elements, attributes, and whitespace.
        
        Args:
            html: The HTML content to minimize
            
        Returns:
            Minimized HTML content
        """
        if not html:
            return ""
        
        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(html, 'lxml')
        
        # Remove unwanted elements
        for selector in ['svg', 'style', 'form', 'button', 'script', 'select', 
                         'link', 'pages-css', 'noscript']:
            for element in soup.select(selector):
                element.decompose()
        
        # Remove comments
        from bs4 import Comment
        for comment in soup.find_all(text=lambda text: isinstance(text, Comment)):
            comment.extract()
        
        # Process all elements to remove attributes
        for element in soup.find_all():
            # Skip meta tags
            if element.name == "meta":
                continue
                
            # Remove all attributes except src, href, and title
            allowed_attrs = ["src", "href", "title"]
            attrs_to_remove = [attr for attr in element.attrs.keys() if attr not in allowed_attrs]
            for attr in attrs_to_remove:
                del element[attr]
            
            # Remove elements with data URLs in src
            if element.has_attr('src') and element['src'].startswith('data'):
                element.decompose()
        
        # Convert to string
        result = str(soup)
        
        # Remove tabs and newlines
        result = re.sub(r'\t+', '', result)
        result = re.sub(r'\n+', '', result)
        
        # Replace certain tags with shorter versions
        result = re.sub(r'<\/span>', '</s>', result)
        result = re.sub(r'<\/div>', '</d>', result)
        result = re.sub(r'<span>', '<s>', result)
        result = re.sub(r'<div>', '<d>', result)
        
        # Remove whitespace between tags (additional optimization)
        result = re.sub(r'>\s+<', '><', result)
        
        return result.strip()
    
    @staticmethod
    def extract_text(html: str, selector: str) -> Optional[str]:
        """
        Extract text content from HTML using a CSS selector.
        
        Args:
            html: The HTML content
            selector: CSS selector for the element
            
        Returns:
            Extracted text or None if not found
        """
        soup = BeautifulSoup(html, 'lxml')
        element = soup.select_one(selector)
        if element:
            return element.get_text().strip()
        return None
    
    @staticmethod
    def extract_multiple_texts(html: str, selector: str) -> list:
        """
        Extract text from multiple elements using a CSS selector.
        
        Args:
            html: The HTML content
            selector: CSS selector for the elements
            
        Returns:
            List of extracted texts
        """
        soup = BeautifulSoup(html, 'lxml')
        elements = soup.select(selector)
        return [element.get_text().strip() for element in elements]
    
    @staticmethod
    def extract_attribute(html: str, selector: str, attribute: str) -> Optional[str]:
        """
        Extract attribute value from an HTML element using a CSS selector.
        
        Args:
            html: The HTML content
            selector: CSS selector for the element
            attribute: The attribute to extract
            
        Returns:
            Attribute value or None if not found
        """
        soup = BeautifulSoup(html, 'lxml')
        element = soup.select_one(selector)
        if element and element.has_attr(attribute):
            return element[attribute]
        return None
    
    @staticmethod
    def extract_multiple_attributes(html: str, selector: str, attribute: str) -> list:
        """
        Extract attribute values from multiple HTML elements using a CSS selector.
        
        Args:
            html: The HTML content
            selector: CSS selector for the elements
            attribute: The attribute to extract
            
        Returns:
            List of attribute values
        """
        soup = BeautifulSoup(html, 'lxml')
        elements = soup.select(selector)
        return [element[attribute] for element in elements if element.has_attr(attribute)]
