# ------------------------------IMPORTS------------------------------


import NyaaPy
import urllib.request
import shutil
import webbrowser as wb


# ------------------------------FUNCTIONS------------------------------


def is_in_database(anime_name: str):
    """Check if anime exists in Nyaa database
    Args:
        anime_name (str): Name of the anime to check.

    Raises:
        Exception: If the anime is not found in the database, the only possible reason is that user has no Internet connection.

    Returns:
        bool: True if check was successful, False otherwise.
    """
    try:
        if len(NyaaPy.Nyaa.search(keyword=anime_name, category=1, subcategory=2, filters=2)) == 0:
            return False
    except:
        raise Exception('No Internet connection available.')
    return True


def download(torrent: dict):
    """Downloads a file from the web and saves it in a folder that has the name of the downloaded anime (the file also gets its original name).
    If you want more details, just read: https://stackoverflow.com/questions/7243750/download-file-from-web-in-python-3
    
    Args:
        torrent (dict): The dictionary returned by the NyaaPy.search() method.

    Returns:
        bool: True if the transfer was successful, False otherwise.
    """
    try :
        with urllib.request.urlopen(torrent['download_url']) as response, open(torrent['name'] + '.torrent', 'wb') as out_file:
            shutil.copyfileobj(response, out_file)  
        
    except:
        return False
    
    return True


def transfer(torrent: dict):
    """Opens the user's torrent client and transfers the file to it.
    Args:
        torrent (dict): The dictionary returned by the NyaaPy.search() method.

    Returns:
        bool: True if the transfer was successful, False otherwise.
    """
    try:
        wb.open(torrent['magnet'])
        return True
        
    except:
        return False


def find_torrent(uploader: str, anime_name: str, episode: int, quality: int):
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
        episode = '0' + str(episode)
    
    found_torrents = NyaaPy.Nyaa.search(keyword=f'[{uploader}] {anime_name} - {episode} [{quality}p]', category=1, subcategory=2, filters=2)
    try:
        # We take the very closest title to what we are looking for in order to avoid errors while browsing among every found torrents
        torrent = None
        for t in found_torrents:
            if t['name'].lower().find(f'{anime_name} - {episode}'.lower()) != -1 and t['name'].lower().find('~') == -1:  # we want to avoid ~ because Erai-Raws use it for already packed episodes
                torrent = t
                break  # break if found, so we get the most recent one
            
        # Else, we take try to get the closest title to the one we are looking for. (break if found, so we get the most recent one)
        if torrent is None:
            for t in found_torrents:
                if t['name'].lower().find(f'{anime_name}'.lower()) != -1 and t['name'].lower().find(f' {episode} ') != -1 and t['name'].lower().find('~') == -1:  # we want to avoid ~ because Erai-Raws use it for already packed episodes
                    torrent = t
                    break
                        
    # The only exception possible is that no torrent have been found when NyaaPy.Nyaa.search() (we are doing dict operations on a None object => raise an exception)
    except:
        return None
    
    return torrent