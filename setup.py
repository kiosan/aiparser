from setuptools import setup, find_packages

setup(
    name="aidrones-scraper",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "beautifulsoup4>=4.9.0",
        "python-dotenv>=0.15.0",
        "lxml>=4.6.0",
        "aiohttp>=3.7.0",
        "zyte-api>=0.8.0",
    ],
    python_requires=">=3.8",
)
