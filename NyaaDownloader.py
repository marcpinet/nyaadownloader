# ------------------------------IMPORTS------------------------------


import NyaaPy
import urllib.request
import shutil
import os
import webbrowser as wb
import sys

from winotify import Notification, audio
from time import sleep


# ------------------------------GLOBAL VARIABLES------------------------------


# Default uploaders
uploaders = ['Erai-raws', 'SubsPlease']

# Different qualities available
QUALITIES = (480, 720, 1080)


#------------------------------CLASSES, METHODS & FUNCTIONS------------------------------


def show_uploaders():
    print('\n\n The current uploaders are: \n')
    i = 1
    for uploader in uploaders:
        print(f'\t {i} - {uploader}')
        i += 1


class Batch:
    """Class that defines a batch of anime.
    """
    
    
    number_of_batchs = 0
    def __init__(self, name: str, quality: int, begin: int, end: int):
        """Constructor of the Batch class.

        Args:
            name (str): Name of the anime.
            quality (int): Quality of the anime to be downloaded.
            begin (int): Episode number of the first episode the user wants to download.
            end (int): Episode number of the last episode the user wants to download.
        """
        self.name = name
        self.quality = QUALITIES[quality-1]
        self.begin = begin
        self.end = end
        self.successful = 0
        self.fail_number = 0
        Batch.failed = []
        
    def download(self, torrent: dict):
        """Downloads a file from the web and saves it in a folder that has the name of the downloaded anime (the file also gets its original name).
        If you want more details, just read: https://stackoverflow.com/questions/7243750/download-file-from-web-in-python-3

        Args:
            torrent (dict): The dictionary returned by the NyaaPy.search() method.
        """
        os.system('mkdir DownloadedTorrents > nul 2>&1')
        
        foldername = self.name
        
        # To avoid unwanted characters that Windows does not support (for folder names)
        for s in ['\\', '/', ':', '*', '?', '"', '<', '>', '|']:
            foldername = foldername.replace(s, ' ')
        
        os.system(f'mkdir \"DownloadedTorrents\\{foldername}\" > nul 2>&1')
        
        print(f" Downloading: {torrent['name']}, please wait...\n")
        try :
            with urllib.request.urlopen(torrent['download_url']) as response, open(torrent['name'] + '.torrent', 'wb') as out_file:
                shutil.copyfileobj(response, out_file)
            
            # I prefer to add the .torrent at the very last moment so that the user will know if the file has fully downloaded (moved to the right folder once it's done).
            os.system(f"move \"{torrent['name']}.torrent\" \"DownloadedTorrents\\{foldername}\\{torrent['name']}.torrent\" > nul 2>&1")    
            
            self.successful += 1
            
        except:
            print(' Download failed. Please, check your internet connection.\n')
            Batch.failed.append({'name': torrent['name'], 'reason': 'No internet connection or file permission error', 'code': '1'})

    def transfer(self, torrent: dict):
        """Opens the user's torrent client and transfers the file to it.

        Args:
            torrent (dict): The dictionary returned by the NyaaPy.search() method.
        """
        print(f" Transferring to torrent client: {torrent['name']}, please wait...\n")
        try:
            wb.open(torrent['magnet'])
            self.successful += 1
            
        except:
            print(' Transfer failed. Please, make sure to have a torrent client or a web browser that supports magnet links!')
            Batch.failed.append({'name': torrent['name'], 'reason': 'No torrent client found.', 'code': '1'})
        

#------------------------------MAIN FUNCTION------------------------------


