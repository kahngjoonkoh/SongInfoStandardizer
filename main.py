import os, time, requests

import tkinter as tk
from tkinter.filedialog import askdirectory

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

from multiprocessing import Pool


def main():

    # Gets songs folder directory and scans it
    root = tk.Tk()
    root.withdraw()
    base_dir = askdirectory()
    try:
        params_list = scan_dir(base_dir)
    except Exception as e:
        print(e)
        press_enter_to_exit()
    # If there are no files that should be renamed, the program exits.
    if len(params_list) == 0:
        exit()

    # Multithreading
    p = Pool(20)
    p.map(task, params_list)
    p.terminate()
    p.join()

    press_enter_to_exit()


"""
Parses the filename.
Retrieves the harmonic info of the song from Tunebat.com.
Renames the original file.
"""
def task(params: list) -> None:
    filename, base_dir = params
    artist, song_name, ext = parse_filename(filename)
    key, bpm = retrieve_harmonic_info(artist, song_name)

    # Validating for connection failure
    if key == None or bpm == None:
        print(f"Unable to fetch key/bpm for '{song_name}'")
        return

    # Validating for web scraping issues
    try:
        int(bpm)
    except Exception as e:
        print(f"Unable to fetch key/bpm for '{song_name}'")
        return

    os.rename(f"{base_dir}/{filename}", f"{base_dir}/{key} - {bpm} - {artist} - {song_name}.{ext}")
    print(f"Renamed '{song_name}' Successfully")

"""
Gets a string directory as input.
Returns filenames that have an extension of .mp3 or .wav
and if the filename is not standardized yet.
"""
def scan_dir(base_dir: str) -> list:
    l = []
    for filepath in os.listdir(base_dir):
        fn = filepath.split("/")[-1]
        if (fn.endswith(".mp3") or fn.endswith(".wav")) and fn.count(" - ") <= 2:
            l.append([fn, base_dir])
    return l


"""
Gets a string filename as input and parses it to return 
a tuple of artist, song_name, and file extension.
Returns None when filename is determined to standardized
already.
"""
def parse_filename(fn: str) -> str:
    ext = fn.split(".")[-1]
    temp = fn.rsplit(".", 1)[0].split(" - ", 1)
    artist = temp[0]
    song_name = temp[1]
    return artist, song_name, ext


"""
Uses selenium to open the search url and retrieve all text on the website. 
The text is indexed so that it would only give the key and bpm of the audio file.
"""
def retrieve_harmonic_info(artist: str, song_name: str) -> str:
    url = f"https://tunebat.com/Search?q={artist} {song_name}".replace(" ", "%20")
    option_headless = webdriver.ChromeOptions()
    option_headless.add_argument("--disable-gpu")
    option_headless.add_argument("--disable-extensions")
    option_headless.add_argument("--start-maximized")
    option_headless.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")
    option_headless.add_argument("--headless")
    option_headless.add_argument("no-sandbox")
    option_headless.add_argument('--log-level=1')

    driver = webdriver.Chrome(options=option_headless)
    driver.get(url)


    try:
        print(f"Connecting -> {url}")
        WebDriverWait(driver, 60).until(EC.title_contains("Tunebat"))
        # Removes ads that might interfere.
        all_iframes = driver.find_elements(by=By.TAG_NAME, value="iframe")
        custom_ad_frames = driver.find_elements(by=By.CLASS_NAME, value="pa-unit-global")
        if len(all_iframes) > 0:
            driver.execute_script("""
                var elems = document.getElementsByTagName("iframe");
                for(var i = 0, max = elems.length; i < max; i++)
                     {
                         elems[i].hidden=true;
                     }
                                  """)

        if len(custom_ad_frames) > 0:
            driver.execute_script("""
                    var elems = document.getElementsByClassName("pa-unit-global");
                    for(var i = 0, max = elems.length; i < max; i++)
                         {
                             elems[i].hidden=true;
                         }
                                      """)
        print(f"Connected  -> {url}")

    except Exception as e:
        print(e)
        return None, None

    content = driver.find_element(by=By.XPATH, value="/html/body").text
    driver.quit()

    # Gets the harmonic info of the first item in the search result.
    harmonic_info = content.split("\n")[17:25]
    # Key and BPM respectively.
    return harmonic_info[2], harmonic_info[4]

def press_enter_to_exit():
    input("\nPress enter to exit")
    exit()

if __name__ == "__main__":
    base_dir = "."
    main()
