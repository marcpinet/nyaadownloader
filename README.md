<h1>❓ How it Works </h1>
Formerly console-based, NyaaDownloader is a lightweight and user-friendly tool with a Graphical User Interface that allows to you to downlod many .torrent (or transfer magnets) at a time. <br><br>
The search engine is based on <a href="https://nyaa.si/" target=_blank>Nyaa.si</a> one and the way the script looks for episode is constantly improved to avoid errors and differenciate the way uploaders name their torrents.<br><br>
If you want to add or remove a provider (uploader) like <a href=https://beta.erai-raws.info><i>Erai-Raws</i></a> or <a href=https://subsplease.org><i>SubsPlease</i></a> etc., well... you can, directly in the GUI.<br>
Since they are the only two uploaders that are mainly active and trusted by <a href="https://nyaa.si/" target=_blank>Nyaa.si</a>, I decided to only put those two. Feel free to add any other uploader you trust (and remove the ones that you're not interested in).<br><br>
The program have been made so that the user <b>won't make any mistake</b> in the input and will be warned if the anime title he wrote exists.<br><br>
You specify the anime name, the episode where you want to start downloading, and then the last episode (or you can choose to download the whole show).<br> You can also select the quality and download multiple anime at a time.<br><br>
Most importantly, you can choose whether you want to download them as a .torrent or if you only want to open them in your torrent client by using magnet links.<br><br>
During the process, logs will appear at the right of the GUI. You'll be able to save them as .txt file.<br>
Downloaded .torrent files will be sorted into their respective folders.<br><br>
It's really fast, even if the code can probably be improved (be indulgent, I'm still a beginner).<br>
Every downloaded torrent will be stored in a folder (names wil be the anime names) in the same folder as the script under the name `DownloadedTorrents`.<br><br>
By the way, Nyaa website won't think you're trying to DDoS it with a lot of requests, there is a short delay between each requets that avoids IP Blocking.<br><br>

<h1>📌 Requirements (only if you use the Python script)</h1>

You need to be on a Windows 10 machine, of course.<br>
You'll also need a BitTorrent client to open .torrent files and magnet links.<br><br>
With the command `pip install <library>` you'll need to install the following ones :
  
  • NyaaPy<br>
  • winotify<br>
  • requests<br>
  • PyQt5<br>
  
To install them in one command, just download the `requirements.txt` and `cd <path>` with the cmd to where the file is located. Then run the following command: `pip install -r requirements.txt` and it should be done! Python version: `3.9.1` but should works with any `3.0+` version.<br><br>
Then, run `main.pyw` and done!<br><br>

<h1>💻 "I don't have Python on my PC, what should I do?"</h1>
Don't worry mate, I created a .exe file which can be executed on any Windows 10 machine.<br>Just go <a href="https://github.com/marcpinet/batch-downloader-nyaa.si/releases" target=_blank>here</a> and download the latest version of NyaaDownloader by clicking on it (above `Source Code.zip`).<br><br>Carefully read the <b>Note</b> section if you've got any problem with it.<br><br>

<h1>⚙️ Work in progress</h1>

I will add more features when it will come to my mind.<br>
Feel free to contribute to this project by posting your suggestions in the <b>Issue</b> section.<br>
I constantly try to improve this little project.<br><br>


<h1>🐍 The script in action</h1>

This quick video shows you how the script works.<br><br>
<b>Funfact</b>: In the video, we can see that there is an issue while trying to download <i>Tokyo Revengers</i>. Well, it's fixed now and you'll see what episode couldn't be downloaded.
Automatically stops at 10 unsuccessful tries to avoid useless checking and spamming Nyaa website.



https://user-images.githubusercontent.com/52708150/131202882-9908a228-13fc-4b7b-a9bb-4700296454d0.mp4



