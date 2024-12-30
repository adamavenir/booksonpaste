#!/usr/bin/env python3
import sys
import random
import subprocess
import argparse
import re
import tiktoken
from pathlib import Path
import requests
from typing import Union, Optional
import tempfile
import os

# Cache directory for downloaded texts
CACHE_DIR = Path.home() / '.booksonpaste' / 'cache'

# Project Gutenberg texts to use (public domain classics)
GUTENBERG_TEXTS = [
    # British Literature
    ('https://www.gutenberg.org/cache/epub/1342/pg1342.txt', 'pride_prejudice'),    # Pride and Prejudice
    ('https://www.gutenberg.org/cache/epub/161/pg161.txt', 'sense_sensibility'),    # Sense and Sensibility
    ('https://www.gutenberg.org/cache/epub/768/pg768.txt', 'wuthering_heights'),    # Wuthering Heights
    ('https://www.gutenberg.org/cache/epub/98/pg98.txt', 'tale_two_cities'),        # Tale of Two Cities
    ('https://www.gutenberg.org/cache/epub/145/pg145.txt', 'middlemarch'),          # Middlemarch
    ('https://www.gutenberg.org/cache/epub/158/pg158.txt', 'emma'),                 # Emma
    ('https://www.gutenberg.org/cache/epub/1400/pg1400.txt', 'great_expectations'), # Great Expectations

    # American Literature
    ('https://www.gutenberg.org/cache/epub/1952/pg1952.txt', 'yellow_wallpaper'),   # The Yellow Wallpaper
    ('https://www.gutenberg.org/cache/epub/1250/pg1250.txt', 'anthem'),             # Anthem
    ('https://www.gutenberg.org/cache/epub/76/pg76.txt', 'huck_finn'),              # Huckleberry Finn
    ('https://www.gutenberg.org/cache/epub/2701/pg2701.txt', 'moby_dick'),          # Moby Dick
    ('https://www.gutenberg.org/cache/epub/64317/pg64317.txt', 'age_innocence'),    # The Age of Innocence
    ('https://www.gutenberg.org/cache/epub/113/pg113.txt', 'secret_garden'),        # The Secret Garden

    # Gothic and Mystery
    ('https://www.gutenberg.org/cache/epub/84/pg84.txt', 'frankenstein'),           # Frankenstein
    ('https://www.gutenberg.org/cache/epub/1661/pg1661.txt', 'sherlock'),           # Sherlock Holmes
    ('https://www.gutenberg.org/cache/epub/345/pg345.txt', 'dracula'),              # Dracula
    ('https://www.gutenberg.org/cache/epub/43/pg43.txt', 'jekyll_hyde'),            # Dr. Jekyll and Mr. Hyde
    ('https://www.gutenberg.org/cache/epub/3268/pg3268.txt', 'mysteries_udolpho'),  # The Mysteries of Udolpho

    # Early Science Fiction
    ('https://www.gutenberg.org/cache/epub/35/pg35.txt', 'time_machine'),           # The Time Machine
    ('https://www.gutenberg.org/cache/epub/36/pg36.txt', 'war_worlds'),             # The War of the Worlds
    ('https://www.gutenberg.org/cache/epub/209/pg209.txt', 'turn_screw'),           # The Turn of the Screw
    ('https://www.gutenberg.org/cache/epub/624/pg624.txt', 'looking_backward'),     # Looking Backward

    # Adventure and Historical
    ('https://www.gutenberg.org/cache/epub/120/pg120.txt', 'treasure_island'),      # Treasure Island
    ('https://www.gutenberg.org/cache/epub/1184/pg1184.txt', 'count_monte'),        # The Count of Monte Cristo
    ('https://www.gutenberg.org/cache/epub/1257/pg1257.txt', 'three_musketeers'),   # The Three Musketeers
    ('https://www.gutenberg.org/cache/epub/1259/pg1259.txt', 'twenty_years'),       # Twenty Years After

    # Social Commentary
    ('https://www.gutenberg.org/cache/epub/45/pg45.txt', 'anne_green_gables'),      # Anne of Green Gables
    ('https://www.gutenberg.org/cache/epub/174/pg174.txt', 'picture_dorian'),       # The Picture of Dorian Gray
    ('https://www.gutenberg.org/cache/epub/514/pg514.txt', 'little_women'),         # Little Women
    ('https://www.gutenberg.org/cache/epub/730/pg730.txt', 'oliver_twist'),         # Oliver Twist
]

