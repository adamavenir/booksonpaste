import pytest
from pathlib import Path
import tempfile
import shutil
from unittest.mock import patch, Mock
from booksonpaste.bop import (
    parse_size,
    format_number,
    format_output,
    count_tokens,
    generate_text,
    CACHE_DIR,
    download_text,
    clear_cache,
    ensure_cache_dir,
    is_cache_empty,
    copy_to_clipboard,
)

# Mock text for testing
MOCK_TEXT = """
First paragraph.
This is a test paragraph with multiple lines.
It needs to be long enough to meet our size requirements.
We'll add some more text here to make it longer.

Second paragraph.
More test content here.
Adding several lines to make it substantial.
This should help with the size requirements.

Third paragraph.
Final test lines here.
Making this one longer too.
The more text we have, the better our tests will work.
"""

# Test parse_size function
@pytest.mark.parametrize("input_str,expected", [
    ("100", 100),
    ("1k", 1_000),
    ("1.5k", 1_500),
    ("1m", 1_000_000),
    ("1mm", 1_000_000),
    ("2.5m", 2_500_000),
])
def test_parse_size_valid(input_str, expected):
    assert parse_size(input_str) == expected

@pytest.mark.parametrize("input_str", [
    "k",
    "m",
    "abc",
    "1x",
    "",
])
def test_parse_size_invalid(input_str):
    with pytest.raises(ValueError):
        parse_size(input_str)

# Test format_number function
@pytest.mark.parametrize("input_num,expected", [
    (1000, "1,000"),
    (1000000, "1,000,000"),
    (1234567, "1,234,567"),
    (0, "0"),
    (123, "123"),
])
def test_format_number(input_num, expected):
    assert format_number(input_num) == expected

# Test format_output function
@pytest.mark.parametrize("chars,tokens,output_type,expected", [
    (1000, 200, 'clipboard', "📋 1,000 characters (200 tokens)"),
    (1000, 200, 'stdout', "＞ 1,000 characters (200 tokens)"),
    (1000, 200, 'file', "📄 1,000 characters (200 tokens)"),
])
def test_format_output(chars, tokens, output_type, expected):
    assert format_output(chars, tokens, output_type) == expected

# Test count_tokens function
def test_count_tokens():
    text = "Hello, world!"
    assert count_tokens(text) > 0  # Basic sanity check
    assert isinstance(count_tokens(text), int)

# Test cache management
@pytest.fixture
def clean_temp_cache_dir():
    """Create a clean temporary cache directory for testing."""
    original_cache_dir = CACHE_DIR
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_dir = Path(tmpdir) / '.booksonpaste' / 'cache'
        # Temporarily replace CACHE_DIR
        import booksonpaste.bop
        booksonpaste.bop.CACHE_DIR = temp_dir
        yield temp_dir
        # Restore original CACHE_DIR
        booksonpaste.bop.CACHE_DIR = original_cache_dir

def test_cache_management(clean_temp_cache_dir):
    """Test cache directory management functions."""
    # Test is_cache_empty when directory doesn't exist
    assert is_cache_empty()
    
    # Test ensure_cache_dir
    ensure_cache_dir()
    assert clean_temp_cache_dir.exists()
    assert is_cache_empty()  # Should still be empty after creation
    
    # Create a test file
    test_file = clean_temp_cache_dir / "test.txt"
    test_file.write_text("test")
    assert not is_cache_empty()
    
    # Test clear_cache
    clear_cache()
    assert is_cache_empty()

# Test clipboard operations
def test_copy_to_clipboard():
    """Test clipboard operations with mocked subprocess."""
    with patch('subprocess.Popen') as mock_popen:
        mock_process = Mock()
        mock_process.communicate.return_value = (None, None)
        mock_popen.return_value = mock_process
        
        assert copy_to_clipboard("test text")
        mock_popen.assert_called_once()
        mock_process.communicate.assert_called_once()

def test_copy_to_clipboard_failure():
    """Test clipboard operations failure."""
    with patch('subprocess.Popen', side_effect=Exception("Mock error")):
        assert not copy_to_clipboard("test text")

# Test text generation
@pytest.fixture
def temp_cache_dir():
    """Create a temporary cache directory for testing."""
    original_cache_dir = CACHE_DIR
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_dir = Path(tmpdir) / '.booksonpaste' / 'cache'
        temp_dir.mkdir(parents=True)
        # Create a mock cache file
        cache_file = temp_dir / "mock_text.txt"
        cache_file.write_text(MOCK_TEXT)
        # Temporarily replace CACHE_DIR
        import booksonpaste.bop
        booksonpaste.bop.CACHE_DIR = temp_dir
        yield temp_dir
        # Restore original CACHE_DIR
        booksonpaste.bop.CACHE_DIR = original_cache_dir

@pytest.fixture
def mock_text_sources(monkeypatch):
    """Mock text sources to return our test text."""
    def mock_get_random_text():
        return MOCK_TEXT
    
    monkeypatch.setattr('booksonpaste.bop.get_random_text', mock_get_random_text)
    yield

def test_generate_text_chars(temp_cache_dir, mock_text_sources):
    """Test character-based text generation."""
    target_size = 100
    text = generate_text(target_size, mode='chars')
    print(f"\nGenerated text (len={len(text)}):\n{text}")  # Debug print
    # Should not exceed target size
    assert len(text) <= target_size
    # Should be reasonably close to target (within 20%)
    assert len(text) >= target_size * 0.8

def test_generate_text_tokens(temp_cache_dir, mock_text_sources):
    """Test token-based text generation."""
    target_size = 100
    text = generate_text(target_size, mode='tokens')
    token_count = count_tokens(text)
    # Should not exceed target size
    assert token_count <= target_size
    # Should be reasonably close to target (within 20%)
    assert token_count >= target_size * 0.8

def test_generate_text_wrapping(temp_cache_dir, mock_text_sources):
    """Test that generated text maintains paragraph structure."""
    text = generate_text(1000, mode='chars')
    paragraphs = [p for p in text.split('\n\n') if p.strip()]
    # Should have at least one paragraph
    assert len(paragraphs) > 0
    # Each paragraph should be non-empty
    assert all(len(p.strip()) > 0 for p in paragraphs)

def test_download_text(temp_cache_dir):
    """Test text downloading and caching."""
    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.text = MOCK_TEXT
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Test downloading new text
        text = download_text("https://example.com/test.txt", "test")
        assert text == MOCK_TEXT
        mock_get.assert_called_once()
        
        # Test using cached text
        text = download_text("https://example.com/test.txt", "test")
        assert text == MOCK_TEXT
        # Should not call requests.get again
        mock_get.assert_called_once() 