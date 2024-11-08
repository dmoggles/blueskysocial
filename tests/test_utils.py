import unittest
from blueskysocial.utils import parse_uri


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


if __name__ == "__main__":
    unittest.main()