def parse_size(size_str: str) -> int:
    """Parse size strings like '100', '100k', '1m', '1mm' into raw numbers."""
    size_str = size_str.lower()
    if size_str.endswith('mm') or size_str.endswith('m'):
        multiplier = 1_000_000
        size_str = size_str.rstrip('m')
    elif size_str.endswith('k'):
        multiplier = 1_000
        size_str = size_str.rstrip('k')
    else:
        multiplier = 1
    
    try:
        return int(float(size_str) * multiplier)
    except ValueError:
        raise ValueError(f"Invalid size format: {size_str}")

def ensure_cache_dir():
    """Create cache directory if it doesn't exist."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

def clear_cache():
    """Remove all cached text files."""
    if CACHE_DIR.exists():
        for file in CACHE_DIR.glob("*.txt"):
            file.unlink()

def ensure_clean_cache(print_message: bool = True):
    """Ensure cache directory exists and is clean. Optionally print a message."""
    clear_cache()
    ensure_cache_dir()
    if print_message:
        print("Cache cleared.", file=sys.stderr)

def download_text(url: str, filename: str) -> str:
    """Download and cache a text file."""
    cache_path = CACHE_DIR / f"{filename}.txt"
    
    if cache_path.exists():
        return cache_path.read_text(encoding='utf-8')
    
    response = requests.get(url)
    response.raise_for_status()
    text = response.text
    
    # Clean up Project Gutenberg headers and footers
    text = re.sub(r'\*\*\* START OF .+ PROJECT GUTENBERG .+ \*\*\*.*?\n', '', text, flags=re.DOTALL)
    text = re.sub(r'\*\*\* END OF .+ PROJECT GUTENBERG .+ \*\*\*.*', '', text, flags=re.DOTALL)
    
    # Cache the cleaned text
    ensure_cache_dir()
    cache_path.write_text(text, encoding='utf-8')
    return text

def is_cache_empty() -> bool:
    """Check if the cache directory is empty or doesn't exist."""
    return not CACHE_DIR.exists() or not any(CACHE_DIR.glob("*.txt"))

def get_random_text() -> str:
    """Get a random cached text, downloading if necessary."""
    if is_cache_empty():
        ensure_clean_cache(print_message=False)
    url, filename = random.choice(GUTENBERG_TEXTS)
    return download_text(url, filename)

def copy_to_clipboard(text: str) -> bool:
    """Copy text to macOS clipboard using pbcopy."""
    try:
        process = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
        process.communicate(text.encode('utf-8'))
        return True
    except Exception as e:
        print(f"Error copying to clipboard: {e}", file=sys.stderr)
        return False

def count_tokens(text: str) -> int:
    """Count tokens in text using tiktoken."""
    enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))

def format_number(n: int) -> str:
    """Format a number with commas."""
    return f"{n:,}"

def format_output(chars: int, tokens: int, output_type: str = 'clipboard') -> str:
    """Format the output message with the appropriate icon and numbers."""
    icons = {
        'clipboard': '📋',
        'stdout': '＞',
        'file': '📄'
    }
    return f"{icons[output_type]} {format_number(chars)} characters ({format_number(tokens)} tokens)"

def generate_text(target_size: int, mode: str = 'chars', debug: bool = False) -> str:
    """
    Generate text of approximately target_size.
    mode can be 'chars' or 'tokens'
    debug enables verbose output
    """
    print("Fetching text...", file=sys.stderr, end='', flush=True)
    source_text = get_random_text()
    if debug:
        print(f"\nSource text length: {len(source_text)}", file=sys.stderr)
    paragraphs = [p.strip() for p in source_text.split('\n\n') if p.strip()]
    if debug:
        print(f"Number of paragraphs: {len(paragraphs)}", file=sys.stderr)
    
    # If we don't have enough text from one source, get more
    while mode == 'chars' and sum(len(p) for p in paragraphs) < target_size * 1.2 or \
          mode == 'tokens' and sum(count_tokens(p) for p in paragraphs) < target_size * 1.2:
        print(".", file=sys.stderr, end='', flush=True)
        additional_text = get_random_text()
        additional_paragraphs = [p.strip() for p in additional_text.split('\n\n') if p.strip()]
        paragraphs.extend(additional_paragraphs)
    
    print("\nGenerating...", file=sys.stderr)
    if debug:
        print(f"Total paragraphs available: {len(paragraphs)}", file=sys.stderr)
    
    # Pick a random starting point
    start_idx = random.randint(0, len(paragraphs) - 1)
    if debug:
        print(f"Starting at paragraph {start_idx}", file=sys.stderr)
    
    result = []
    current_size = 0
    current_idx = start_idx
    
    # Keep adding paragraphs, wrapping around when we reach the end
    while True:
        paragraph = paragraphs[current_idx]
        
        if mode == 'tokens':
            next_size = count_tokens(paragraph)
        else:
            next_size = len(paragraph + '\n\n')  # Include newlines in size calculation
            
        # Stop if adding this paragraph would exceed target size
        if current_size + next_size > target_size:
            # If this is the first paragraph and it's too big, take a portion
            if not result:
                if mode == 'tokens':
                    words = paragraph.split()
                    partial = []
                    partial_size = 0
                    for word in words:
                        word_size = count_tokens(word + ' ')
                        if partial_size + word_size > target_size:
                            break
                        partial.append(word)
                        partial_size += word_size
                    if partial:
                        result.append(' '.join(partial) + '\n\n')
                else:
                    result.append(paragraph[:target_size - 2] + '\n\n')
            break
            
        result.append(paragraph + '\n\n')
        current_size += next_size
        if debug:
            print(f"Added paragraph {current_idx}, current size: {current_size}", file=sys.stderr)
        
        # Move to next paragraph, wrapping around if needed
        current_idx = (current_idx + 1) % len(paragraphs)
        
        # If we've wrapped around to the start point, break to avoid infinite loop
        if current_idx == start_idx:
            break
    
    return ''.join(result)

