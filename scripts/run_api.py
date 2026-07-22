#!/usr/bin/env python3
"""Start Beauty Genius FastAPI server."""

from __future__ import annotations

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "api_server.main:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
    )
