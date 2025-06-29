# ------------------------------IMPORTS------------------------------


from PTT import parse_title
from typing import Dict, List, Optional, Union
import re



# ------------------------------CLASSES------------------------------


class TorrentInfo:
    """
    Class to store parsed torrent information in a structured way.
    """
    
    def __init__(self, raw_title: str, parsed_data: Dict):
        self.raw_title = raw_title
        self.parsed_data = parsed_data
        
        self.title = parsed_data.get('title', '')
        self.year = parsed_data.get('year')
        self.resolution = parsed_data.get('resolution', '')
        self.quality = parsed_data.get('quality', '')
        self.codec = parsed_data.get('codec', '')
        self.group = parsed_data.get('group', '')
        
        self.seasons = parsed_data.get('seasons', [])
        self.episodes = parsed_data.get('episodes', [])
        
        self.audio = parsed_data.get('audio', [])
        self.languages = parsed_data.get('languages', [])
        self.dubbed = parsed_data.get('dubbed', False)
        self.subbed = parsed_data.get('subbed', False)
        
        # Other properties
        self.complete = parsed_data.get('complete', False)
        self.repack = parsed_data.get('repack', False)
        self.proper = parsed_data.get('proper', False)
        self.extension = parsed_data.get('extension', '')
        self.container = parsed_data.get('container', '')
        self.bit_depth = parsed_data.get('bit_depth', '')
        self.hdr = parsed_data.get('hdr', [])
        self.channels = parsed_data.get('channels', [])
        
    def get_episode_number(self) -> Optional[int]:
        """Get the first episode number if available."""
        return self.episodes[0] if self.episodes else None
        
    def get_season_number(self) -> Optional[int]:
        """Get the first season number if available."""
        return self.seasons[0] if self.seasons else None
        
    def has_episode(self, episode_num: int) -> bool:
        """Check if this torrent contains a specific episode."""
        return episode_num in self.episodes
        
    def get_quality_score(self) -> int:
        """
        Calculate a quality score for ranking torrents.
        Higher score = better quality.
        """
        score = 0
        
        resolution_scores = {
            '2160p': 400, '4k': 400,
            '1440p': 300, '2k': 300,
            '1080p': 200,
            '720p': 100,
            '480p': 50,
            '360p': 25,
            '240p': 10
        }
        score += resolution_scores.get(self.resolution, 0)
        
        # Quality source scorin
        quality_scores = {
            'BluRay': 100, 'BluRay REMUX': 150,
            'REMUX': 120,
            'WEB-DL': 80,
            'WEBRip': 70,
            'HDTV': 60,
            'DVDRip': 40,
            'CAM': -100
        }
        score += quality_scores.get(self.quality, 0)
        
        codec_scores = {
            'hevc': 30, 'h265': 30,
            'avc': 20, 'h264': 20,
            'av1': 40
        }
        score += codec_scores.get(self.codec, 0)
        
        if '10bit' in self.bit_depth:
            score += 20
        elif '12bit' in self.bit_depth:
            score += 30
            
        if 'HDR' in self.hdr or 'HDR10' in self.hdr:
            score += 25
        if 'HDR10+' in self.hdr:
            score += 30
        if 'DV' in self.hdr:
            score += 35
            
        audio_scores = {
            'FLAC': 30,
            'TrueHD': 25,
            'DTS Lossless': 25,
            'DTS Lossy': 15,
            'Dolby Digital Plus': 15,
            'Dolby Digital': 10,
            'AAC': 10
        }
        for audio_format in self.audio:
            score += audio_scores.get(audio_format, 0)
            
        if self.repack:
            score -= 5
        if 'CAM' in self.quality or 'TS' in self.quality or 'TC' in self.quality:
            score -= 200
            
        return score
        
    def __str__(self) -> str:
        """String representation of the torrent info."""
        parts = []
        if self.title:
            parts.append(f"Title: {self.title}")
        if self.episodes:
            parts.append(f"Episodes: {', '.join(map(str, self.episodes))}")
        if self.seasons:
            parts.append(f"Seasons: {', '.join(map(str, self.seasons))}")
        if self.resolution:
            parts.append(f"Resolution: {self.resolution}")
        if self.quality:
            parts.append(f"Quality: {self.quality}")
        if self.group:
            parts.append(f"Group: {self.group}")
        if self.languages:
            parts.append(f"Languages: {', '.join(self.languages)}")
            
        return " | ".join(parts)


# ------------------------------FUNCTIONS------------------------------


def parse_torrent_title(title: str, translate_languages: bool = True) -> TorrentInfo:
    """
    Parse a torrent title using PTT library.
    
    Args:
        title (str): The torrent title to parse
        translate_languages (bool): Whether to translate language codes to full names
        
    Returns:
        TorrentInfo: Parsed torrent information
    """
    parsed_data = parse_title(title, translate_languages=translate_languages)
    
    return TorrentInfo(title, parsed_data)


def find_matching_torrents(torrents: List[Dict], anime_name: str, episode: int, 
                          quality: str, min_quality_score: int = 0) -> List[TorrentInfo]:
    """
    Find torrents that match the specified criteria and parse them with PTT.
    
    Args:
        torrents (List[Dict]): List of torrent dictionaries from NyaaPy
        anime_name (str): Name of the anime to match
        episode (int): Episode number to find
        quality (str): Preferred quality (e.g., "1080p")
        min_quality_score (int): Minimum quality score to consider
        
    Returns:
        List[TorrentInfo]: List of matching parsed torrents, sorted by quality score
    """
    matching_torrents = []
    
    for torrent in torrents:
        try:
            parsed_torrent = parse_torrent_title(torrent['name'])
            
            if matches_criteria(parsed_torrent, anime_name, episode, quality):
                if parsed_torrent.get_quality_score() >= min_quality_score:
                    parsed_torrent.torrent_data = torrent
                    matching_torrents.append(parsed_torrent)
                    
        except Exception as e:
            print(f"Error parsing torrent '{torrent['name']}': {e}")
            continue
    
    return sorted(matching_torrents, key=lambda t: t.get_quality_score(), reverse=True)


