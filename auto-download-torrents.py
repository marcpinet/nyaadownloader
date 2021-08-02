
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


class Anime:
    """
    Class that defines anime by different attributes : name, quality, episodes, etc.
    """
    numberOfAnime = 0
    def __init__(self, name, quality, begin, end):
        self.name = name
        self.quality = qualities[quality-1]
        self.begin = begin
        self.end = end
        Anime.numberOfAnime += 1


    def download(self, torrentName, downloadLink, animeName):
        """
        If you want more details, just read: https://stackoverflow.com/questions/7243750/download-file-from-web-in-python-3 
        """
        os.system('mkdir DownloadedTorrents > nul 2>&1')
        os.system(f'mkdir \"DownloadedTorrents\\{animeName}\" > nul 2>&1')
        with urllib.request.urlopen(downloadLink) as response, open(torrentName, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)
            print(f"Downloading: {torrentName}, please wait...\n")
        os.system(f"move \"{torrentName}\" \"DownloadedTorrents\\{animeName}\\{torrentName}\" > nul 2>&1")


    def transfer(self, magnet, torrentName=''):
        print(f'Transferring to torrent client: {torrentName}, please wait...\n')
        wb.open(magnet)

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
        watchingAnimes = []
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
            watchingAnimes.append(Anime(animeName, qualityChoice, animeBegin, animeEnd))
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


        missingTorrents = []


        # For each anime the user has inputted...
        for item in watchingAnimes:

            # In order to exit the loop when an episode with the 'END' tag is mentionned inside it (Erai-Raws does that, not SubsPlease)
            unexpectedEnd = False

            # The number of downloaded episode of the currently checked anime (item). Will be used to calculate percentage.
            foundAnimes = 0


            # For each episode from the anime...
            for i in range(item.begin, item.end + 1):
                

                # The program tries to retrieve from Nyaa.si the list of results for the anime and the corresponding episode. It often takes the most recent one.
                for u in uploaders:


                    if i >= 10:
                        epValue = str(i)
                    else:
                        epValue = '0' + str(i)


                    foundTorrent = NyaaPy.Nyaa.search(keyword=f'[{u}] {item.name} - {epValue} [{item.quality}p]', category=1, subcategory=2, filters=2)
                    print(f'Checking: [{u}] {item.name} - {epValue} [{item.quality}p]')
                

                    # If at least one torrent has been found [...]
                    if len(foundTorrent) != 0:

                        # We take the closest title to what we are looking for in order to avoid errors while browsing among every found torrents
                        torrent = None
                        for t in foundTorrent:
                            if t['name'].lower().find(f'{item.name} - {epValue}'.lower()) != -1:
                                torrent = t

                        if torrent == None:
                            torrent = foundTorrent[0]
                            

                        # We take the only two variables from the dictionary we are interested in (the result from the query stored in the variable foundTorrent)
                        downloadLink = torrent['download_url']
                        torrentName = torrent['name'] + '.torrent'
                        magnet = torrent['magnet']
                        # We put this variable to True so the program will continue until there is a result
                        stillFoundTorrents = True
                        foundAnimes+=1
                        # If the user chose .torrent option...
                        if answer == 1:
                            # We download and then move the downloaded torrent to the dedicated folder.
                            foldername = item.name
                            for s in ['\\', '/', ':', '*', '?', '"', '<', '>', '|']:
                                foldername = foldername.replace(s, ' ')

                            item.download(torrentName, downloadLink, foldername)

                        # If the user chose magnet option
                        else:
                            # We transfer it to a bittorent client which the user is supposed to have...
                            item.transfer(magnet, torrentName)
                        

                        if u == 'Erai-raws' and torrentName.find(' END [') != -1:
                            print(f'Hey!, {item.name} has no more than {epValue}...\n')
                            unexpectedEnd = True


                        # We don't wanna download the same episode from two different uploaders...
                        break


                    # [...] Else, the program alerts you that no torrent have been found with the corresponding name.
                    else:
                        print(f"No torrent found for the name: [{u}] {item.name} - {epValue} [{item.quality}p].\nEither it still hasn't aired or doesn't exist...\n")
                        if f'{item.name} - Episode {epValue}' not in missingTorrents and u == uploaders[-1]:
                            missingTorrents.append(f'{item.name} - Episode {epValue}')


                # So we don't check for inexistant title
                if unexpectedEnd:
                    break


            if unexpectedEnd:
                percentage = '0' if str(round(foundAnimes*100/(int(epValue) - item.begin + 1), 2)).strip('0').strip('.') == '' else str(round(foundAnimes*100/(int(epValue) - item.begin + 1), 2)).strip('0').strip('.')

            else:
                percentage = '0' if str(round(foundAnimes*100/(item.end - item.begin + 1), 2)).strip('0').strip('.') == '' else str(round(foundAnimes*100/(item.end - item.begin + 1), 2)).strip('0').strip('.')
            
            # This notifies you that every torrent from an anime has been fully downloaded.
            toaster = win10toast.ToastNotifier()
            toaster.show_toast('Nyaa Auto-download', f'The anime {item.name} has been {verbalBase} at {percentage}%!')
            percentageStock = []
            percentageStock.append(percentage == '100')


        # Getting out of the while True.
        os.system('cls')
        running = False


    # Creating Logs if missing episodes. Else, do nothing but tells the user that everything went well.
    if all(percentageStock):
        print(f'\nEvery anime have been fully {verbalBase}!\n')
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
