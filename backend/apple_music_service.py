from pathlib import Path

"""
Apple Music / iTunes Tunnel Service
===================================
A bridge ("tunnel") from your Apple ID / iTunes account into the Christman / Brockston agent ecosystem.

This is the MCP / agent-friendly way to let your beings (Brockston, Claude, Perplexity, etc.) access or reference your Apple Music data, playlists, purchases, voice-related files, and your album "53 Years in the Making".

Two modes supported:
1. Public iTunes Search API (no auth) - for store search, lookups, recommendations.
2. Personal library "tunnel" - you provide Apple Music share links or local MP3 paths (from your library export or the IDE's Music & Voice Library). Agents can then "play", "reference", or "recommend" them.

For full personal library access (your actual playlists, library contents, etc.):
- Use "Sign in with Apple" + MusicKit / Apple Music API (requires Apple Developer account + user authorization).
- Or, on your Mac, use local scripting (osascript) to query the Apple Music app.
- Or, periodically sync your library to local MP3s + use the IDE library to manage links.

Environment:
    APPLE_MUSIC_USER_TOKEN (optional, for future personal API calls - store encrypted refresh token from your OAuth flow)
    APPLE_DEVELOPER_TOKEN (for public MusicKit calls if you set up a developer account)

Usage from agents / MCP:
    from backend.apple_music_service import AppleMusicService
    apple = AppleMusicService()
    results = apple.search_store("jazz playlist 53 years in the making")
    link = apple.get_share_link("your-track-id")  # or use pre-generated Apple Music links from your account

See the frontend Music & Voice Library for the UI side (paste Apple Music links or import local MP3 folders).

© 2026 Everett Nathaniel Christman & The Christman AI Project
Cardinal Rule: Honest data access. No pretending we have your library if we don't.
"""

import os
import json
import logging
import urllib.request
import urllib.error
import urllib.parse
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

ITUNES_SEARCH_URL = "https://itunes.apple.com/search"
APPLE_MUSIC_BASE = "https://music.apple.com"

