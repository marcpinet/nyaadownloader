# ------------------------------IMPORTS------------------------------


import nyaapy.nyaasi.nyaa as NyaaPy
from nyaapy.torrent import Torrent

import re
import requests
import webbrowser as wb


# ------------------------------FUNCTIONS------------------------------


def is_in_database(anime_name: str) -> bool:
    """Check if anime exists in Nyaa database
    Args:
        anime_name (str): Name of the anime to check.

    Raises:
        Exception: If the underlying module throws one.

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
    except Exception as e:
        raise e
    return True


def download(torrent: dict) -> bool:
    """Download a nyaa.si torrent from the web (also retrives its original name)

    Args:
        torrent (dict): The dictionary returned by the NyaaPy.search() method.

    Returns:
        bool: True if the transfer was successful, False otherwise.
    """
    try:
        with requests.get(torrent.download_url) as response, open(
            torrent.name + ".torrent", "wb"
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
        return wb.open(torrent.magnet)

    except:
        return False

def parse_batch_info(torrent_name: str) -> None | tuple:
    #if "batch" not in anime_name.lower(): # oh it will not always have the word "batch" in name
    #    return None
    m = re.search(r"[\s(\[]([0-9]+)\s*[-~]\s*([0-9]+)[\s)\]]", torrent_name)
    if m is None:
        return None
    return (int(m[1]), int(m[2]))

def find_torrent(uploader: str, anime_name: str, episode_num: int, quality: int, codec: str | None, untrusted_option: bool, allow_batch: bool, start_end: tuple[int, int], statusbar_signal) -> Torrent | None:
    """Find if the torrent is already in the database. If not, download it.

    Returns:
        dict: Returns torrent if found, else None.
    """

    if quality is None:
        resolutions = [2160, 1080, 720, 480]
        codecs = ["AV1", "HEVC", None]
        qualities = [(res, codec) for res in resolutions for codec in codecs]
        for quality in qualities:
            resolution = quality[0]
            codec = quality[1]
            result = find_torrent(uploader, anime_name, episode_num, resolution, codec, untrusted_option, allow_batch, start_end, statusbar_signal)
            if result is not None and isinstance(result, Torrent):
                return result
        return None

    # Because anime title usually have their episode number like '0X' when X < 10, we need to add a 0 to the episode number.
    def get_episode_str(episode_num: int):
        if episode_num >= 10:
            episode = str(episode_num)
        else:
            episode = "0" + str(episode_num)
        return episode
    episode = get_episode_str(episode_num)

    hevc_keywords = ["HEVC", "x265", "H.265"]
    hevc_keyword_positive = "|".join(map(lambda k: f'"{k}"', hevc_keywords))
    hevc_keyword_negative = " ".join(map(lambda k: f'-"{k}"', hevc_keywords))
    av1_keyword_positive = "AV1"
    av1_keyword_negative = "-AV1"

    queries = []

    # Explicitly match only the exact codec we're looking for and nothing else (or none of supported codecs as fallback)
    if codec == "AV1":
        queries.append(f"[{uploader}] ({anime_name}) {episode} [{quality}p] " + av1_keyword_positive + " " + hevc_keyword_negative)
    elif codec == "HEVC":
        queries.append(f"[{uploader}] ({anime_name}) {episode} [{quality}p] " + av1_keyword_negative + " " + hevc_keyword_positive)
    else:
        queries.append(f"[{uploader}] ({anime_name}) {episode} [{quality}p] " + av1_keyword_negative + " " + hevc_keyword_negative)

    found_torrents = []
    for query in queries:
        if statusbar_signal:
            statusbar_signal.emit(query)
        chunk = NyaaPy.Nyaa.search(
            keyword=query,
            category=1,
            subcategory=2,
            filters=0 if untrusted_option else 2,
        )
        if statusbar_signal:
            statusbar_signal.emit("")
        if not isinstance(found_torrents, list) or len(found_torrents) == 0:
            found_torrents = found_torrents + chunk

    if len(found_torrents) == 0:
        return None
    
    try:
        # We take the very closest title to what we are looking for.
        torrent = None
        a_name = anime_name.lower()

        ep = episode_num
        ep_start = start_end[0]
        ep_end = start_end[1]
        #ep_start_str = get_episode_str(ep_start)
        #ep_end_str = get_episode_str(ep_end)

        if allow_batch:
            for t in found_torrents:
                t_name = t.name.lower()
                batch_start_end = parse_batch_info(t_name)
                if (
                    batch_start_end is not None
                    and batch_start_end[0] == ep # the batch starts with the episode we're currently trying to download
                    and batch_start_end[1] <= ep_end # the batch ends before or exactly where we want to end
                    and f"{a_name} - " in t_name # (prefer this name form first, so that we hopefully avoid matching sequels)
                ):
                    torrent = t
                    break

        if allow_batch and torrent is None:
            for t in found_torrents:
                t_name = t.name.lower()
                batch_start_end = parse_batch_info(t_name)
                if (
                    batch_start_end is not None
                    and batch_start_end[0] == ep # the batch starts with the episode we're currently trying to download
                    and batch_start_end[1] <= ep_end # the batch ends before or exactly where we want to end
                    and a_name in t_name # of course should have our anime name in the title as well
                ):
                    torrent = t
                    break

        if torrent is None:
            for t in found_torrents:
                t_name = t.name.lower()
                batch_start_end = parse_batch_info(t_name)
                if (
                    f"{a_name} - {episode}" in t_name
                    and batch_start_end is None
                ):
                    torrent = t
                    break

        # Else, we take try to get a close title to the one we are looking for.
        if torrent is None:
            for t in found_torrents:
                t_name = t.name.lower()
                batch_start_end = parse_batch_info(t_name)
                if (
                    a_name in t_name
                    and (
                        f" {episode} " in t_name
                        or f"({episode})" in t_name
                        or f"[{episode}]" in t_name
                        or f"E{episode} " in t_name
                        or f"E{episode}]" in t_name
                    )
                    and batch_start_end is None
                ):
                    torrent = t
                    break

    except Exception as e:
        raise e

    return torrent