def main():
    try:
        parser = argparse.ArgumentParser(
            description='BooksOnPaste (bop) - Generate text from classic books',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  bop 100k             # Copy 100,000 characters to clipboard
  bop -t 1m           # Copy 1 million tokens to clipboard
  bop 50k -s          # Output 50k characters to stdout
  bop -t 100 -f out.txt  # Write 100 tokens to file
  bop 1m --new        # Clear cache and generate new text
  bop --gen 100k      # Just generate text without copying/saving
  bop --clear         # Clear the cache without generating text
  bop 100k --debug    # Show detailed progress information"""
        )
        parser.add_argument('size', nargs='?', help='Amount of text to generate (e.g., 100, 100k, 1m)')
        parser.add_argument('-t', '--tokens', action='store_true', help='Count in tokens instead of characters')
        parser.add_argument('-s', '--stdout', action='store_true', help='Output to stdout instead of clipboard')
        parser.add_argument('-f', '--file', nargs='?', const='bop-output.txt', help='Output to file (optional filename)')
        parser.add_argument('-n', '--new', action='store_true', help='Clear cache and fetch new text')
        parser.add_argument('-g', '--gen', action='store_true', help='Just generate and display text without copying')
        parser.add_argument('-c', '--clear', action='store_true', help='Clear the cache without generating text')
        parser.add_argument('-d', '--debug', action='store_true', help='Show detailed progress information')
        
        args = parser.parse_args()
        
        try:
            # Handle clear command
            if args.clear:
                ensure_clean_cache()
                return

            # Ensure size is provided for text generation
            if not args.size:
                parser.error("size argument is required unless using --clear")
                
            # Clear cache if requested
            if args.new:
                ensure_clean_cache()
                
            target_size = parse_size(args.size)
            mode = 'tokens' if args.tokens else 'chars'
            
            # Generate text
            text = generate_text(target_size, mode, debug=args.debug)
            char_count = len(text)
            token_count = count_tokens(text)
            
            # Handle output based on flags
            if args.gen or args.stdout or args.file:
                if args.file:
                    with open(args.file, 'w', encoding='utf-8') as f:
                        f.write(text)
                    print(format_output(char_count, token_count, 'file'), file=sys.stderr)
                else:
                    try:
                        print(text)
                        print(format_output(char_count, token_count, 'stdout'), file=sys.stderr)
                    except BrokenPipeError:
                        # Python flushes standard streams on exit; redirect remaining output
                        # to devnull to avoid another BrokenPipeError at shutdown
                        devnull = os.open(os.devnull, os.O_WRONLY)
                        os.dup2(devnull, sys.stdout.fileno())
                        sys.exit(0)
            else:
                if copy_to_clipboard(text):
                    print(format_output(char_count, token_count, 'clipboard'), file=sys.stderr)
                else:
                    print("Failed to copy to clipboard, outputting to stdout:", file=sys.stderr)
                    print(text)
                    print(format_output(char_count, token_count, 'stdout'), file=sys.stderr)
                    
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            if isinstance(e, BrokenPipeError):
                sys.exit(0)
            print(f"Unexpected error: {e}", file=sys.stderr)
            sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled.", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
