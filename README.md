# bulk-download-from-nyaa.si

My first scrapper! It is focused on making simplier to bulk download torrents from Nyaa.si

<h1> How it Works </h1>
Everything is written into the script as a comment if you need some explainations. <br>
If you want to add a provider like Erai-Raws or SubsPlease etc., you'll need to edit the list in the script.
Since they are the only two uploaders that are mainly active and trusted by Nyaa.si, I decided to only put those two. Feel free to add any other uploader you trust.

You specify the anime name, the episode where you want to start downloading, and then the last episode. You can also select the quality and download multiple anime at a time.<br>
Most importantly, you can choose whether you want to download them as a .torrent or if you only want to open them in your torrent client by using magnet links.

It's really fast, even if the code isn't well-written, it works and it doesn't steal your creditentials.<br>
Every downloaded torrent will be stored in a dedicated folder in the same folder as the script under the name "DownloadedTorrents".

<h1> Requirements </h1>

With the command pip install <library> you'll need to install the following ones :
  
  • NyaaPy<br>
  • win10toast<br>
  • requests<br>
