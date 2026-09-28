"""HTTP client seam for the connection test.

The endpoint tests patch ``httpx.Client`` here. The POST itself arrives with
the OpenAI-compatible adapter.
"""

import httpx

TIMEOUT = httpx.Timeout(15.0)
