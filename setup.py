from setuptools import setup, find_packages
import pathlib

# Read README with UTF-8 encoding
HERE = pathlib.Path(__file__).parent
README = (HERE / "README.md").read_text(encoding="utf-8")

setup(
    name="azmig_tool",
    version="3.0.0",
    packages=find_packages(),
    install_requires=[
        "rich",
        "pandas",
        "openpyxl",
        "azure-identity",
        "azure-mgmt-resource",
        "azure-mgmt-compute",
        "azure-mgmt-network",
        "azure-mgmt-authorization",
        "azure-mgmt-recoveryservices",
        "azure-core",
        "requests"
    ],
    entry_points={
        "console_scripts": [
            "azmig=azmig_tool.interface.cli:main",
        ],
    },
    author="Atef Aziz",
    description="Azure Bulk Migration CLI Tool with REST API client",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/atef-aziz/azmig_tool",
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: System Administrators",
        "Topic :: System :: Systems Administration",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
