#------------------------------IMPORTS------------------------------


import NyaaPy
import urllib.request
import shutil
import os
import webbrowser as wb
import win10toast
from time import sleep


#------------------------------GLOBAL VARIABLES------------------------------


uploaders = ['Erai-raws', 'SubsPlease']

qualities = [480, 720, 1080]


#------------------------------CLASSES, METHODS & FUNCTIONS------------------------------
    
    
class Episode:
    """Class that defines the episode of an anime by different attributes
    """
    
    
    def __init__(self, name: str):
        """Constructor of the Anime class.

        Args:
            name (str): Anime name. Defaults to 'UndefinedAnimeName'.
        """
        self.name = name
        self.successful = 0
    
    
    def download(self, torrentname: str, downloadlink: str):
        """Downloads a file from the web and saves it in a folder that has the name of the downloaded anime (the file also gets its original name).
        If you want more details, just read: https://stackoverflow.com/questions/7243750/download-file-from-web-in-python-3

        Args:
            torrentname (str: The name of the file to be saved.
            downloadlink (str): The link of the file to download.
        """
        os.system('mkdir DownloadedTorrents > nul 2>&1')
        os.system(f'mkdir \"DownloadedTorrents\\{self.name}\" > nul 2>&1')
        
        foldername = self.name
                            
        for s in ['\\', '/', ':', '*', '?', '"', '<', '>', '|']:
            foldername = foldername.replace(s, ' ')
        
        print(f"Downloading: {torrentname}, please wait...\n")
        try :
            with urllib.request.urlopen(downloadlink) as response, open(torrentname, 'wb') as out_file:
                shutil.copyfileobj(response, out_file)
            self.successful += 1
        except:
            print('Download failed. Please, check your internet connection.\n')
            
            
        os.system(f"move \"{torrentname}\" \"DownloadedTorrents\\{foldername}\\{torrentname}\" > nul 2>&1")


    def transfer(self, torrentname: str, magnet: str):
        """Opens user's torrent client and transfers the file to it.

        Args:
            torrentname (str): Torrent name to print to the console for the user to be able to see.
            magnet (str): Magnet link of the torrent to be downloaded.
        """
        print(f'Transferring to torrent client: {torrentname}, please wait...\n')
        try:
            wb.open(magnet)
            self.successful += 1
        except:
            print('Transfer failed. Please, make sure to have a torrent client or a web browser that supports magnet links!')


class Batch:
    """Class that defines a batch of anime.
    """
    
    
    numberOfBatchs = 0
    def __init__(self, animename: str, quality: int, begin: int, end: int):
        """Constructor of the Batch class.

        Args:
            animename (str): Name of the anime.
            quality (int): Quality of the anime to be downloaded.
            begin (int): Episode number of the first episode the user wants to download.
            end (int): Episode number of the last episode the user wants to download.
        """
        self.animename = animename
        self.episode = Episode(animename)
        self.quality = qualities[quality-1]
        self.begin = begin
        self.end = end
        Batch.numberOfBatchs += 1
        

#------------------------------MAIN FUNCTION------------------------------


