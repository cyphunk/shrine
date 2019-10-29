# execute as thread (.start() which will call run()
# or just execute once with .get_latest_post()
import threading
import time
import instaloader
import json
import os 
import shutil
import subprocess
# we import a printer object just to check when printer is busy
import printer 

USER_AGENT="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.81 Safari/537.36"
DEFAULT_INTERVAL=5
cwd = os.path.dirname(os.path.abspath(__file__))
DATA_URI="dynamic_data"
DATA_PATH=cwd+"/"+DATA_URI
if not os.path.exists(DATA_PATH):
    os.mkdir(DATA_PATH)

class Instagram(threading.Thread):
    def __init__(self, hashtag=None, interval=DEFAULT_INTERVAL, user_agent=USER_AGENT, printer_name="PRINTER", kwargs=None):
        threading.Thread.__init__(self)
        self.daemon = True
        self.hashtag = hashtag
        self.interval = int(interval)
        self.data_path = DATA_PATH
        self.data_uri = DATA_URI
        self.paused = False
        self.printer_wait = False
        self.printer_name = printer_name
        self._lp = printer.Printer(name=self.printer_name)
        self._kill = False
        self._lock = threading.Lock()
        self._posts = None
        self._loader = instaloader.Instaloader(user_agent=user_agent,filename_pattern="{date_utc}_UTC_{mediaid}_{shortcode}", download_videos=False, compress_json=False, download_geotags=False, download_comments=False, dirname_pattern=self.data_path+"/{target}")
        # for geotags we get location error and supposedly this requires login https://github.com/instaloader/instaloader/issues/376
        
        #https://realpython.com/intro-to-python-threading/
        #https://stackoverflow.com/questions/44166443/how-to-change-argument-value-in-a-running-thread-in-python
        #https://www.python-course.eu/threads.php
    def get_latest_post(self):
        print("Downloading hashtag '%s'"%self.hashtag)
        try:
            self._posts = self._loader.get_hashtag_posts(self.hashtag)
        except:
            e = sys.exc_info()[0]
            print(e)
            pass
        # we only want the last (latest we hope?) so this loop will run once. but the return from get_hashtags is not a list but a generator class, so we have to:
        print("self._posts type",type(self._posts))
        
        for post in self._posts:
            downloaded = self._loader.download_post(post,self.hashtag)
            if downloaded:
                print("downloaded something")
                filename_without_extension = self._loader.format_filename(post)
                print(post,filename_without_extension,post.url,post.date)
                return post
            else:
                print("nothing new to download?")
                return False
    def kill(self):
        self._kill = True
    def clear_data_dir(self):
        print(f"clearing '{self.data_path}'")
        for root, dirs, files in os.walk(self.data_path):
            for f in files:
                print(f)
                os.unlink(os.path.join(root, f))
            for d in dirs:
                print(d)
                shutil.rmtree(os.path.join(root, d))
    def size_of_data_dir(self):
        return subprocess.check_output(['du','-sh', self.data_path]).split()[0].decode('utf-8')

    def run(self):
        lastexec = 0
        while True:
            if self._kill == True:
                break
            if self.paused == True:
                time.sleep(0.1)
                continue
            # print("wait",self.printer_wait,"busy",self._lp.busy())
            if self.printer_wait and self._lp.busy():
                time.sleep(0.1)
                continue                
            with self._lock:
                now = time.time()
                if now > lastexec + int(self.interval):
                    lastexec = now 
                    try:
                        self.get_latest_post()
                    except:
                        e = sys.exc_info()[0]
                        print(e)
                        pass
                        
            time.sleep(0.1)
        print("run finished")
