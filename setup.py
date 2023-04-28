from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="nanomesh",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description=
    "A library to easily manage and configure local Nano networks for testing and development",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/nanomesh",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    python_requires=">=3.8",
    install_requires=[],
)