def main():


    running = True
    while running:


        # Main Screen
        print(
"""

Welcome to my bulk downloader for Nyaa.si!

\tNote: Make sure to write the title in "Japanese".
\tFor instance, instead of My Hero Academia, write Boku no Hero Academia.

\tSince uploaders often use the Japanese title, you won't be able to find your anime otherwise.
\tDon't worry, there is no case sensitivity.

\tIf you don't know how to say it, you may refer to MyAnimeList.net so you can get both translations.

Please note that this program isn't made for downloading things like One Piece, Naruto or Bleach.
Indeed, there are already multiple torrents that contains every single episodes. Think smart!
If you find any bug, please make me know on my GitHub ~~> https://github.com/marcpinet

"""
        )
        
        nextStep = input('Press ENTER to continue...')
        animeToDownload = []
        stillWantsAnime = True


        while stillWantsAnime:


            os.system('cls')


            # Asking the user to input the anime title.
            print('\n\nPlease, write the name of the anime you want to download:')
            animeName = ''
            while len(animeName) <= 2:
                animeName = input('> ')
                
                if len(animeName) <= 2:
                    print('Please, be sure to enter a valide title (not a blank character!)')


            # Asking the user to input the episode from where the download should begin...
            print('\n\nStarting from which episode?')
            animeBegin = -1
            while animeBegin not in range(1, 1000):
                try:
                    animeBegin = int(input('> '))
                    
                except ValueError:
                    print('Please, make sure to input an integer.')
                    continue
                
                if animeBegin not in range(1, 1000) and int(animeBegin) == animeBegin:
                    print('Please, make sure to input a value between 1 and 1000.')


            # ... and where it should stop.
            print('\n\nUp to which episode?')
            animeEnd = -1
            while animeBegin > animeEnd or animeEnd not in range(1, 1000):
                try:
                    animeEnd = int(input('> '))
                    
                except ValueError:
                    print('Please, make sure to input an integer.')
                    continue
                
                if animeBegin > animeEnd or animeEnd not in range(1, 1000):
                    print('Please, make sure to input a value greater than or equal to the previous one and lower than 1000!')


            # The quality of the episodes will be defined by the user for each anime.?
            qualityChoice = 0
            print('\n\nIn which quality should the episode be downloaded in? (1=480p, 2=720p, 3=1080p)')
            while qualityChoice not in [1, 2, 3]:
                try:
                    qualityChoice = int(input('> '))
                    
                except ValueError:
                    print('Please, make sure to input an integer.')
                    continue
                
                if qualityChoice not in [1, 2, 3]:
                    print('Please, make sure to answer either 1, 2 or 3.')


            # Finally, we append the class to the list of animes.
            animeToDownload.append(Batch(animeName, qualityChoice, animeBegin, animeEnd))
            os.system('cls')
            print(f'\n\nAlright, {animeName} from episode {animeBegin} to {animeEnd} will be downloaded in {qualities[qualityChoice-1]}p.')


            # From there, the user will decide whether he wants to download more animes or not.
            print('Do you want to download another anime? (1=Yes, 2=No)')
            answer = 0
            while answer not in [1, 2]:
                try:
                    answer = int(input('> '))
                    
                except ValueError:
                    print('Please, make sure to input an integer.')
                    continue
                
                if answer not in [1, 2]:
                    print('Please, make sure to answer either 1 or 2.')
                    
                elif answer == 2:
                    stillWantsAnime = False
                    os.system('cls')


        os.system('cls')


        # Finally, the user will have to choose whether we wants to download them as a .torrent or directly import them as magnet in his/her torrent client.
        print('\n\nFinally, download torrents or open magnets in client? (1=.torrent, 2=magnet)')
        answer = 0
        while answer not in [1, 2]:
            try:
                answer = int(input('> '))
            except ValueError:
                print('Please, make sure to input an integer.')
                continue
            if answer not in [1, 2]:
                print('Please, make sure to answer either 1 or 2.')
                    
        verbalBase = 'downloaded' if answer == 1 else 'transferred'


        os.system('cls')
        
        
        if Batch.numberOfBatchs == 1:
            print('\n\nThe following anime will be downloaded:\n')
        else:
            print('\n\nThese {Batch.numberOfBatchs} anime will be downloaded:\n')
        for batch in animeToDownload:
            print('\t', batch.episode.name, 'from episode', batch.begin, 'to', batch.end, 'in', str(batch.quality) + 'p')
        nextStep = input('\n\nPress ENTER to continue...')
        os.system('cls')


        # For each anime the user has inputted...
        for batch in animeToDownload:


            # In order to exit the loop when an episode with the 'END' tag is mentionned inside it (Erai-Raws does that, not SubsPlease)
            unexpectedEnd = False


            # For each episode from the anime...
            for i in range(batch.begin, batch.end + 1):


                # The program tries to retrieve from Nyaa.si the list of results for the anime and the corresponding episode. It often takes the most recent one.
                for u in uploaders:


                    if i >= 10:
                        epValue = str(i)
                    else:
                        epValue = '0' + str(i)


                    foundTorrent = NyaaPy.Nyaa.search(keyword=f'[{u}] {batch.episode.name} - {epValue} [{batch.quality}p]', category=1, subcategory=2, filters=2)
                    print(f'Checking: [{u}] {batch.episode.name} - {epValue} [{batch.quality}p]')

                    try:
                        # We take the closest title to what we are looking for in order to avoid errors while browsing among every found torrents
                        torrent = None
                        for t in foundTorrent:
                            if t['name'].lower().find(f'{batch.episode.name} - {epValue}'.lower()) != -1:
                                torrent = t

                        # Else, we take try to get the closest title to the one we are looking for.
                        if torrent == None:
                            for t in foundTorrent:
                                if t['name'].lower().find(f'{batch.episode.name}'.lower()) != -1 and t['name'].lower().find(f'{epValue}'.lower()) != -1:
                                    torrent = t
                    
                    except:
                        pass
                        
                    # If at least one torrent has been found [...]
                    if torrent != None:

                        # We take the only two variables from the dictionary we are interested in (the result from the query stored in the variable foundTorrent)
                        downloadlink = torrent['download_url']
                        torrentname = torrent['name'] + '.torrent'
                        magnet = torrent['magnet']
                        
                        # We put this variable to True so the program will continue until there is a result
                        stillFoundTorrents = True
                        
                        # If the user chose .torrent option...
                        if answer == 1:
                            # We download the .torrent file and save it in a folder which is in the same folder as where the script is running from.
                            batch.episode.download(torrentname, downloadlink)

                        # If the user chose magnet option
                        else:
                            # We transfer it to a bittorent client which the user is supposed to have...
                            batch.episode.transfer(torrentname, magnet)
                        

                        if u == 'Erai-raws' and torrentname.find(' END [') != -1:
                            print(f'Hey, {batch.episode.name} has no more than {epValue} episodes!...\n')
                            unexpectedEnd = True


                        # We don't wanna download the same episode from two different uploaders...
                        break


                    # [...] Else, the program alerts you that no torrent have been found with the corresponding name.
                    else:
                        print(f"No torrent found for the name: [{u}] {batch.episode.name} - {epValue} [{batch.quality}p].\nEither it still hasn't aired or doesn't exist...\n")
                        
                        # Just wanted to use that (lol) but it also makes the program use less RAM (like 8 bytes lmao)
                        if 'missingTorrents' not in locals():
                                missingTorrents = []
                        
                        # When uploaders reaches the index -1, it means that every uploader has been tried.
                        if f'{batch.episode.name} - Episode {epValue}' not in missingTorrents and u == uploaders[-1]:
                            missingTorrents.append(f'{batch.episode.name} - Episode {epValue}')


                # So we don't check for inexistant title
                if unexpectedEnd:
                    break


            if unexpectedEnd:
                percentage = '0' if str(round(batch.episode.successful*100/(int(epValue) - batch.begin + 1), 2)).strip('0').strip('.') == '' else str(round(batch.episode.successful*100/(int(epValue) - batch.begin + 1), 2)).strip('0').strip('.')

            else:
                percentage = '0' if str(round(batch.episode.successful*100/(batch.end - batch.begin + 1), 2)).strip('0').strip('.') == '' else str(round(batch.episode.successful*100/(batch.end - batch.begin + 1), 2)).strip('0').strip('.')
            
            
            # This notifies you that every torrent from an anime has been fully downloaded.
            toaster = win10toast.ToastNotifier()
            toaster.show_toast('Nyaa Auto-download', f'The anime {batch.episode.name} has been {verbalBase} at {percentage}%!')

            # Checking if every anime have indeed been downloaded at 100%
            if 'percentageStock' not in locals():
                percentageStock = []
            percentageStock.append(percentage == '100')


        # Getting out of the while True.
        os.system('cls')
        running = False


    # Creating Logs if missing episodes. Else, do nothing but tells the user that everything went well.
    if all(percentageStock):
        
        print(f'\nEvery anime has been fully {verbalBase}!\n')
        if verbalBase == 'downloaded':
            exitVariable = input('Press enter to exit and open the folder containing .torrent files...')
        else:
            exitVariable = input('Press enter to exit...')
    
    else:
        print("\n\nThe episodes that couldn't be downloaded have been stored in a .txt file.")
        print('You can access it by going into the same folder as the python script.')
        
        os.system('echo > missingEpisodes.txt 2>&1')
        text = '\n'.join(missingTorrents)

        with open('missingEpisodes.txt', 'w') as logs:
            logs.write("The following episodes couldn't be downloaded:\n\n" + text + '\n')

        print('\nDo wou want to open the .txt file from there or exit the program? (1=.txt, 2=exit)')
        
        openTxtOrExit = 0
        while openTxtOrExit not in [1, 2]:
            try:
                openTxtOrExit = int(input('> '))
                
            except ValueError:
                print('Please, make sure to input an integer.')
                continue
            
            if openTxtOrExit not in [1, 2]:
                print('Please, make sure to answer either 1 or 2.')
                
            elif openTxtOrExit == 1:
                print('File opened! The program will shutdown itself once you close the .txt...')
                
                if verbalBase == 'downloaded':
                    print('The folder containing .torrent files will then be opened.')
                
                os.system('missingEpisodes.txt 2>&1')
                sleep(5)
                
            else:
                print('Ok.')
                sleep(2.5)

    if verbalBase == 'downloaded':
        os.system('start DownloadedTorrents 2>&1')


#------------------------------MAIN CALL------------------------------


if __name__ == '__main__':
    main()
