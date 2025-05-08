# ------------------------------IMPORTS------------------------------


import nyaapy.nyaasi.nyaa as NyaaPy
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


def find_torrent(uploader: str, anime_name: str, episode: int, quality: int, hevc: bool, untrusted_option: bool) -> dict:
    """Find if the torrent is already in the database. If not, download it.
    Args:
        uploader (str): The name of the uploader.
        anime_name (str): The name of the anime.
        episode (int): The episode number.
        quality (str): The quality of the torrent.

    Returns:
        dict: Returns torrent if found, else None.
    """

    # Because anime title usually have their episode number like '0X' when X < 10, we need to add a 0 to the episode number.
    if episode >= 10:
        episode = str(episode)
    else:
        episode = "0" + str(episode)

    hevc_keywords = ["HEVC", "x265", "H.265"]

    queries = []

    # Explicitly either HEVC or not
    if hevc:
        queries.append(f"[{uploader}] ({anime_name}) {episode} [{quality}p] " + "|".join(map(lambda k: f'"{k}"', hevc_keywords)))
    else:
        queries.append(f"[{uploader}] ({anime_name}) {episode} [{quality}p] " + " ".join(map(lambda k: f'-"{k}"', hevc_keywords)))

    found_torrents = []
    for query in queries:
        chunk = NyaaPy.Nyaa.search(
            keyword=query,
            category=1,
            subcategory=2,
            filters=0 if untrusted_option else 2,
        )
        print(query, found_torrents)
        if not isinstance(found_torrents, list) or len(found_torrents) == 0:
            found_torrents = found_torrents + chunk

    if len(found_torrents) == 0:
        return {}
    
    try:
        # We take the very closest title to what we are looking for.
        torrent = None
        a_name = anime_name.lower()
        for t in found_torrents: # (break if found, so we get the most recent one)
            t_name = t.name.lower()
            if (
                f"{a_name} - {episode}" in t_name
                and "~" not in t_name
            ):  # we want to avoid ~ because Erai-Raws use it for already packed episodes
                torrent = t
                break

        # Else, we take try to get a close title to the one we are looking for.
        if torrent is None:
            for t in found_torrents:
                t_name = t.name.lower()
                if (
                    a_name in t_name
                    and f" {episode} " in t_name
                    and "~" not in t_name
                ):  # we want to avoid ~ because Erai-Raws use it for already packed episodes
                    torrent = t
                    break

    except Exception as e:
        raise e

    return torrent
