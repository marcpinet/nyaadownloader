[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://GitHub.com/Naereen/StrapDown.js/graphs/commit-activity) [![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/) [![Windows](https://svgshare.com/i/ZhY.svg)](https://svgshare.com/i/ZhY.svg) [![Ask Me Anything !](https://img.shields.io/badge/Ask%20me-anything-1abc9c.svg)](https://GitHub.com/Naereen/ama)

# NyaaDownloader

🚀 Download many .torrent from Nyaa.si at a time! 🚀

🔌 Instantly transfer them into your Bittorrent client 🔌

🔎 Automatically search the closest title to ensure an accurate result 🔎

📦 Exists as an all-in-one executable file, so you can skip the prerequisites 📦

🧾 ... and many more features! 🧾

## Features

* Integrated Graphical User Interface (GUI) 🖥
* Enter uploaders name (defaults are [Erai-raws](https://www.erai-raws.info/) and [Subsplease](https://subsplease.org/)) 🤖
* Enter the anime title you want to download ✏️
* Choose the quality 🎞
* Retreive them either as .torrent or directly transfer them into your Bittorrent client ⚙️
* Logging system (you can save them into a text file) 📝
* Downloaded anime are sorted and stored into their respective folders 📁
* Get warned whether the anime title you entered exists in Nyaa database or not ⚠️

## Demo

https://user-images.githubusercontent.com/52708150/131512813-20f10705-0d71-4a09-9c3d-1af3983a666b.mp4

## Getting Started

This script is being controlled through a user interface. 
For beginners, that is why the main is a `.pyw` rather than a `.py` one.

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Support 👨‍💻

Any problems with running the script and any questions please create a new issue [here](https://github.com/marcpinet/batch-downloader-nyaa.si/issues/new?assignees=&labels=&template=bug_report.md&title=).

You can also contribute to this project by requesting new features [here](https://github.com/marcpinet/batch-downloader-nyaa.si/issues/new?assignees=&labels=&template=feature_request.md&title=).

I never ask for money for my open source projects. However, you can still tip me if you want.
I am a [Brave Verified Creator](https://i.imgur.com/fOUfdM5.png)!

### How to use without Python installed

I made an executable file of this project using [pyinstaller](https://github.com/pyinstaller/pyinstaller).
You can find the latest release [here](https://github.com/marcpinet/batch-downloader-nyaa.si/releases/latest).

### Prerequisites

* Python 3.9+ (3.0+ might work)

#### Before we get started

You will need to have a web browser that supports magnet link and also a bittorrent client.

Get a copy of the Project. Assuming you have git installed, open your Terminal and enter:

```bash
git clone 'https://github.com/marcpinet/batch-downloader-nyaa.si.git'
```

To install all needed requirements run the following command in the project directory:

```bash
pip install -r requirements.txt
```

## Running 🏃

To run this script open your Terminal in the project directory.

To start the script, enter:

```bash
pythonw main.pyw
```

You can then close the Terminal.

## Tips and tricks

If you failed many times checking for an anime you like, you can try to find his full translated name from [MyAnimeList](https://myanimelist.net) as shown below.

https://user-images.githubusercontent.com/52708150/230735983-0f5f0d1b-fd01-42c4-9934-3700ce6abe23.mp4

If you still didn't find what you were looking for, you can try to search some "keywords" of its title and find how uploaders you like name their uploads.

As an example, you might know *[JoJo's Bizarre Adventure: Golden Wind](https://myanimelist.net/anime/37991/JoJo_no_Kimyou_na_Bouken_Part_5__Ougon_no_Kaze?q=jojo&cat=anime)*, but its japanese title is *JoJo no Kimyou na Bouken Part 5: Ougon no Kaze*.

However, they don't always name them like that. For instance, it can be named *JoJo no Kimyou na Bouken - Ougon no Kaze* (without the "**Part 5:**" which can influence the search), so you'll need to check by yourself if the above trick failed.

## Authors

* **Marc Pinet** - *Initial work* - [marcpinet](https://github.com/marcpinet)

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* Hat tip to anyone whose code was used

## To Do List 📝

You can find what I plan to do for the project [here](https://github.com/marcpinet/batch-downloader-nyaa.si/projects).
Also, you can find what I already implemented [here](https://github.com/marcpinet/batch-downloader-nyaa.si/projects?query=is%3Aclosed).



