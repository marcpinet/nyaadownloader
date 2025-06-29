# ------------------------------IMPORTS------------------------------


import NyaaPy
import requests
import webbrowser as wb
from . import torrent_parser
from typing import List, Optional, Dict


# ------------------------------FUNCTIONS------------------------------


def is_in_database(anime_name: str) -> bool:
    """Check if anime exists in Nyaa database
    Args:
        anime_name (str): Name of the anime to check.

    Raises:
        Exception: If the anime is not found in the database, the only possible reason is that user has no Internet connection.

    Returns:
        bool: True if check was successful, False otherwise.
    """
    try:
        if (
            len(
                NyaaPy.Nyaa.search(
                    keyword=anime_name, category=1, subcategory=2, filters=0
                )
            )
            == 0
        ):
            return False
    except:
        raise Exception("No Internet connection available.")
    return True


def download(torrent: dict) -> bool:
    """Download a nyaa.si torrent from the web (also retrives its original name)

    Args:
        torrent (dict): The dictionary returned by the NyaaPy.search() method.

    Returns:
        bool: True if the transfer was successful, False otherwise.
    """
    try:
        with requests.get(torrent["download_url"]) as response, open(
            torrent["name"] + ".torrent", "wb"
        ) as out_file:
            out_file.write(response.content)

    except requests.Timeout:
        return False

    return True


def transfer(torrent: dict) -> bool:
    """Open the user's torrent client and transfers the file to it.
    Args:
        torrent (dict): The dictionary returned by the NyaaPy.search() method.

    Returns:
        bool: True if the transfer was successful, False otherwise.
    """
    try:
        wb.open(torrent["magnet"])

    except:
        return False

    return True


def find_torrent(uploader: str, anime_name: str, episode: int, quality: int, untrusted_option: bool) -> dict:
    """Find if the torrent is already in the database using PTT for enhanced parsing.
    Args:
        uploader (str): The name of the uploader.
        anime_name (str): The name of the anime.
        episode (int): The episode number.
        quality (int): The quality of the torrent (e.g., 1080).
        untrusted_option (bool): Whether to include untrusted torrents.

    Returns:
        dict: Returns torrent if found, else empty dict.
    """
    try:
        # Search for torrents with multiple patterns to increase success rate
        search_patterns = [
            f"[{uploader}] {anime_name} - {episode:02d} [{quality}p]",
            f"[{uploader}] {anime_name} - {episode} [{quality}p]",
            f"[{uploader}] {anime_name} - {episode:02d} ({quality}p)",
            f"[{uploader}] {anime_name} - {episode} ({quality}p)",
            f"{uploader} {anime_name} {episode:02d}",
            f"{anime_name} {episode:02d} {quality}p",
            f"{anime_name} - {episode:02d}"
        ]
        
        found_torrents = []
        
        # If no specific uploader, search more broadly
        if not uploader:
            search_patterns = [
                f"{anime_name} - {episode:02d} [{quality}p]",
                f"{anime_name} - {episode} [{quality}p]",
                f"{anime_name} {episode:02d} {quality}p",
                f"{anime_name} - {episode:02d}",
                f"{anime_name} episode {episode}"
            ]
        
        # Search with each pattern
        for pattern in search_patterns[:3]:  # Limit to first 3 patterns to avoid too many requests
            try:
                torrents = NyaaPy.Nyaa.search(
                    keyword=pattern,
                    category=1,
                    subcategory=2,
                    filters=0 if untrusted_option else 2,
                )
                found_torrents.extend(torrents)
                if len(found_torrents) > 20:  # Stop if we have enough results
                    break
            except Exception:
                continue
        
        if not found_torrents:
            return {}
        
        # Use PTT to find the best matching torrent
        preferred_groups = [uploader] if uploader else []
        best_torrent = torrent_parser.get_best_torrent(
            found_torrents, 
            anime_name, 
            episode, 
            f"{quality}p", 
            preferred_groups
        )
        
        if best_torrent and hasattr(best_torrent, 'torrent_data'):
            return best_torrent.torrent_data
        
        # Fallback to original logic if PTT parsing fails
        return _find_torrent_fallback(found_torrents, anime_name, episode, uploader)
        
    except Exception as e:
        print(f"Error in find_torrent: {e}")
        return {}


