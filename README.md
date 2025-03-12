# Web Scraping Agent

A Python agent that scrapes websites for product information using the Zyte API.

## Features

- Website crawling to discover product pages
- HTML retrieval using Zyte API with browser rendering
- HTML minimization for efficient processing including comment removal and base64 decoding
- Structured product information extraction including images
- Configurable scraping parameters and timeout handling
- Error resilience and fallback options

## Setup

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file with your Zyte API key:
   ```
   ZYTE_API_KEY=your_api_key_here
   ```

## Usage

### Testing the Zyte API Connection

First, verify your API connection is working correctly:

```bash
# Run the comprehensive test suite
./run_tests.sh

# Or run a specific test directly
python3 tests/integration/test_zyte_api.py https://example.com --timeout 15

# Run unit tests
python3 -m unittest discover -s tests/unit
```

### Using the Scraper Agent

```python
from scraper.agent import ScraperAgent

# Initialize the agent with browser rendering enabled (default)
agent = ScraperAgent(use_browser=True)

# Start scraping a website
products = agent.scrape_website_sync("https://example.com")

# Process the products
for product in products:
    print(f"Product: {product.name}, Price: {product.price}")
    print(f"Images: {product.images}")
```

### HTML Minimization Example

```bash
# Fetch a URL, minimize the HTML and output to console
python examples/html_minimizer_example.py https://example.com -u

# Save to file and disable browser rendering (faster)
python examples/html_minimizer_example.py https://example.com -u --no-browser -o output.html

# Control request timeout
python examples/html_minimizer_example.py https://example.com -u --timeout 20

# Process a local HTML file
python examples/html_minimizer_example.py path/to/file.html
```

### HTML Minimization Features

The HTML minimizer performs several optimizations:

- **Removes unnecessary elements**: SVG, scripts, styles, forms, buttons, etc.
- **Strips HTML comments**: All comments including multi-line and conditional comments
- **Handles base64 encoded content**: Automatically detects and decodes base64 encoded responses
- **Removes unnecessary attributes**: Preserves only essential attributes like src, href, and title
- **Removes elements with data URLs**: Eliminates embedded images and resources

## Troubleshooting

### Common Issues

1. **API Connection Errors**:
   - Verify your Zyte API key in the `.env` file
   - Check that your Zyte account has an active subscription
   - Try running with `--no-browser` flag which uses less resources

2. **Timeouts**:
   - Increase the timeout parameter: `--timeout 30` or higher
   - Some sites may take longer to render with browser rendering

3. **Memory Usage**:
   - HTML minimization significantly reduces memory usage
   - For large websites, consider processing in batches

4. **Base64 Encoded Content**:
   - Some APIs return HTML content as base64 encoded strings
   - The minimizer will automatically attempt to decode this content
   - If decoding fails, an error message will be shown

5. **Python 3.13 Compatibility**:
   - This project is compatible with Python 3.13 and higher
   - Some dependencies might require specific versions in requirements.txt

## License

MIT
