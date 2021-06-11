# bulk-download-from-nyaa.si

My first scrapper! It is focused on making easier to bulk download torrents/transfer magnets from Nyaa.si

<h1> How it Works </h1>
Everything is written into the script as a comment if you need some explainations. <br>
If you want to add a provider like <b>Erai-Raws</b> or <b>SubsPlease</b> etc., you'll need to edit the list in the script.
Since they are the only two uploaders that are mainly active and trusted by Nyaa.si, I decided to only put those two. Feel free to add any other uploader you trust.<br><br>

You specify the anime name, the episode where you want to start downloading, and then the last episode. You can also select the quality and download multiple anime at a time.<br><br>
Most importantly, you can choose whether you want to download them as a .torrent or if you only want to open them in your torrent client by using magnet links.

It's really fast, even if the code isn't well-written, it works and it doesn't steal your creditentials.<br>
Every downloaded torrent will be stored in a dedicated folder in the same folder as the script under the name "DownloadedTorrents".

<h1>Requirements (only if you use the Python script)</h1>

With the command pip install <library> you'll need to install the following ones :
  
  • NyaaPy<br>
  • win10toast<br>
  • requests<br>
  
To install them in one command, just download the `requirements.txt` and `cd <path>` with the cmd to where the file is located. Then run the following command: `pip install -r requirements.txt` and it should be done!
<h1>Important Note for the binary (.exe) from the release</h1>
win10toast doesn't work at all with PyToExe so you won't receive any Windows 10 notification when a download/transfer has been successfully completed. Instead, it will only prints in the console. If you still want these type of notification, you may use the Python Script from the source code since this binary can't do it.

  
  <h1> WORK IN PROGRESS </h1>

I will probably make the code smoother and more readable. Once I learn classes in Python, I will try to turn it into an OOP Project.
The goal is to make a working GUI for the program.
If you have any suggestion, let me know!
