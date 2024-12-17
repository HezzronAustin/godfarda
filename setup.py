from setuptools import setup, find_packages

setup(
    name="ai-tools-ecosystem",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "aiohttp",
        "pytest",
        "pytest-asyncio",
        "pytest-cov"
    ],
)