def main():


    running = True
    while running:


        # Main Screen
        print(
"""

 Welcome to my batch downloader for Nyaa.si!

\t Note: Make sure to write the title in Japanese.
\t For instance, instead of writting My Hero Academia, write Boku no Hero Academia.

\t Since uploaders often use the Japanese title, you won't be able to find your anime otherwise.
\t Don't worry, there is no case sensitivity.
\t Also, for instance, the uploader Erai-Raws specifies the season number for the title (e.g Boku no Hero Academia 5th Season).
\t SubsPlease increases the episode number without using the season number (e.g Boku no Hero Academia - 103).
\t Erai-Raws would be better for one season whereas SubsPlease might be better when you want to download many seasons at once.

\t If you don't know how to say it, you may refer to MyAnimeList.net so you can get both translations.

\t Please note that this program isn't made for downloading huge and old things like Bleach.
\t Indeed, there are already multiple torrents that contains every single episodes. Think smart!
\t Don't make it wrong, you can still download the latest episodes of things like One Piece.
\t It only depends on whether the uploaders uploaded them episode by episode or not.
 
 If you find any bug, please make me know on my GitHub ~~> https://github.com/marcpinet

"""
        )
        
        user_input = input(' Press ENTER to continue...')
        anime_to_check = []
        percentage_stock = []  # Will be used to determine whether all anime have been succesfully downloaded or not.
        still_wants_anime = True


        os.system('cls')
        show_uploaders()


        # Input of the uploaders to be added (whether or not)
        print('\n Firstly, add one? (1=Yes, 2=No)')
        user_input = 0
        while user_input not in [1, 2]:
            try:
                user_input = int(input(' > '))
                
            except ValueError:
                print(' Please, make sure to input an integer.')
                continue
            
            if user_input not in [1, 2]:
                print(' Please, make sure to answer either 1 or 2.')
                
            elif user_input == 1:
                print('\n\n Enter the name of the uploader you want to add (or type "-1" to skip this step): ')
                while user_input != '-1':
                    user_input = input(' > ')
                    if user_input != '-1':
                        if user_input not in uploaders:
                            uploaders.strip().append(user_input)
                            print(f' Added {user_input}')
                            show_uploaders()
                        else:
                            print(' This one is already in the list...')
                            continue
                        
                        print('\n Add another one: (or type "-1" to skip this step)')
                    else:
                        user_input = 2
                        break
                    
        
        os.system('cls')
        show_uploaders()
        

        # Input of the uploaders to be removed (whether or not)
        print('\n Next, remove one? (1=Yes, 2=No)')
        user_input = -1
        while user_input not in [1, 2]:
            try:
                user_input = int(input(' > '))
                
            except ValueError:
                print(' Please, make sure to input an integer.')
                continue
            
            if user_input not in [1, 2]:
                print(' Please, make sure to answer either 1 or 2.')
                
            elif user_input == 1:
                
                user_input = 0
                print('\n\n Enter the number of the uploader you want to remove (or type "-1" to stop): ')
                while user_input != -1:
                    try:
                        user_input = int(input(' > '))
                        
                    except ValueError:
                        print(' Please, make sure to input an integer.')
                        continue
                    
                    if len(uploaders) == 1:
                        print(" You can't remove the last one.")
                        user_input = input('\n\n Press ENTER to continue...')
                        user_input = 2
                        break
                    
                    if user_input == -1:
                        user_input = 2
                        break
                    
                    if user_input not in range(1, len(uploaders)+1):
                        print(f' Please, make sure to input an integer between 1 and {len(uploaders)}')
                    
                    elif user_input in range(1, len(uploaders)+1):
                        print(f' Removed {uploaders[user_input-1]}')
                        del uploaders[user_input-1]
                        show_uploaders()
                        print('\n Remove another one: (or type "-1" to stop)')

        # Input of every anime informations
        while still_wants_anime:
                            
            
            os.system('cls')


            # Asking the user to input the anime title.
            print('\n\n Please, write the name of the anime you want to download: (spell it correctly!)')
            anime_name = ''
            while len(anime_name) <= 2:
                # We correct the user input by replacing the spaces with the correct format (in case he added more spaces than expected).
                anime_name = ' '.join(a for a in input(' > ').strip().split(' ') if a != '')
                
                if len(anime_name) <= 2:
                    print(' Please, be sure to enter a valide title (not a blank character!)')
                
                # We check if the input exists in Nyaa.si (to avoid a misspelt title or a wrong one).
                try:
                    if len(NyaaPy.Nyaa.search(keyword=anime_name, category=1, subcategory=2, filters=2)) == 0:
                        print(" This anime doesn't exit in Nyaa.si database. Try to check its spelling on MyAnimeList.net or read yourself again!")
                        anime_name = ''  # We reset it, so the user will be asked again.
                    
                except:
                    sys.exit(" No internet connection available")


            # Asking the user to input the episode from where the download should begin...
            print('\n\n Starting from which episode?')
            anime_begin = 0
            while anime_begin not in range(1, 1000):
                try:
                    anime_begin = int(input(' > '))
                    
                except ValueError:
                    print(' Please, make sure to input an integer.')
                    continue
                
                if anime_begin not in range(1, 1000) and int(anime_begin) == anime_begin:
                    print(' Please, make sure to input a value between 1 and 1000.')


            # ... and where it should stop.
            print('\n\n Up to which episode? (or type -1 to get all episodes)')
            anime_end = 0
            while anime_begin > anime_end or anime_end not in range(1, 1000):
                try:
                    anime_end = int(input(' > '))
                    
                except ValueError:
                    print(' Please, make sure to input an integer.')
                    continue

                if anime_end == -1:
                    anime_end = 1000  # The user can't type 1000, so we'll use that value to identify his choice
                    break
                
                elif anime_begin > anime_end or anime_end not in range(1, 1000):
                    print(' Please, make sure to input a value greater than or equal to the previous one and lower than 1000!')


            # The quality of the episodes will be defined by the user for each anime?
            quality_choice = 0
            print('\n\n In which quality should the episode be downloaded in? (1=480p, 2=720p, 3=1080p)')
            while quality_choice not in [1, 2, 3]:
                try:
                    quality_choice = int(input(' > '))
                    
                except ValueError:
                    print(' Please, make sure to input an integer.')
                    continue
                
                if quality_choice not in [1, 2, 3]:
                    print(' Please, make sure to answer either 1, 2 or 3.')


            # Finally, we append the class to the list of animes.
            anime_to_check.append(Batch(anime_name, quality_choice, anime_begin, anime_end))
            os.system('cls')
            print(f'\n\n Alright, {anime_name} from episode {anime_begin} to {anime_end if anime_end != 1000 else "the end"} will be downloaded in {QUALITIES[quality_choice-1]}p.')


            # From there, the user will decide whether he wants to download more animes or not.
            print(' Do you want to download another anime? (1=Yes, 2=No)')
            user_input = 0
            while user_input not in [1, 2]:
                try:
                    user_input = int(input(' > '))
                    
                except ValueError:
                    print(' Please, make sure to input an integer.')
                    continue
                
                if user_input not in [1, 2]:
                    print(' Please, make sure to answer either 1 or 2.')
                    
                elif user_input == 2:
                    still_wants_anime = False
                    os.system('cls')


        os.system('cls')


        # Finally, the user will have to choose whether we wants to download them as a .torrent or directly import them as magnet in his/her torrent client.
        print('\n\n Finally, download torrents or open magnets in client? (1=.torrent, 2=magnet)')
        torr_choice = 0
        while torr_choice not in [1, 2]:
            try:
                torr_choice = int(input(' > '))
            except ValueError:
                print(' Please, make sure to input an integer.')
                continue
            if torr_choice not in [1, 2]:
                print(' Please, make sure to answer either 1 or 2.')
                    
        verbal_base = 'downloaded' if torr_choice == 1 else 'transferred'


        os.system('cls')
        
        
        if len(anime_to_check) == 1:
            print('\n\n The following anime will be downloaded:\n')
        else:
            print(f'\n\n These {len(anime_to_check)} anime will be downloaded:\n')
        for batch in anime_to_check:
            print('\t', batch.name, 'from episode', batch.begin, 'to', batch.end if batch.end != 1000 else "the end", 'in', str(batch.quality) + 'p')
        user_input = input('\n\n Press ENTER to continue...')
        os.system('cls')


        # For each anime the user has inputted...
        for batch in anime_to_check:


            # In order to exit the loop when an episode with the 'END' tag is mentionned inside it (Erai-Raws does that, not SubsPlease)
            unexpected_end = False


            # For each episode from the anime...
            for i in range(batch.begin, batch.end + 1):


                # The program tries to retrieve from Nyaa.si the list of results for the anime and the corresponding episode. It often takes the most recent one.
                for u in uploaders:


                    if i >= 10:
                        ep_value = str(i)
                    else:
                        ep_value = '0' + str(i)


                    found_torrents = NyaaPy.Nyaa.search(keyword=f'[{u}] {batch.name} - {ep_value} [{batch.quality}p]', category=1, subcategory=2, filters=2)
                    print(f' Checking: [{u}] {batch.name} - {ep_value} [{batch.quality}p]')

                    try:
                        # We take the very closest title to what we are looking for in order to avoid errors while browsing among every found torrents
                        torrent = None
                        for t in found_torrents:
                            if t['name'].lower().find(f'{batch.name} - {ep_value}'.lower()) != -1 and t['name'].lower().find('~') == -1:  # we want to avoid ~ because Erai-Raws use it for already packed episodes
                                torrent = t
                                break  # break if found, so we get the most recent one

                        # Else, we take try to get the closest title to the one we are looking for. (break if found, so we get the most recent one)
                        if torrent is None:
                            for t in found_torrents:
                                if t['name'].lower().find(f'{batch.name}'.lower()) != -1 and t['name'].lower().find(f' {ep_value} ') != -1 and t['name'].lower().find('~') == -1:  # we want to avoid ~ because Erai-Raws use it for already packed episodes
                                    torrent = t
                                    break
                    
                    # The only exception possible is that no torrent have been found => torrent = None => goes to the else block.
                    except:
                        pass
                        
                    # If at least one torrent has been found [...]
                    if torrent is not None:

                        # Note: If 5 torrents ___in a row___ couldn't be retrieved and the user choose the option 'download full show', it will stop checking
                        batch.fail_number = 0
                        
                        # If the user chose .torrent option...
                        if torr_choice == 1:
                            # We download the .torrent file and save it in a folder which is in the same folder as where the script is running from.
                            batch.download(torrent)

                        # If the user chose magnet option
                        else:
                            # We transfer it to a bittorent client which the user is supposed to have...
                            batch.transfer(torrent)
                    

                        if u == 'Erai-raws' and torrent['name'].find(' END [') != -1:
                            print(f' Hey, {batch.name} has no more than {ep_value} episodes!\n') if batch.end != 1000 else print(' Last episode reached.\n')
                            unexpected_end = True


                        # We don't wanna download the same episode from two different uploaders...
                        break


                    # [...] Else, the program alerts you that no torrent have been found with the corresponding name.
                    else:
                        print(f" No torrent found from {u} for the name: {batch.name} - {ep_value} [{batch.quality}p].\n Either it still hasn't aired or doesn't exist...\n")
                        
                        # When uploaders reaches the index -1, it means that every uploader has been tried.
                        if u == uploaders[-1]:
                            Batch.failed.append({'name': f'{batch.name} - {ep_value}', 'reason': 'Does not exist on Nyaa.si', 'code': '0'})
                            batch.fail_number += 1

                            if batch.end == 1000 and batch.fail_number > 4:
                                print(f' Last episode seems to be the last one found ({int(ep_value)-5}).\n')
                                del Batch.failed[-5:]
                                unexpected_end = True
                                break


                # So we don't check for inexistant title
                if unexpected_end:
                    break

            if batch.end == 1000 and torrent['name'].find(' END [') == -1:
                percentage = '0' if str(round(batch.successful*100/(int(ep_value) - 5 - batch.begin + 1), 2)).strip('0').strip('.') == '' else str(round(batch.successful*100/(int(ep_value) - 5 - batch.begin + 1), 2)).strip('0').strip('.')

            elif unexpected_end:
                percentage = '0' if str(round(batch.successful*100/(int(ep_value) - batch.begin + 1), 2)).strip('0').strip('.') == '' else str(round(batch.successful*100/(int(ep_value) - batch.begin + 1), 2)).strip('0').strip('.')

            else:
                percentage = '0' if str(round(batch.successful*100/(batch.end - batch.begin + 1), 2)).strip('0').strip('.') == '' else str(round(batch.successful*100/(batch.end - batch.begin + 1), 2)).strip('0').strip('.')
            
            
            # This notifies you that every torrent from an anime has been fully downloaded.
            toast = Notification(
                app_id='Nyaa Downloader',
                title='Nyaa Downloader',
                msg=f'The anime {batch.name} has been {verbal_base} at {percentage}%!',
            )

            toast.set_audio(audio.Default, loop=False)

            toast.build().show()
            sleep(3.3)
            
            # Boolean if every anime have indeed been downloaded at 100% (will be checked later with the all() function).
            percentage_stock.append(percentage == '100')


        # Getting out of the while True.
        os.system('cls')
        running = False


    # Creating Logs if missing episodes. Else, do nothing but tells the user that everything went well.
    if all(percentage_stock):
        
        print(f'\n Every anime has been fully {verbal_base}!\n')
        if verbal_base == 'downloaded':
            user_input = input(' Press ENTER to exit and open the folder containing .torrent files...')
        else:
            user_input = input(' Press ENTER to exit...')
    
    else:
        print("\n\n The episodes that couldn't be downloaded have been stored in a .txt file.")
        print(' You can access it by going into the same folder as the python script.')
        
        os.system('echo > MissingEpisodes.txt > nul 2>&1')
        text = '\n'.join([' '.join(x['name'].split(' ')[1:]) if x['code'] == 1 else x['name'] + ' || REASON: ' + x['reason'] for x in Batch.failed])

        with open('MissingEpisodes.txt', 'w') as logs:
            logs.write("The following episodes couldn't be downloaded:\n\n" + text + '\n')

        print('\n Do wou want to open the .txt file from there or exit the program? (1=.txt, 2=exit)')
        
        user_input = 0
        while user_input not in [1, 2]:
            try:
                user_input = int(input(' > '))
                
            except ValueError:
                print(' Please, make sure to input an integer.')
                continue
            
            if user_input not in [1, 2]:
                print(' Please, make sure to answer either 1 or 2.')
                
            elif user_input == 1:
                print('\n\n File opened! The program will shutdown itself in 5 seconds...')
                
                if verbal_base == 'downloaded':
                    print(' The folder containing .torrent files will then be opened.')
                
                os.system('start MissingEpisodes.txt > nul 2>&1')
                sleep(5)
                
            else:
                print(' Ok.')
                sleep(2.5)

    if verbal_base == 'downloaded' and any([bool(x.successful) for x in anime_to_check]) > 0:
        os.system('start DownloadedTorrents > nul 2>&1')


#------------------------------MAIN CALL------------------------------


if __name__ == '__main__':
    os.system("mode con: cols=150 lines=30")
    main()