class AppleMusicService:
    """
    The "tunnel" service for Apple Music / iTunes.
    Agents and the IDE can use this to search the store or reference your personal content via links / local paths.
    """

    def __init__(self, developer_token: Optional[str] = None, user_token: Optional[str] = None):
        self.developer_token = developer_token or os.getenv("APPLE_DEVELOPER_TOKEN")
        self.user_token = user_token or os.getenv("APPLE_MUSIC_USER_TOKEN")  # encrypted refresh token from your auth flow

        self._available = True  # Public search always works; personal requires tokens/links

        logger.info(
            "[AppleMusicService] Tunnel initialized. "
            f"Public search ready. Personal tunnel status: {'user token present' if self.user_token else 'use share links or local MP3s from the IDE library'}"
        )

    @property
    def is_available(self) -> bool:
        return self._available

    def search_store(
        self,
        term: str,
        media: str = "music",
        entity: str = "song,album,playlist",
        limit: int = 20,
        country: str = "us"
    ) -> List[Dict[str, Any]]:
        """
        Search the public iTunes / Apple Music store (no auth needed).
        Returns structured results with track/album/playlist info and Apple Music links.

        Use this for agents to find your music or recommendations.
        """
        params = {
            "term": term,
            "media": media,
            "entity": entity,
            "limit": str(limit),
            "country": country
        }
        url = f"{ITUNES_SEARCH_URL}?{urllib.parse.urlencode(params)}"

        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))
                results = data.get("results", [])
                # Normalize to consistent shape + add clean Apple Music links where possible
                normalized = []
                for r in results:
                    link = r.get("trackViewUrl") or r.get("collectionViewUrl") or r.get("playlistViewUrl")
                    normalized.append({
                        "id": r.get("trackId") or r.get("collectionId") or r.get("playlistId"),
                        "name": r.get("trackName") or r.get("collectionName") or r.get("playlistName"),
                        "artist": r.get("artistName"),
                        "kind": r.get("kind") or r.get("collectionType"),
                        "apple_music_link": link,
                        "preview_url": r.get("previewUrl"),
                        "artwork": r.get("artworkUrl600") or r.get("artworkUrl100"),
                        "raw": r  # full for advanced use
                    })
                logger.info(f"[AppleMusicService] Store search for '{term}' returned {len(normalized)} results")
                return normalized
        except Exception as e:
            logger.error(f"[AppleMusicService] Store search failed: {e}")
            return []

    def generate_apple_music_link(self, search_term: str) -> Optional[str]:
        """
        Helper: Search the store and return the best matching Apple Music link.
        Useful for agents to "give you a link like Apple Music would".
        """
        results = self.search_store(search_term, limit=1)
        if results:
            return results[0].get("apple_music_link")
        return None

    def get_user_library_references(self) -> List[Dict[str, Any]]:
        """
        Personal "tunnel" side for Everett's collection (incl. the album "53 Years in the Making" and Brockston.mp3).

        Returns references from the IDE's Music & Voice Library (local MP3s in ~/Downloads
        or Apple Music share links generated from your Apple ID).

        In a full implementation:
        - Use your stored user_token + Apple Music API to call /v1/me/library/playlists etc.
        - Or query local Apple Music app on your Mac via osascript / MusicKit.
        - Or sync your purchases/library periodically.

        The IDE library + this service is the current practical tunnel.
        """
        logger.info("[AppleMusicService] Personal library references requested (53 Years in the Making / Brockston.mp3).")
        return [
            {"title": "Brockston.mp3", "source": str(Path.home() / "Downloads" / "Brockston.mp3"), "type": "local_mp3", "album": "53 Years in the Making", "note": "Add/play via IDE explorer or Music Library."},
            {"note": "Use the Music & Voice Library in the IDE (Lib button) to manage your full album MP3s and Apple Music share links from your Apple ID."},
            {"note": "Generate Apple Music links: music.apple.com > your album > ... > Share > Copy Link. Paste into the library for agents to reference."}
        ]

    def play_or_reference(self, identifier: str) -> Dict[str, Any]:
        """
        Agent-friendly helper: Given a search term, ID, or known link, return a playable/reference object.
        The IDE can then play local files or open Apple Music links.
        """
        if identifier.startswith("http") and "music.apple.com" in identifier:
            return {
                "type": "apple_music_link",
                "link": identifier,
                "instruction": "Open this in Apple Music (or paste into the IDE library)."
            }
        # Otherwise treat as search
        results = self.search_store(identifier, limit=3)
        if results:
            best = results[0]
            return {
                "type": "search_result",
                "name": best["name"],
                "artist": best["artist"],
                "apple_music_link": best.get("apple_music_link"),
                "preview": best.get("preview_url"),
                "local_note": "If you have the MP3 locally, add it via the IDE explorer or library import for direct playback."
            }
        return {"error": "No results"}

# Convenience for quick use in agents / MCP tools
apple_music = None

def get_apple_music_service() -> AppleMusicService:
    global apple_music
    if apple_music is None:
        apple_music = AppleMusicService()
    return apple_music

# Example MCP-style tool functions (for DerekMCPServer / your agents)
def search_apple_music(term: str) -> List[Dict[str, Any]]:
    """MCP tool: Search Apple Music / iTunes store."""
    return get_apple_music_service().search_store(term)

def get_apple_music_link_for(term: str) -> Optional[str]:
    """MCP tool: Get a clean Apple Music share link for something (like Apple would give you)."""
    return get_apple_music_service().generate_apple_music_link(term)

def reference_my_album_tracks() -> List[Dict[str, Any]]:
    """MCP tool: Get references to your personal '53 Years in the Making' tracks (via the library tunnel)."""
    # In practice, this would pull from your stored links or Apple API.
    # For now, points to the IDE library.
    svc = get_apple_music_service()
    return svc.get_user_library_references() + [
        {"suggestion": "Use the IDE Music Library 'Import My Album' button with the folder containing your MP3s."}
    ]