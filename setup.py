
from setuptools import setup, find_packages

setup(
    name="indyforge",
    version="0.1.0",
    description="Raiders of the Lost Architecture – AI multi-agent docs generator",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "langgraph>=0.1.5",
        "langchain-community",
        "langchain-ollama",
        "tree-sitter",
        "click",
        "python-dotenv",
    ],
    entry_points={
        "console_scripts": [
            "indyforge=indyforge.cli:main",
        ],
    },
    python_requires=">=3.11",
)
