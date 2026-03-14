#!/usr/bin/env python3
"""
TIDAL CLI for Clawdbot
Provides command-line access to TIDAL music streaming service.
"""

import argparse
import json
import os
import sys
import webbrowser
from pathlib import Path
from typing import Optional, List

try:
    import tidalapi
except ImportError:
    print(json.dumps({"status": "error", "message": "tidalapi not installed. Run: pip3 install tidalapi"}))
    sys.exit(1)


# Session file location
CLAWDBOT_DIR = Path.home() / ".clawdbot"
SESSION_FILE = CLAWDBOT_DIR / "tidal-session.json"


class TidalCLI:
    def __init__(self):
        self.session = tidalapi.Session()
        CLAWDBOT_DIR.mkdir(parents=True, exist_ok=True)
    
    def _load_session(self) -> bool:
        """Load existing session from file."""
        if not SESSION_FILE.exists():
            return False
        
        try:
            self.session.load_session_from_file(SESSION_FILE)
            return self.session.check_login()
        except Exception:
            return False
    
    def _save_session(self):
        """Save session to file."""
        self.session.save_session_to_file(SESSION_FILE)
    
    def _ensure_auth(self) -> bool:
        """Ensure we have a valid session."""
        if self._load_session():
            return True
        return False
    
    def _format_track(self, track, source_track_id: Optional[str] = None) -> dict:
        """Format a track object to dict."""
        data = {
            "id": str(track.id),
            "title": track.name,
            "artist": track.artist.name if hasattr(track, 'artist') and track.artist else "Unknown",
            "album": track.album.name if hasattr(track, 'album') and track.album else "Unknown",
            "duration": track.duration if hasattr(track, 'duration') else 0,
            "url": f"https://tidal.com/browse/track/{track.id}"
        }
        if source_track_id:
            data["source_track_id"] = source_track_id
        return data
    
    def _format_playlist(self, playlist) -> dict:
        """Format a playlist object to dict."""
        return {
            "id": str(playlist.id),
            "title": playlist.name,
            "description": getattr(playlist, 'description', '') or '',
            "track_count": getattr(playlist, 'num_tracks', 0),
            "duration": getattr(playlist, 'duration', 0),
            "created": str(getattr(playlist, 'created', '')) if hasattr(playlist, 'created') else None,
            "last_updated": str(getattr(playlist, 'last_updated', '')) if hasattr(playlist, 'last_updated') else None,
            "url": f"https://tidal.com/playlist/{playlist.id}"
        }
    
    def login(self) -> dict:
        """Login to TIDAL via OAuth (opens browser)."""
        try:
            login, future = self.session.login_oauth()
            
            # Open browser
            auth_url = login.verification_uri_complete
            if not auth_url.startswith('http'):
                auth_url = 'https://' + auth_url
            
            print(f"Opening browser for TIDAL login...", file=sys.stderr)
            print(f"If browser doesn't open, visit: {auth_url}", file=sys.stderr)
            print(f"Code expires in {login.expires_in} seconds", file=sys.stderr)
            
            webbrowser.open(auth_url)
            
            # Wait for auth
            future.result()
            
            if self.session.check_login():
                self._save_session()
                return {
                    "status": "success",
                    "message": "Successfully logged in to TIDAL",
                    "user_id": str(self.session.user.id)
                }
            else:
                return {"status": "error", "message": "Login failed"}
                
        except TimeoutError:
            return {"status": "error", "message": "Login timed out"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def status(self) -> dict:
        """Check authentication status."""
        if self._load_session():
            user = self.session.user
            return {
                "status": "success",
                "authenticated": True,
                "user": {
                    "id": str(user.id),
                    "username": getattr(user, 'username', None),
                    "email": getattr(user, 'email', None)
                }
            }
        return {
            "status": "success", 
            "authenticated": False,
            "message": "Not logged in. Run: tidal-cli.py login"
        }
    
    def favorites(self, limit: int = 20) -> dict:
        """Get user's favorite tracks."""
        if not self._ensure_auth():
            return {"status": "error", "message": "Not authenticated. Run: tidal-cli.py login"}
        
        try:
            limit = max(1, min(100, limit))
            favorites = self.session.user.favorites
            tracks = list(favorites.tracks(limit=limit))
            
            track_list = [self._format_track(t) for t in tracks]
            return {
                "status": "success",
                "count": len(track_list),
                "tracks": track_list
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def recommend(self, track_ids: Optional[List[str]] = None, limit: int = 20, 
                  seed_limit: int = 10) -> dict:
        """Get recommendations based on tracks or favorites."""
        if not self._ensure_auth():
            return {"status": "error", "message": "Not authenticated. Run: tidal-cli.py login"}
        
        try:
            limit = max(1, min(50, limit))
            
            # Use provided track IDs or get from favorites
            if not track_ids:
                favorites = self.session.user.favorites
                fav_tracks = favorites.tracks(limit=seed_limit, order="DATE", order_direction="DESC")
                track_ids = [str(t.id) for t in fav_tracks]
            
            if not track_ids:
                return {"status": "error", "message": "No tracks to base recommendations on"}
            
            # Get recommendations for each track
            all_recommendations = []
            seen_ids = set()
            
            for tid in track_ids:
                try:
                    track = self.session.track(tid)
                    if track:
                        recs = track.get_track_radio(limit=limit)
                        for r in recs:
                            if str(r.id) not in seen_ids:
                                all_recommendations.append(self._format_track(r, source_track_id=tid))
                                seen_ids.add(str(r.id))
                except Exception as e:
                    print(f"Warning: Could not get recommendations for track {tid}: {e}", file=sys.stderr)
            
            return {
                "status": "success",
                "seed_tracks": track_ids,
                "count": len(all_recommendations),
                "recommendations": all_recommendations
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def playlists(self) -> dict:
        """List user's playlists."""
        if not self._ensure_auth():
            return {"status": "error", "message": "Not authenticated. Run: tidal-cli.py login"}
        
        try:
            playlists = self.session.user.playlists()
            playlist_list = [self._format_playlist(p) for p in playlists]
            
            # Sort by last_updated
            playlist_list.sort(key=lambda x: x.get('last_updated') or '', reverse=True)
            
            return {
                "status": "success",
                "count": len(playlist_list),
                "playlists": playlist_list
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def playlist_tracks(self, playlist_id: str, limit: int = 100) -> dict:
        """Get tracks from a playlist."""
        if not self._ensure_auth():
            return {"status": "error", "message": "Not authenticated. Run: tidal-cli.py login"}
        
        try:
            limit = max(1, min(500, limit))
            playlist = self.session.playlist(playlist_id)
            
            if not playlist:
                return {"status": "error", "message": f"Playlist {playlist_id} not found"}
            
            tracks = playlist.items(limit=limit)
            track_list = [self._format_track(t) for t in tracks]
            
            return {
                "status": "success",
                "playlist": self._format_playlist(playlist),
                "count": len(track_list),
                "tracks": track_list
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def create_playlist(self, title: str, track_ids: List[str], 
                       description: str = "") -> dict:
        """Create a new playlist with tracks."""
        if not self._ensure_auth():
            return {"status": "error", "message": "Not authenticated. Run: tidal-cli.py login"}
        
        if not track_ids:
            return {"status": "error", "message": "No track IDs provided"}
        
        try:
            playlist = self.session.user.create_playlist(title, description)
            playlist.add(track_ids)
            
            return {
                "status": "success",
                "message": f"Created playlist '{title}' with {len(track_ids)} tracks",
                "playlist": self._format_playlist(playlist)
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def delete_playlist(self, playlist_id: str) -> dict:
        """Delete a playlist."""
        if not self._ensure_auth():
            return {"status": "error", "message": "Not authenticated. Run: tidal-cli.py login"}
        
        try:
            playlist = self.session.playlist(playlist_id)
            if not playlist:
                return {"status": "error", "message": f"Playlist {playlist_id} not found"}
            
            playlist.delete()
            return {
                "status": "success",
                "message": f"Deleted playlist {playlist_id}"
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}


def main():
    parser = argparse.ArgumentParser(description="TIDAL CLI for Clawdbot")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Login
    subparsers.add_parser("login", help="Login to TIDAL (opens browser)")
    
    # Status
    subparsers.add_parser("status", help="Check authentication status")
    
    # Favorites
    fav_parser = subparsers.add_parser("favorites", help="Get favorite tracks")
    fav_parser.add_argument("--limit", type=int, default=20, help="Max tracks (default: 20)")
    
    # Recommend
    rec_parser = subparsers.add_parser("recommend", help="Get recommendations")
    rec_parser.add_argument("--tracks", nargs="*", help="Track IDs to base recommendations on")
    rec_parser.add_argument("--limit", type=int, default=20, help="Recommendations per track (default: 20)")
    rec_parser.add_argument("--seed-limit", type=int, default=10, help="Favorites to use as seeds (default: 10)")
    
    # Playlists
    subparsers.add_parser("playlists", help="List playlists")
    
    # Playlist tracks
    pt_parser = subparsers.add_parser("playlist-tracks", help="Get tracks from a playlist")
    pt_parser.add_argument("playlist_id", help="Playlist ID")
    pt_parser.add_argument("--limit", type=int, default=100, help="Max tracks (default: 100)")
    
    # Create playlist
    cp_parser = subparsers.add_parser("create-playlist", help="Create a playlist")
    cp_parser.add_argument("title", help="Playlist title")
    cp_parser.add_argument("--tracks", nargs="+", required=True, help="Track IDs to add")
    cp_parser.add_argument("--description", default="", help="Playlist description")
    
    # Delete playlist
    dp_parser = subparsers.add_parser("delete-playlist", help="Delete a playlist")
    dp_parser.add_argument("playlist_id", help="Playlist ID")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    cli = TidalCLI()
    
    if args.command == "login":
        result = cli.login()
    elif args.command == "status":
        result = cli.status()
    elif args.command == "favorites":
        result = cli.favorites(limit=args.limit)
    elif args.command == "recommend":
        result = cli.recommend(track_ids=args.tracks, limit=args.limit, seed_limit=args.seed_limit)
    elif args.command == "playlists":
        result = cli.playlists()
    elif args.command == "playlist-tracks":
        result = cli.playlist_tracks(args.playlist_id, limit=args.limit)
    elif args.command == "create-playlist":
        result = cli.create_playlist(args.title, args.tracks, args.description)
    elif args.command == "delete-playlist":
        result = cli.delete_playlist(args.playlist_id)
    else:
        parser.print_help()
        sys.exit(1)
    
    print(json.dumps(result, indent=2, default=str))
    
    if result.get("status") == "error":
        sys.exit(1)


if __name__ == "__main__":
    main()
