# Main imports
import NyaaPy
import urllib.request
import shutil
import os

# Misc Imports
from time import sleep
from win10toast import ToastNotifier

# Because I don't know how to do it else. A simple, but still good, while True.
while True:

    # If you want, you can add uploaders there. I only trust these two ones and they use the best encoding of all time.
    uploaders = [
        "Erai-raws",
        "SubsPlease"
    ]

    quality = [480, 720, 1080]
    qualityChoice = 0

    # Main screen
    print(
        "Welcome to my bulk downloader for Nyaa.si!\n\n"
        "\tNote: Make sure to write the title in \"Japanese\".\n"
        "\tFor instance, instead of My Hero Academia, write Boku no Hero Academia.\n\n"
        "\tSince uploaders often use the Japanese title, you won't be able to find your anime otherwise.\n"
        "\tDon't worry, there is no case sensitivity.\n"
        "\tIf you don't know how to say it, you may refer to MyAnimeList.net so you can get both translations.\n\n"
        "Please note that this program isn't made for downloading things like One Piece, Naruto or Bleach.\n"
        "Indeed, there are already multiple torrents that contains every single episodes. Think smart!\n"
        "If you find any bug, please make me know on my GitHub ~~> https://github.com/marcpinet\n\n"
    )

    # Yes.
    uselessVariable = input("Press Enter to continue...")

    # We try to get mutliples list inside this list with the starting episode and the last one the user chose.
    watchingAnimes = []
    stillWantsAnime = True

    while stillWantsAnime:
        os.system("cls")
        # Temporary list containing every informations needed for an anime.
        tmp = []
        print("Please, write the name of the anime you want to download:")
        anime = input("> ")
        tmp.append(anime)

        print("\nStarting from which episode?")
        begin = -1

        while begin not in range(1, 1000):
            begin = int(input("> "))
            if begin not in range(1, 1000):
                print("Please, make sure to input a value between 1 and 1000.\n")
        tmp.append(begin)

        print("\nUntil which episode?")
        end = -1

        while begin > end:
            end = int(input("> "))
            if begin > end:
                print("Please, make sure to input a value greater than or equal to the previous one.\n")
        tmp.append(end)

        watchingAnimes.append(tmp)
        print(f"I will download {anime} from episode {begin} to {end}.\n\n")

        # From there, the user will decide wether he wants to download more animes or not.
        print("Do you want to download another anime? (1=Yes, 2=No)\n")
        answer = 0

        while answer not in [1, 2]:
            answer = int(input("> "))
            if answer not in [1, 2]:
                print("Please, make sure to answer either 1 or 2.\n")
            elif answer == 2:
                stillWantsAnime = False
                os.system("cls")

    # Choose the quality
    while qualityChoice not in [1, 2, 3]:
        print("Choose a quality (you need to unter the corresponding number)\n\n\t1 - 480p\n\t2 - 720p\n\t3 - 1080p\n")
        qualityChoice = int(input("> "))

    os.system("cls")

    nbFound = len(watchingAnimes)
    os.system("mkdir DownloadedTorrents")

    # For each anime you're watching
    for item in watchingAnimes:
        # We make the program thinks that no torrent have been found and we start to the first anime (0)
        stillFoundTorrents = False
        numAnime = 0

        # For each episode from the anime...
        for i in range(int(item[1]), int(item[2] + 1)):
            # The program tries to retrieve from Nyaa.si the list of results for the anime and the corresponding episode. It often takes the most recent one.
            for u in uploaders:

                if i >= 10:
                    foundTorrent = NyaaPy.Nyaa.search(keyword=f"[{u}] {item[0]} - {i} [{quality[qualityChoice-1]}p]", category=1, subcategory=2, filters=2)
                    print(f"Checking: [{u}] {item[0]} - {i} [{quality[qualityChoice-1]}p]")
                else:
                    foundTorrent = NyaaPy.Nyaa.search(keyword=f"[{u}] {item[0]} - 0{i} [{quality[qualityChoice-1]}p]", category=1, subcategory=2, filters=2)
                    print(f"Checking: [{u}] {item[0]} - 0{i} [{quality[qualityChoice-1]}p]")
            
            # If at least one torrent has been found [...]
                if len(foundTorrent) != 0:
                    # We take the only two variables from the dictionary we are interested in (the result from the query stored in the variable foundTorrent)
                    downloadLink = foundTorrent[0]["download_url"]
                    torrentName = foundTorrent[0]["name"] + ".torrent"
                    # We put this variable to True so the program will continue until there is a result
                    stillFoundTorrents = True

                    # To be honest with you, this one is a copy/paste from StackOverflow since it was my first web scrapping program. But I can tell you that I now understand what it does.
                    # If you want more details, just read: https://stackoverflow.com/questions/7243750/download-file-from-web-in-python-3 
                    with urllib.request.urlopen(downloadLink) as response, open(torrentName, 'wb') as out_file:
                        shutil.copyfileobj(response, out_file)
                        print(f"Downloading: {torrentName}, please wait...")
                    
                    # We move the downloaded torrent to the dedicated folder.
                    os.system(f"move \"{torrentName}\" \"DownloadedTorrents\\{torrentName}\"")
                    print("\n")

                    # We don't wanna download the same episode from two different uploaders...
                    break
            
                # [...] Else, the program alerts you that no torrent have been found with the corresponding name.
                else:
                    if i >= 10:
                         print(f"No torrent found for the name: [{u}] {item[0]} - 0{i} [{quality[qualityChoice-1]}p].\nMaybe it still hasn't aired...\n")
                    else:
                         print(f"No torrent found for the name: [{u}] {item[0]} - 0{i} [{quality[qualityChoice-1]}p].\nMaybe it still hasn't aired...\n")
            
            if stillFoundTorrents:
                continue   

        # This notifies you that every torrent from an anime has been fully downloaded
        toaster = ToastNotifier()
        toaster.show_toast("Nyaa Auto-download", f"The anime {item[0]} has been succesffuly downloaded!")


    break

os.system("cls")
print("\nAll anime have been successfully downloaded.\nThe program will now close.")
sleep(4)