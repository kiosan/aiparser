from setuptools import setup, find_packages

setup(
    name="scraper",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "requests",
        "zyte-api>=0.7.0",
        "beautifulsoup4",
        "lxml>=4.6.0",
        "dataclasses-json",
        "python-dotenv",
        "openai>=1.0.0",
        "argparse",
        "urllib3"
    ],
    python_requires=">=3.8",
)
