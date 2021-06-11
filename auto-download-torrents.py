
#------------------------------IMPORTS------------------------------

import NyaaPy
import urllib.request
import shutil
import os
import webbrowser as wb
import win10toast
from time import sleep

#------------------------------GLOBAL VARIABLES------------------------------


uploaders = ["Erai-raws", "SubsPlease"]

quality = [480, 720, 1080]


#------------------------------FUNCTIONS------------------------------


def cleanConsole():
    os.system("cls")


#------------------------------MAIN PROGRAM------------------------------
while True:


    # Main Screen
    print(
        "\nWelcome to my bulk downloader for Nyaa.si!\n\n"
        "\tNote: Make sure to write the title in \"Japanese\".\n"
        "\tFor instance, instead of My Hero Academia, write Boku no Hero Academia.\n\n"
        "\tSince uploaders often use the Japanese title, you won't be able to find your anime otherwise.\n"
        "\tDon't worry, there is no case sensitivity.\n"
        "\tIf you don't know how to say it, you may refer to MyAnimeList.net so you can get both translations.\n\n"
        "Please note that this program isn't made for downloading things like One Piece, Naruto or Bleach.\n"
        "Indeed, there are already multiple torrents that contains every single episodes. Think smart!\n"
        "If you find any bug, please make me know on my GitHub ~~> https://github.com/marcpinet\n\n"
    )
    nextStep = input("Press ENTER to continue...")
    watchingAnimes = []
    stillWantsAnime = True


    while stillWantsAnime:


        cleanConsole()
        tmp = [] 


        # Asking the user to input the anime title.
        print("\n\nPlease, write the name of the anime you want to download:")
        anime = ""
        while len(anime) <= 2:
            anime = input("> ")
            if len(anime) <= 2:
                print("Please, be sure to enter a valide title (not a blank character!)")
        tmp.append(anime)


        # Asking the user to input the episode from where the download should begin...
        print("\n\nStarting from which episode?")
        begin = -1
        while begin not in range(1, 1000):
            try:
                begin = int(input("> "))
            except ValueError:
                print("Please, make sure to input an integer.")
                continue
            if begin not in range(1, 1000) and int(begin) == begin:
                print("Please, make sure to input a value between 1 and 1000.")
        tmp.append(begin)


        # ... and where it should stop.
        print("\n\nUp to which episode?")
        end = -1
        while begin > end or end not in range(1, 1000):
            try:
                end = int(input("> "))
            except ValueError:
                print("Please, make sure to input an integer.")
                continue
            if begin > end or end not in range(1, 1000):
                print("Please, make sure to input a value greater than or equal to the previous one and lower than 1000!")
        tmp.append(end)


        # The quality of the episodes will be defined by the user for each anime.?
        qualityChoice = 0
        print("\n\nIn which quality should the episode be downloaded in? (1=480p, 2=720p, 3=1080p)")
        while qualityChoice not in [1, 2, 3]:
            try:
                qualityChoice = int(input("> "))
            except ValueError:
                print("Please, make sure to input an integer.")
                continue
            if qualityChoice not in [1, 2, 3]:
                print("Please, make sure to answer either 1, 2 or 3.")
        tmp.append(qualityChoice)


        # Finally, we append the tmp list that contains every gathered information above to the main list that will contains every anime.
        watchingAnimes.append(tmp)
        cleanConsole()
        print(f"\n\nAlright, I will download {anime} from episode {begin} to {end} in {quality[qualityChoice-1]}p.")


        # From there, the user will decide whether he wants to download more animes or not.
        print("Do you want to download another anime? (1=Yes, 2=No)")
        answer = 0
        while answer not in [1, 2]:
            try:
                answer = int(input("> "))
            except ValueError:
                print("Please, make sure to input an integer.")
                continue
            if answer not in [1, 2]:
                print("Please, make sure to answer either 1 or 2.")
            elif answer == 2:
                stillWantsAnime = False
                os.system("cls")


    cleanConsole()


    # Finally, the user will have to choose wheter we wants to download them as a .torrent or directly import them as magnet in his/her torrent client.
    print("\n\nFinally, download torrents or open magnets in client? (1=.torrent, 2=magnet)")
    answer = 0
    while answer not in [1, 2]:
        try:
            answer = int(input("> "))
        except ValueError:
            print("Please, make sure to input an integer.")
            continue
        if answer not in [1, 2]:
            print("Please, make sure to answer either 1 or 2.")
    verbalBase = "downloaded" if answer == 1 else "transferred"


    cleanConsole()


    missingTorrents = []


    # For each anime the user has inputted...
    for item in watchingAnimes:


        # The number of downloaded episode of the currently checked anime (item). Will be used to calculate percentage.
        numAnime = 0


        # For each episode from the anime...
        for i in range(int(item[1]), int(item[2] + 1)):
            

            # The program tries to retrieve from Nyaa.si the list of results for the anime and the corresponding episode. It often takes the most recent one.
            for u in uploaders:


                if i >= 10:
                    foundTorrent = NyaaPy.Nyaa.search(keyword=f"[{u}] {item[0]} - {i} [{quality[item[3]-1]}p]", category=1, subcategory=2, filters=2)
                    print(f"Checking: [{u}] {item[0]} - {i} [{quality[item[3]-1]}p]")
                

                else:
                    foundTorrent = NyaaPy.Nyaa.search(keyword=f"[{u}] {item[0]} - 0{i} [{quality[item[3]-1]}p]", category=1, subcategory=2, filters=2)
                    print(f"Checking: [{u}] {item[0]} - 0{i} [{quality[item[3]-1]}p]")
            

            # If at least one torrent has been found [...]
                if len(foundTorrent) != 0:


                    # We take the only two variables from the dictionary we are interested in (the result from the query stored in the variable foundTorrent)
                    downloadLink = foundTorrent[0]["download_url"]
                    torrentName = foundTorrent[0]["name"] + ".torrent"
                    magnet = foundTorrent[0]["magnet"]
                    # We put this variable to True so the program will continue until there is a result
                    stillFoundTorrents = True

                    # If the user chose .torrent option...
                    if answer == 1:
            

                        # If you want more details, just read: https://stackoverflow.com/questions/7243750/download-file-from-web-in-python-3 
                        os.system("mkdir DownloadedTorrents > nul 2>&1")
                        with urllib.request.urlopen(downloadLink) as response, open(torrentName, 'wb') as out_file:
                            shutil.copyfileobj(response, out_file)
                            print(f"Downloading: {torrentName}, please wait...\n")
                        

                        # We move the downloaded torrent to the dedicated folder.
                        os.system(f"move \"{torrentName}\" \"DownloadedTorrents\\{torrentName}\" > nul 2>&1")


                        # We don't wanna download the same episode from two different uploaders...
                        numAnime+=1
                        break
                    

                    # If the user chose magnet option
                    else:
                        print(f"Transferring to torrent client: {torrentName}, please wait...\n")
                        wb.open(magnet)
                        numAnime+=1
                        break
            

                # [...] Else, the program alerts you that no torrent have been found with the corresponding name.
                else:


                    if i >= 10:
                        print(f"No torrent found for the name: [{u}] {item[0]} - {i} [{quality[item[3]-1]}p].\nEither it still hasn't aired or doesn't exist...\n")
                        if f"{item[0]} - Episode {i}" not in missingTorrents:
                            missingTorrents.append(f"{item[0]} - Episode {i}")


                    else:
                        print(f"No torrent found for the name: [{u}] {item[0]} - 0{i} [{quality[item[3]-1]}p].\nEither it still hasn't aired or doesn't exist...\n")
                        if f"{item[0]} - Episode 0{i}" not in missingTorrents:
                            missingTorrents.append(f"{item[0]} - Episode 0{i}")


        # This notifies you that every torrent from an anime has been fully downloaded.
        toaster = win10toast.ToastNotifier()
        percentage = "0" if str(round(numAnime*100/(item[2]-item[1]+1), 2)).strip('0').strip('.') == "" else str(round(numAnime*100/(item[2]-item[1]+1), 2)).strip('0').strip('.')
        toaster.show_toast("Nyaa Auto-download", f"The anime {item[0]} has been {verbalBase} at {percentage}%!")
        percentageStock = []
        percentageStock.append(percentage == "100")


    # Getting out of the while True.
    cleanConsole()
    break


# Creating Logs if missing episodes. Else, do nothing but tells the user that everything went well.
if all(percentageStock):
    print(f"\n\nEvery anime have been fully {verbalBase}! The program will now close itself...")
else:
    print("\n\nThe episodes that couldn't be downloaded have been stored in a .txt file.")
    print("You can access it by going into the same folder as the python script.")
    
    os.system("echo > missingEpisodes.txt 2>&1")
    text = '\n'.join(missingTorrents)

    with open("missingEpisodes.txt", "w") as logs:
        logs.write("The following episodes couldn't be downloaded:\n\n" + text + "\n")
    logs.close()


    print("\nDo wou want to open the .txt file from there or exit the program? (1=.txt, 2=exit)")
    openTxtOrExit = 0
    while openTxtOrExit not in [1, 2]:
        try:
            openTxtOrExit = int(input("> "))
        except ValueError:
            print("Please, make sure to input an integer.")
            continue
        if openTxtOrExit not in [1, 2]:
            print("Please, make sure to answer either 1 or 2.")
        elif openTxtOrExit == 1:
            os.system("missingEpisodes.txt 2>&1")
            print("File opened! The program will shutdown itself once you close the .txt...")


sleep(5)
