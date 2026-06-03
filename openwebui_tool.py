"""
title: Docmost
author: focalfury
version: 1.0.0
description: Proxy for the Docmost MCP server — search, create, read, update, and organize documentation pages and spaces.
"""

import json
import requests
from typing import Optional

# Update this to match your deployment address
_MCP_URL = "http://10.10.0.100:8000/mcp"
_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}


def _call(tool: str, arguments: dict) -> str:
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": tool, "arguments": arguments},
    }
    try:
        resp = requests.post(_MCP_URL, json=payload, headers=_HEADERS, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        return f"Request failed: {e}"

    # Parse SSE envelope: lines starting with "data: "
    for line in resp.text.splitlines():
        if line.startswith("data: "):
            try:
                envelope = json.loads(line[6:])
            except json.JSONDecodeError:
                continue
            if "error" in envelope:
                err = envelope["error"]
                return f"MCP error {err.get('code', '')}: {err.get('message', err)}"
            result = envelope.get("result", {})
            content = result.get("content", [])
            if content and content[0].get("type") == "text":
                return content[0]["text"]
            return json.dumps(result, indent=2)

    return "No data in response"


class Tools:
    def get_workspace(self) -> str:
        """Get information about the current Docmost workspace."""
        return _call("get_workspace", {})

    def list_spaces(self) -> str:
        """List all available spaces in the Docmost workspace."""
        return _call("list_spaces", {})

    def list_groups(self) -> str:
        """List all groups in the Docmost workspace."""
        return _call("list_groups", {})

    def list_pages(self, space_id: Optional[str] = None) -> str:
        """
        List pages ordered by last-updated descending.

        :param space_id: ID of the space to list pages from. Omit to list across all spaces.
        """
        args = {}
        if space_id:
            args["space_id"] = space_id
        return _call("list_pages", args)

    def get_page(self, page_id: str) -> str:
        """
        Get the full content and metadata of a page.

        :param page_id: ID of the page to retrieve.
        """
        return _call("get_page", {"page_id": page_id})

    def create_page(
        self,
        title: str,
        content: str,
        space_id: str,
        parent_page_id: Optional[str] = None,
    ) -> str:
        """
        Create a new page with Markdown content, optionally nested under a parent.

        :param title: Title of the new page.
        :param content: Markdown content for the page body.
        :param space_id: ID of the space to create the page in.
        :param parent_page_id: Optional page ID to nest the new page under.
        """
        args: dict = {"title": title, "content": content, "space_id": space_id}
        if parent_page_id:
            args["parent_page_id"] = parent_page_id
        return _call("create_page", args)

    def update_page(
        self,
        page_id: str,
        content: str,
        title: Optional[str] = None,
    ) -> str:
        """
        Update a page's content and optionally its title. Preserves page ID and history.

        :param page_id: ID of the page to update.
        :param content: New Markdown content.
        :param title: Optional new title. Omit to leave the title unchanged.
        """
        args: dict = {"page_id": page_id, "content": content}
        if title:
            args["title"] = title
        return _call("update_page", args)

    def move_page(
        self,
        page_id: str,
        parent_page_id: Optional[str] = None,
        position: Optional[str] = None,
    ) -> str:
        """
        Move a page to a new parent or to the space root.

        :param page_id: ID of the page to move.
        :param parent_page_id: Target parent page ID. Pass empty string or omit to move to root.
        :param position: Optional fractional-index position string (≥5 chars). Defaults to end.
        """
        args: dict = {"page_id": page_id}
        if parent_page_id:
            args["parent_page_id"] = parent_page_id
        if position:
            args["position"] = position
        return _call("move_page", args)

    def search(self, query: str, space_id: Optional[str] = None) -> str:
        """
        Full-text search across Docmost pages and content.

        :param query: Search query string.
        :param space_id: Optional space ID to restrict the search to a single space.
        """
        args: dict = {"query": query}
        if space_id:
            args["space_id"] = space_id
        return _call("search", args)
