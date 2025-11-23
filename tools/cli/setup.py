"""Setup script for JARVIS CLI."""

from setuptools import setup, find_packages

setup(
    name="jarvis-cli",
    version="1.0.0",
    description="JARVIS AI Assistant Command Line Interface",
    author="JARVIS Team",
    py_modules=["jarvis_cli"],
    install_requires=[
        "requests>=2.28.0",
    ],
    extras_require={
        "clipboard": ["pyperclip>=1.8.0"],
    },
    entry_points={
        "console_scripts": [
            "jarvis=jarvis_cli:main",
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development",
        "Topic :: Software Development :: Code Generators",
    ],
)
