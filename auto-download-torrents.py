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

    # If you want, you can add uploaders there.
    uploaders = ["Erai-raws", "SubsPlease"]

    choice = 0

    while choice not in [1, 2, 3]:
        print("Choose a quality (you need to unter the corresponding number)\n\n\t1 - 480p\n\t2 - 720p\n\t3 - 1080p\n")
        choice = int(input("> "))

    os.system("cls")

    quality = [480, 720, 1080]

    # If you want, you can add animes here. If you don't know how to use Python, I recommend you to read this in order to avoid errors:
    # >     https://pastebin.com/AKj60M4d     <
    # ["name of your anime", startingFromEpisodeX, endingToEpisodeY]
    watchingAnimes = [
        ["Boku no Hero Academia 5th Season", 1, 12],
        ["Fumetsu No Anata e", 1, 5],
        ["One Piece", 1, 977],
        ["Tokyo Revengers", 1, 10]
    ]
    
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
                    foundTorrent = NyaaPy.Nyaa.search(keyword="[" + u + "] " + item[0] + " - " + str(i) + " [" + str(quality[choice-1]) + "p]", category=1, subcategory=2, filters=2)
                    print("Checking: [" + u + "] " + item[0] + " - " + str(i) + " [" + str(quality[choice-1]) + "p]")
                else:
                    foundTorrent = NyaaPy.Nyaa.search(keyword="[" + u + "] " + item[0] + " - 0" + str(i) + " [" + str(quality[choice-1]) + "p]", category=1, subcategory=2, filters=2)
                    print("Checking: [" + u + "] " + item[0] + " - 0" + str(i) + " [" + str(quality[choice-1]) + "p]")
            
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
                        print("Downloading: " + torrentName + ", please wait...")
                    
                    # We move the downloaded torrent to the dedicated folder.
                    os.system(f"move \"{torrentName}\" \"DownloadedTorrents\\{torrentName}\"")
                    print("\n")

                    # We don't wanna download the same episode from two different uploaders...
                    break
            
                # [...] Else, the program alerts you that no torrent have been found with the corresponding name.
                else:
                    if i >= 10:
                         print("No torrent found for the name: " + "[" + u + "] " + item[0] + " - " + str(i) + " [" + str(quality[choice-1]) + "p].\nMaybe it still hasn't aired...\n")
                    else:
                         print("No torrent found for the name: " + "[" + u + "] " + item[0] + " - 0" + str(i) + " [" + str(quality[choice-1]) + "p].\nMaybe it still hasn't aired...\n")
            
            if stillFoundTorrents:
                continue   

        # This notifies you that every torrent from an anime has been fully downloaded
        toaster = ToastNotifier()
        toaster.show_toast("Nyaa Auto-download","The anime " + item[0] + " has been succesffuly downloaded!")


    break

os.system("cls")
print("\nAll anime have been verified.\nThe program will now close.")
sleep(4)