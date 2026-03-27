
from setuptools import setup, find_packages
import glob, os

# Collect config/ files for distribution
config_files = []
for root, dirs, files in os.walk("config"):
    for f in files:
        config_files.append(os.path.join(root, f))

setup(
    name="indyforge",
    version="0.1.0",
    description="Raiders of the Lost Architecture – AI multi-agent docs generator",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "langgraph>=0.1.5",
        "langchain-community",
        "langchain-core>=0.2.0",
        "langchain-ollama",
        "tree-sitter",
        "click",
        "python-dotenv",
        "pyyaml>=6.0.0",
    ],
    data_files=[
        (root, [os.path.join(root, f) for f in files])
        for root, dirs, files in os.walk("config") if files
    ],
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "indyforge=indyforge.cli:main",
        ],
    },
    python_requires=">=3.11",
)
