"""Tests for network failures that must not terminate a batch run."""

from http.client import IncompleteRead
import unittest
from unittest.mock import patch

from iiif_resource_discovery.fetch import FetchError, HttpFetcher

class HttpFetcherTests(unittest.TestCase):
    def test_incomplete_chunked_response_becomes_structured_error(self) -> None:
        class IncompleteResponse:
            status = 200
            headers = {"Content-Type": "text/html"}

            def __enter__(self) -> "IncompleteResponse":
                return self

            def __exit__(self, *args: object) -> None:
                return None

            def geturl(self) -> str:
                return "https://example.org/incomplete"

            def read(self, amount: int) -> bytes:
                raise IncompleteRead(b"partial", 20)

        fetcher = HttpFetcher(timeout_seconds=1, retries=0, backoff_seconds=0)
        with patch("iiif_resource_discovery.fetch.urlopen", return_value=IncompleteResponse()):
            with self.assertRaises(FetchError) as context:
                fetcher.fetch("https://example.org/incomplete")

        self.assertEqual(context.exception.error_type, "incomplete_response")


if __name__ == "__main__":
    unittest.main()
