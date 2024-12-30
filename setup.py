from setuptools import setup, find_packages

setup(
    name="booksonpaste",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "tiktoken>=0.5.1",
        "requests>=2.31.0",
    ],
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'pytest-cov>=4.0.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'bop=booksonpaste.bop:main',
        ],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="Generate text snippets from classic books",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/booksonpaste",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