def matches_criteria(parsed_torrent: TorrentInfo, anime_name: str, episode: int, quality: str) -> bool:
    """
    Check if a parsed torrent matches the search criteria.
    
    Args:
        parsed_torrent (TorrentInfo): Parsed torrent information
        anime_name (str): Anime name to match
        episode (int): Episode number to find
        quality (str): Preferred quality
        
    Returns:
        bool: True if the torrent matches the criteria
    """
    title_match = anime_name.lower() in parsed_torrent.title.lower()
    
    episode_match = parsed_torrent.has_episode(episode)
    
    quality_match = True
    if quality and parsed_torrent.resolution:
        quality_num = int(quality.replace('p', ''))
        parsed_quality_num = int(parsed_torrent.resolution.replace('p', '')) if parsed_torrent.resolution.replace('p', '').isdigit() else 0
        quality_match = parsed_quality_num >= quality_num
    
    # This helps avoid downloading entire seasons when looking for single episodes
    if len(parsed_torrent.episodes) > 1:
        # If it's a small range (2-3 episodes), it might be OK
        # If it's a large range, probably a batch
        episode_range = max(parsed_torrent.episodes) - min(parsed_torrent.episodes) + 1
        if episode_range > 5:  # Likely a batch
            return False
    
    return title_match and episode_match and quality_match


def get_best_torrent(torrents: List[Dict], anime_name: str, episode: int, 
                     quality: str, preferred_groups: List[str] = None) -> Optional[TorrentInfo]:
    """
    Find the best matching torrent based on quality and other criteria.
    
    Args:
        torrents (List[Dict]): List of torrent dictionaries from NyaaPy
        anime_name (str): Name of the anime
        episode (int): Episode number
        quality (str): Preferred quality
        preferred_groups (List[str]): List of preferred release groups
        
    Returns:
        Optional[TorrentInfo]: Best matching torrent, or None if no matches
    """
    matching_torrents = find_matching_torrents(torrents, anime_name, episode, quality)
    
    if not matching_torrents:
        return None
    
    if preferred_groups:
        for group in preferred_groups:
            for torrent in matching_torrents:
                if torrent.group and group.lower() in torrent.group.lower():
                    return torrent
    
    return matching_torrents[0]


def extract_episode_from_title(title: str) -> Optional[int]:
    """
    Extract episode number from title using PTT parsing.
    
    Args:
        title (str): Torrent title
        
    Returns:
        Optional[int]: Episode number if found
    """
    parsed = parse_torrent_title(title)
    return parsed.get_episode_number()


def get_torrent_summary(parsed_torrent: TorrentInfo) -> str:
    """
    Get a human-readable summary of the torrent information.
    
    Args:
        parsed_torrent (TorrentInfo): Parsed torrent information
        
    Returns:
        str: Summary string
    """
    summary_parts = []
    
    # Basic info
    if parsed_torrent.title:
        summary_parts.append(f"📺 {parsed_torrent.title}")
    
    # Episode/Season info
    episode_info = []
    if parsed_torrent.seasons:
        episode_info.append(f"S{parsed_torrent.seasons[0]:02d}")
    if parsed_torrent.episodes:
        if len(parsed_torrent.episodes) == 1:
            episode_info.append(f"E{parsed_torrent.episodes[0]:02d}")
        else:
            episode_info.append(f"E{parsed_torrent.episodes[0]:02d}-E{parsed_torrent.episodes[-1]:02d}")
    
    if episode_info:
        summary_parts.append(" ".join(episode_info))
    
    # Quality info
    quality_info = []
    if parsed_torrent.resolution:
        quality_info.append(parsed_torrent.resolution)
    if parsed_torrent.quality:
        quality_info.append(parsed_torrent.quality)
    if parsed_torrent.codec:
        quality_info.append(parsed_torrent.codec.upper())
    if parsed_torrent.bit_depth:
        quality_info.append(parsed_torrent.bit_depth)
    
    if quality_info:
        summary_parts.append(f"🎬 {' '.join(quality_info)}")
    
    # Audio info
    audio_info = []
    if parsed_torrent.audio:
        audio_info.extend(parsed_torrent.audio)
    if parsed_torrent.channels:
        audio_info.extend(parsed_torrent.channels)
    
    if audio_info:
        summary_parts.append(f"🔊 {' '.join(audio_info)}")
    
    # Language info
    if parsed_torrent.languages:
        lang_flags = {"English": "🇺🇸", "Japanese": "🇯🇵", "French": "🇫🇷", "Spanish": "🇪🇸", "German": "🇩🇪"}
        lang_display = []
        for lang in parsed_torrent.languages:
            flag = lang_flags.get(lang, "🗣️")
            lang_display.append(f"{flag} {lang}")
        summary_parts.append(" ".join(lang_display))
    
    # Group info
    if parsed_torrent.group:
        summary_parts.append(f"👥 {parsed_torrent.group}")
    
    # Special indicators
    indicators = []
    if parsed_torrent.complete:
        indicators.append("📦 Complete")
    if parsed_torrent.repack:
        indicators.append("🔄 Repack")
    if parsed_torrent.proper:
        indicators.append("✅ Proper")
    if parsed_torrent.hdr:
        indicators.append(f"🌈 {'/'.join(parsed_torrent.hdr)}")
    
    if indicators:
        summary_parts.append(" ".join(indicators))
    
    return " | ".join(summary_parts)
