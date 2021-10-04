import pafy
import vlc # Windows requires VLC installed 64 bits
import time
import requests
import random
import api # Python file which return youtube api key
import os

#Command line tools
from PyInquirer import prompt
from examples import custom_style_2

#Junming Qiu
#Youtubeify - Command line Youtube audio player from URLs

#HOW TO USE
#Fill api_key
#fill songlist.txt with youtube links
#ctrl-c to pause

global api_key
api_key = api.get_api_key()

#Opens title file name and pulls random title art
def grab_title_art(titlefonts=None):
    if not titlefonts:    
        return "{==Welcome to Youtubify==}"

    with open(titlefonts, "r") as f:
        rand_title = random.randint(1, int(f.readline()))
        line = f.readline()
        count = 0
        while len(line) != 0 and count < rand_title:
            line = f.readline()
            if line[:2] == "~>":
                count += 1
                height = int(line.strip().split(" ")[1])
        
        ret_title = ""
       
        for i in range(height):
            ret_title += f.readline()

        f.close()
        return ret_title

#Simple song progress bar
def printProgressBar(iteration, total, prefix='', suffix='', decimals=1, length=100, fill='█', printEnd="\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    if iteration == total: 
        filledLength = int(length * iteration // total)
        bar = fill * filledLength + '-' * (length - filledLength)
        print(f"\r{prefix} |{bar}| {100}% {suffix}", end = printEnd)
        print()
    else:
        percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
        filledLength = int(length * iteration // total)
        bar = fill * filledLength + '-' * (length - filledLength)
        print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)
        
#Finds all titles of urls from playlist txt files
#show_url setting is for debug -> determining what url matches to each song
def update_song_directory(songs, show_url = False):
    name_url = []

    for song in songs:
        song_id = song.split("=")[1]
        new_url = f"https://www.googleapis.com/youtube/v3/videos?id={song_id}&part=snippet&key={api_key}"
        response = requests.get(new_url)
        json_thing = response.json()

        if show_url:
            name_url.append((json_thing["items"][0]["snippet"]["title"], song))
        else:
            name_url.append(json_thing["items"][0]["snippet"]["title"])

    return name_url
    
#Gets duration of video using API
def get_duration(song_id):
    new_url = f"https://www.googleapis.com/youtube/v3/videos?id={song_id}&part=contentDetails&key={api_key}"
    response = requests.get(new_url)
    json_thing = response.json()
    time = json_thing["items"][0]["contentDetails"]["duration"][2:]
    seconds = 0
    
    if "H" in time:
        seconds += 360 * int(time[:time.index("H")])
        time = time[time.index("H") + 1:]
    
    if "M" in time:
        seconds += 60 * int(time[:time.index("M")])
        time = time[time.index("M") + 1:]
    
    if "S" in time:
        seconds += int(time[:time.index("S")])
        
    return seconds

#Searches for videos and returns one which user chooses
def search_mode(max_results=10):
    print("Enter a search term:")
    search_q = input()
    new_url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&maxResults={max_results}&q={search_q}&type=video&key={api_key}"
    response = requests.get(new_url)
    json_thing = response.json()

    result_ids = []
    name_ids = []
    print("Results: ")
    for i in range(max_results):
        result_ids.append(json_thing["items"][i]["id"]["videoId"])
        name_ids.append(json_thing["items"][i]["snippet"]["title"])

    search_CLI = [
        {
            'type': 'list',
            'name': 'user_option',
            'message': 'Choose a Song: ',
            'choices': name_ids
        }
    ]

    answers = prompt(search_CLI, style=custom_style_2)
    answers_name = answers.get("user_option")
    choice = name_ids.index(answers_name)

    if 0 <= choice <= 10:
        return result_ids[choice], name_ids[choice]
    else:
        return None


#Main Program loop
def play(songs, shuffle:bool):
    STOP = False
    searched_song = None
    
    print(grab_title_art("titlefonts.txt"))
    print("Press 'ctrl-c' to pause and see controls")
    print("Press enter now to add all playlists")
    print("Type anything else and enter to add songs by search")

    if input() != "":
        songs = []

    print("Loading Playlists...\n")
    
    if not shuffle:
        song_directory = update_song_directory(songs)
    
    # Load playlist loop
    while not STOP:
        if shuffle:
            print("Shuffling Songs...\n")
            random.shuffle(songs)
            song_directory = update_song_directory(songs)

        curr_song_num = 0
        
        
        # Initialize song loop
        while curr_song_num < len(songs):
            os.system('cls' if os.name == 'nt' else 'clear')
            print(len(songs), "songs loaded")
            if searched_song == None:
                song = songs[curr_song_num]
                print()
                print(f"Now Playing #{curr_song_num}:", song_directory[curr_song_num], 50 * " ")
            
            else:
                song = f"https://www.youtube.com/watch?v={searched_song[0]}"
                print()
                print(f"Now Playing", searched_song[1], 50 * " ")
            
            searched_song = None
            
            url = song.strip()
            try:
                video = pafy.new(url)
            except KeyError:
                curr_song_num += 1
                break
            
            best = video.getbest()
            playurl = best.url
            playtime = get_duration(song.split("=")[1])

            Instance = vlc.Instance()
            player = Instance.media_player_new()
            Media = Instance.media_new(playurl, ':no-video')
            Media.get_mrl()
            player.set_media(Media)
            time.sleep(1)
            player.play()

            count = 0
            
            printProgressBar(0, playtime, prefix = ' Time', suffix = '', length = 50)

            # Play song loop
            while count < playtime:
                try:
                    time.sleep(1)
                    items = list(range(0, 57))
                
                    printProgressBar(count, playtime, prefix = ' Time', suffix = '', length = 50)
                    count += 1
                except KeyboardInterrupt:
                    player.pause()
                    print("h = help", " " * 100)
                    instr = input()
                    
                    if len(instr) == 0:
                        player.play()

                    #Play
                    elif instr == "p":
                        print()
                        player.play()
                    
                    #Skip Song
                    elif instr == "s":
                        print()
                        player.stop()
                        break

                    #Reload song
                    elif instr == "r":
                        print()
                        curr_song_num -= 1
                        player.stop()
                        break

                    elif instr == "rr":
                        print()
                        
                    
                    #Display Timestamp
                    elif instr == "l":
                        print(f"Currently Playing #{curr_song_num}:", song_directory[curr_song_num])
                        print("Current time:", count // 60, "m", count % 60, "s")
                        print("Total Length:", playtime // 60, "m", playtime % 60, "s\n")
                        player.play()
                        
                    #Show List of Songs -> Select Song
                    elif instr == "g":
                        
                        playlist_CLI = [
                            {
                                'type': 'list',
                                'name': 'user_option',
                                'message': 'Choose a Song: ',
                                'choices': song_directory
                            }
                        ]

                        answers = prompt(playlist_CLI, style=custom_style_2)
                        answer_name = answers.get("user_option")
                        new_song_num = song_directory.index(answer_name)

                        if 0 <= new_song_num < len(songs):
                            player.stop()
                            curr_song_num = new_song_num
                            curr_song_num -= 1
                            print()
                            break
                        else:
                            player.play()
                    
                    #Shuffle Songs
                    elif instr == "sh":
                        print("Shuffling Songs...\n")
                        random.shuffle(songs)
                        song_directory = update_song_directory(songs)
                        curr_song_num = -1
                        player.stop()
                        break
                    
                    #Increase volume by 10/+
                    elif instr[0] == "+":
                        player.audio_set_volume(player.audio_get_volume() + len(instr) * 10)
                        print("Current Volume:", player.audio_get_volume())
                        player.play()
                        
                    #Decrease volume by 10/-
                    elif instr[0] == "-":
                        player.audio_set_volume(player.audio_get_volume() - len(instr) * 10)
                        print("Current Volume:", player.audio_get_volume())
                        player.play()
                    
                    #Show commands
                    elif instr == "h":
                        print("Media Controls: l = remaining playtime, +/- = volume controls")
                        print("Song Controls: p = play, s = skip, r = reload, g = go to song")
                        print("App Controls: sh = shuffle, ed = edit playlists, exit = close app\n")
                        print("Search Controls: $p = search + play, $aq = search + add to queue")
                        player.play()
                    
                    #Enter Search Mode -> Select song || Add song to playlist
                    elif instr[0] == "$":
                        # $p = play now
                        # $aq = add song to queue
                        # $ap = add song to playlist
                        # $apq = add song to queue and playlist

                        searched_song = search_mode()
                        command = instr[1:]

                        if searched_song and len(command) > 0:
                            if command == "p":
                                player.stop()
                                break
                            elif command == "aq":
                                songs.append(f"https://www.youtube.com/watch?v={searched_song[0]}")
                                print(searched_song[0], searched_song[1])
                                song_directory.append(searched_song[1])
                                print(f"Song: {searched_song[1]} added to queue")
                                searched_song = None
                                player.play()
                                
                            elif command == "ap":
                                print(f"Song: {searched_song[1]} added to playlist{1}")
                                
                            elif command == "apq":
                                print(f"Song: {searched_song[1]} added to queue and to playlist{1}")
                                
                        else:
                            player.play()

                    #List and select playlist
                    elif instr == "pl":
                        pass

                    #Close Player
                    elif instr == "exit":
                        player.stop()
                        STOP = True
                        curr_song_num = len(songs)
                        print("Shutting Down")
                        break
                              
                    else:
                        player.play()
                        
            curr_song_num += 1
            player.release()
            
        if not STOP:  
            print("Reached End of Songs!\n")
            
  
def main():
    songs = []

    f = open("config.txt", "r")
    
    for line in f:
        if line[0] != "-":
            plist = open(line.strip(), "r")
            
            for song in plist:
                strip = song.strip()
                
                if len(strip) != 0:
                    songs.append(strip)
                    
    plist.close()
    f.close()
    
    play(songs, shuffle=False)
    
if __name__ == "__main__": 
    main() 

"""
Features:
play, pause, skip, shuffle, volume controls
goto song, playlist management (manual for now)
search song, show song timestamp, progress bar
"""

"""
WIP:
- Make downloadable mp3s
- Executable to run
- Procedural loading for playlists
- Reload playlists -> to edit playlist and add new song on the fly
- Fast forward, back
- Add albums by url
- Edit playlists
- Find by genre?
- Show next song
- Config file more options
- Generate sound from app
- More error catching
- Move functions into other package
- Song classification system
- Playlist classification system
"""
