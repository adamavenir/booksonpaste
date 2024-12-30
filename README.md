# booksonpaste

Generate text snippets from classic literature. Useful for testing text input fields, token windows, and text processing systems.

## Features

- Generate text in character or token counts
- Copy directly to clipboard or output to file/stdout
- Uses actual literature instead of lorem ipsum
- Maintains natural paragraph structure
- Smart text wrapping that preserves narrative flow
- Automatic cache management for faster subsequent runs
- Cross-book text generation for larger outputs

## Installation

```bash
# Install with pipx (recommended)
pipx install git+https://github.com/adamavenir/booksonpaste.git

# Or with pip
pip install git+https://github.com/adamavenir/booksonpaste.git
```

## Usage

```bash
# Basic usage - copy to clipboard
bop 100k               # 100,000 characters
bop -t 1m             # 1 million tokens

# Output options
bop 50k -s            # Output to stdout
bop -t 100 -f out.txt # Write to file
bop --gen 100k        # Just generate (same as -s)

# Size formats
bop 100               # 100 characters
bop 50k               # 50,000 characters
bop 1m                # 1,000,000 characters
bop 1mm               # 1,000,000 characters (alternative)
bop -t 100            # 100 tokens

# Cache management
bop --clear           # Clear the cache
bop --new 100k        # Clear cache and generate new text

# Debug output
bop 100k --debug      # Show detailed progress information
```

## Source Texts

Content is drawn from classic literature available through Project Gutenberg, including works from:
- British Literature (Pride and Prejudice, Great Expectations, etc.)
- American Literature (Moby Dick, The Yellow Wallpaper, etc.)
- Gothic and Mystery (Dracula, Frankenstein, etc.)
- Early Science Fiction (The Time Machine, War of the Worlds, etc.)
- Adventure and Historical (Treasure Island, The Three Musketeers, etc.)
- Social Commentary (Little Women, The Picture of Dorian Gray, etc.)

Text is cached locally in `~/.booksonpaste/cache` for faster subsequent runs. The cache is automatically managed:
- First run automatically initializes the cache
- `--clear` command to manually clear the cache
- `--new` flag to refresh cache and generate new text

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/adamavenir/booksonpaste.git
cd booksonpaste

# Install in development mode with test dependencies
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run tests with coverage report
pytest --cov=booksonpaste

# Run specific test file
pytest tests/test_bop.py
```

The test suite covers:
- Size parsing and formatting
- Text generation and wrapping
- Token counting
- Cache management
- Output formatting

## Why?

I originally created this tool to test the input limits of the Claude and ChatGPT interfaces for [cpai](https://github.com/adamavenir/cpai). These apps don't have clearly documented limits on what you can paste into them. This tool helps you generate text of specific sizes—useful for testing these limits as well as any other text processing systems.

"Lorem ipsum" is fine for visual placeholders, but when you need to test systems that process natural language (tokenizers, parsers, etc.), you want real text with natural word frequencies, punctuation, and structure.
