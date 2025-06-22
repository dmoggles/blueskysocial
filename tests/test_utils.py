import unittest
from blueskysocial.utils import parse_uri, bs4_tag_extract_content
from bs4 import BeautifulSoup


class TestParseUri(unittest.TestCase):
    def test_parse_uri_valid(self):
        uri = "at://example.com:repo/collection/rkey"
        expected_result = {
            "repo": "example.com:repo",
            "collection": "collection",
            "rkey": "rkey",
        }
        result = parse_uri(uri)
        self.assertEqual(result, expected_result)

    def test_parse_uri_invalid_format(self):
        uri = "at://example.com:repo/collection"
        with self.assertRaises(ValueError):
            parse_uri(uri)

    def test_parse_uri_empty_string(self):
        uri = ""
        with self.assertRaises(ValueError):
            parse_uri(uri)


class TestBs4TagExtractContent(unittest.TestCase):
    def test_extract_content_with_valid_tag(self):
        """Test extracting content from a valid tag with content attribute."""
        html = '<meta name="description" content="Test content">'
        soup = BeautifulSoup(html, 'html.parser')
        tag = soup.find('meta')
        
        result = bs4_tag_extract_content(tag)
        self.assertEqual(result, "Test content")

    def test_extract_content_with_empty_content(self):
        """Test extracting content from a tag with empty content attribute."""
        html = '<meta name="description" content="">'
        soup = BeautifulSoup(html, 'html.parser')
        tag = soup.find('meta')
        
        result = bs4_tag_extract_content(tag)
        self.assertEqual(result, "")

    def test_extract_content_with_none_tag(self):
        """Test extracting content when tag is None."""
        result = bs4_tag_extract_content(None)
        self.assertEqual(result, "")

    def test_extract_content_without_content_attribute(self):
        """Test extracting content from a tag without content attribute."""
        html = '<div>Some text</div>'
        soup = BeautifulSoup(html, 'html.parser')
        tag = soup.find('div')
        
        result = bs4_tag_extract_content(tag)
        self.assertEqual(result, "")

    def test_extract_content_with_numeric_content(self):
        """Test extracting numeric content from a tag."""
        html = '<meta name="count" content="123">'
        soup = BeautifulSoup(html, 'html.parser')
        tag = soup.find('meta')
        
        result = bs4_tag_extract_content(tag)
        self.assertEqual(result, "123")

    def test_extract_content_with_special_characters(self):
        """Test extracting content with special characters."""
        html = '<meta name="description" content="Test & content with <special> chars">'
        soup = BeautifulSoup(html, 'html.parser')
        tag = soup.find('meta')
        
        result = bs4_tag_extract_content(tag)
        self.assertEqual(result, "Test & content with <special> chars")


if __name__ == "__main__":
    unittest.main()
