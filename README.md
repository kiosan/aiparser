# Web Scraper with OpenAI Agents and Zyte Client

This project integrates OpenAI Agents with Zyte Client to scan websites for products and company details, storing the results in JSON format.

## Project Structure

```
.
├── .env                 # Environment variables (API keys)
├── .env.example         # Example environment variables file
├── batch_scraper.py     # Process multiple URLs in batch mode
├── Dockerfile           # Docker configuration
├── docker-compose.yml   # Docker Compose configuration
├── processed.txt        # Tracks processed websites with product counts
├── requirements.txt     # Python dependencies
├── setup.sh             # Setup script for local development
├── uavs.txt             # List of URLs to process in batch mode
└── scraper/
    ├── __init__.py
    ├── html_processor.py  # HTML processing utilities
    ├── zyte_client.py     # Zyte API client
    ├── openai_agent.py    # OpenAI Agent implementation
    └── main.py            # Main application entry point
```

## Setup

### Local Development

1. Create a virtual environment:
   ```
   ./setup.sh
   ```

2. Activate the virtual environment:
   ```
   source venv/bin/activate
   ```

3. Add your API keys to the `.env` file:
   ```
   ZYTE_API_KEY=your_zyte_api_key_here
   OPENAI_API_KEY=your_openai_api_key_here
   ```

### Using Docker

1. Add your API keys to the `.env` file (same as above)

2. Build the Docker image:
   ```
   docker-compose build
   ```

3. Run the scraper with Docker:
   ```
   docker-compose run scraper https://example.com
   ```

## Usage

### Command Line Arguments

```
python -m scraper.main [URL] [OPTIONS]
```

Options:
- `--output`, `-o`: Output directory for scraped data (default: "output")
- `--type`, `-t`: Type of information to extract: "product", "company", or "auto" (default: "auto")
- `--browser`, `-b`: Use browser rendering for scraping
- `--verbose`, `-v`: Enable verbose output

### Examples

1. Scrape product information from a website:
   ```
   python -m scraper.main https://example.com/product --type product
   ```

2. Scrape company information with browser rendering:
   ```
   python -m scraper.main https://example.com --type company --browser
   ```

3. Run with Docker:
   ```
   docker-compose run scraper https://example.com --type auto --browser
   ```

### Batch Processing

The project includes a batch scraper to process multiple URLs from a file:

```
python batch_scraper.py [OPTIONS]
```

Options:
- `--file`: File containing URLs to process, one per line (default: "uavs.txt")
- `--output`: Output directory for results (default: "output")
- `--type`: Type of scraper to use (auto, agent, manual) (default: "auto")
- `--browser`: Use browser rendering for scraping (default: true)
- `--limit`: Limit the number of URLs to process (0 for no limit)
- `--delay`: Delay between URL processing in seconds (default: 2)
- `--retries`: Number of retry attempts for failed URLs (default: 1)
- `--retry-delay`: Initial delay between retries in seconds (default: 5)
- `--log-file`: Log file path (in addition to console output)
- `--skip-processed`: Skip URLs that have already been processed (checks output files)
- `--skip-in-processed-file`: Skip URLs that are listed in processed.txt file (default: true)
- `--debug`: Enable debug logging

### Processing Tracking System

The batch scraper includes a processing tracking system:

1. Processed websites are tracked in a `processed.txt` file with the following format:
   ```
   domain.com - <number of products>
   ```

2. By default, the system skips websites found in `processed.txt` during batch processing.

3. You can disable this behavior with `--skip-in-processed-file=false`

Example of batch processing:
```
python batch_scraper.py --file uavs.txt --output output --retries 3
```

## Output

The scraped data is saved as JSON files in the output directory. The filename is generated based on the domain and timestamp:
```
output/example_com_20250315_165400.json
```