def _find_torrent_fallback(found_torrents: List[Dict], anime_name: str, episode: int, uploader: str) -> Dict:
    """Fallback method using original logic if PTT parsing fails."""
    try:
        episode_str = f"{episode:02d}" if episode < 10 else str(episode)
        
        # Original logic - look for exact matches first
        for t in found_torrents:
            if (
                t["name"].lower().find(f"{anime_name} - {episode_str}".lower()) != -1
                and t["name"].lower().find("~") == -1
            ):
                return t

        # Fallback - look for partial matches
        for t in found_torrents:
            if (
                t["name"].lower().find(f"{anime_name}".lower()) != -1
                and t["name"].lower().find(f" {episode_str} ") != -1
                and t["name"].lower().find("~") == -1
            ):
                return t
                
    except Exception:
        pass
        
    return {}


def get_torrent_details(torrent: dict) -> Optional[torrent_parser.TorrentInfo]:
    """Get detailed information about a torrent using PTT parsing.
    
    Args:
        torrent (dict): The dictionary returned by the NyaaPy.search() method.
        
    Returns:
        Optional[TorrentInfo]: Parsed torrent information or None if parsing fails.
    """
    try:
        parsed_torrent = torrent_parser.parse_torrent_title(torrent["name"])
        parsed_torrent.torrent_data = torrent
        return parsed_torrent
    except Exception as e:
        print(f"Error parsing torrent details: {e}")
        return None


def search_anime_torrents(anime_name: str, uploader: str = "", quality: str = "", 
                         episode_range: tuple = None, limit: int = 50) -> List[torrent_parser.TorrentInfo]:
    """Search for anime torrents with enhanced filtering using PTT.
    
    Args:
        anime_name (str): Name of the anime to search for.
        uploader (str): Preferred uploader/group name.
        quality (str): Preferred quality (e.g., "1080p").
        episode_range (tuple): Range of episodes to search for (start, end).
        limit (int): Maximum number of results to return.
        
    Returns:
        List[TorrentInfo]: List of parsed torrent information.
    """
    try:
        # Build search query
        search_terms = [anime_name]
        if uploader:
            search_terms.append(uploader)
        if quality:
            search_terms.append(quality)
            
        search_query = " ".join(search_terms)
        
        # Search for torrents
        found_torrents = NyaaPy.Nyaa.search(
            keyword=search_query,
            category=1,
            subcategory=2,
            filters=2,  # Trusted only by default
        )
        
        parsed_torrents = []
        for torrent in found_torrents[:limit]:
            try:
                parsed_torrent = torrent_parser.parse_torrent_title(torrent["name"])
                parsed_torrent.torrent_data = torrent
                
                # Filter by criteria
                if anime_name.lower() not in parsed_torrent.title.lower():
                    continue
                    
                if uploader and (not parsed_torrent.group or uploader.lower() not in parsed_torrent.group.lower()):
                    continue
                    
                if quality and parsed_torrent.resolution != quality:
                    continue
                    
                if episode_range and parsed_torrent.episodes:
                    # Check if any episode in the torrent falls within the desired range
                    start_ep, end_ep = episode_range
                    if not any(start_ep <= ep <= end_ep for ep in parsed_torrent.episodes):
                        continue
                
                parsed_torrents.append(parsed_torrent)
                
            except Exception as e:
                print(f"Error parsing torrent '{torrent['name']}': {e}")
                continue
        
        # Sort by quality score
        return sorted(parsed_torrents, key=lambda t: t.get_quality_score(), reverse=True)
        
    except Exception as e:
        print(f"Error searching anime torrents: {e}")
        return []
