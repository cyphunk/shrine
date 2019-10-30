#!/usr/bin/python
# -*- coding: utf-8 -*-
# 
# Will run web server for admin and the instagram checker
#
# Run as root so can claim http port 80
#
import datetime, os, time

modified_date = datetime.datetime.fromtimestamp(os.stat(__file__).st_mtime).strftime("%Y%m%d")
VERSION = "1_%s"%modified_date

import web
#from web.wsgiserver import CherryPyWSGIServer
import subprocess
import re
import configparser
import shutil
import instagram
import printer

CWD = os.path.dirname(os.path.abspath(__file__))

insta = instagram.Instagram()
lp = printer.Printer()
logfile = "shrine.log"

configobj = configparser.ConfigParser()
configobj.read("server.ini")
config=configobj['shrine']
def config_write():
    with open("server.ini", 'w') as f:
        configobj.write(f)

ADMIN_PASSWORD = config.get('admin_password')
UPLOAD_ALLOWED = config.getboolean('upload_allowed')

insta.hashtag = config['instagram_hashtag']
insta.interval = int(config['instagram_interval'])
insta.paused = config.getboolean('instagram_paused')
insta.printer_wait = config.getboolean('instagram_printer_wait')
print("payused",insta.paused)
print("wait",insta.printer_wait)
print("busy",insta._lp.busy())
if not insta.paused:
    insta.start()
    
lp.name = config['printer_name']
lp.serial_baud = int(config['printer_serial_baud'] or 19200)
lp.interval = int(config['printer_interval'])
lp.margin_enabled = config.getboolean('printer_margin_enabled')
lp.auto_print = config.getboolean('printer_auto_print')
lp.auto_print_dir = insta.data_path
lp.start()

UPLOAD_URI = "uploaded_data"
# Put it inside of the instagram data directory
UPLOAD_PATH = insta.data_path+'/'+UPLOAD_URI

# LCDMEDIADIR         = CODE_BASE+"/lcd/media"
# LCDMEDIACONTROLFILE = CODE_BASE+"/lcd/lcd_media.txt"
# LCDMEDIATYPES       = ['png','jpeg','jpg','mov','mp4','gif']
# LCDDEFAULT          = 'blank.png'

# / shows the current image being printed and previous printed
# /admin to choose the hashtag, 
#           pause/start, 
#           print diagnostics, print test
#           set wireless information

urls = (
  "/admin",             "admin",
  "/showlog",           "showlog",
  "/upload",            "upload",
  "/",                  "index"
)

    
class admin:
    def POST(self):
        global UPLOAD_ALLOWED
        global insta
        
        args = web.input()
        if 'password' not in args or args.password != ADMIN_PASSWORD:
            raise web.unauthorized()
        if 'command' not in args:
            raise web.badrequest()
            
        print(f"command {args.command}")
        
        if args.command == 'instagram_start':
            insta.paused = False
            config['instagram_paused'] = "False"
            if not insta.is_alive():
                insta.start()        
        elif args.command == 'instagram_stop':
            insta.paused = True
            config['instagram_paused'] = "True"
        elif args.command == 'printer_wait_enable':
            insta.printer_wait = True
            config['instagram_printer_wait'] = "False"
        elif args.command == 'printer_wait_disable':
            insta.printer_wait = False
            config['instagram_printer_wait'] = "False"
        elif args.command == 'auto_print_allow':
            lp.auto_print = True
            config['printer_auto_print'] = "True"
        elif args.command == 'auto_print_disallow':
            lp.auto_print = True
            config['printer_auto_print'] = "False"
        elif args.command == 'printer_margin_enable':
            lp.margin_enabled = True
            config['printer_margin_enabled'] = "True"
        elif args.command == 'printer_margin_disable':
            lp.margin_enabled = False
            config['printer_margin_enabled'] = "False"
        elif args.command == 'printer_serial_baud_9600':
            if lp.serial_baud != 9600:
                # will reconfigure printers
                lp.serial_baud = 9600
                config['printer_serial_baud'] = "9600"
                config_write() #.ini read by start_printer.sh
                exec = subprocess.Popen("./start_printer.sh", shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
                output = exec.communicate()[0]
                print("printer setup",output)
        elif args.command == 'printer_serial_baud_19200':
            if lp.serial_baud != 19200:
                # will reconfigure printers
                lp.serial_baud = 19200
                config['printer_serial_baud'] = "19200"
                config_write() #.ini read by start_printer.sh
                exec = subprocess.Popen("./start_printer.sh", shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
                output = exec.communicate()[0]
                print("printer setup",output)

        elif args.command == 'upload_allow':
            UPLOAD_ALLOWED = True
            config['upload_allowed'] = "True"
            # Should we stop instagramer when we are using uploader?
            #insta.pause = True #not permanent
            #config['instagram_paused'] = "True"
        elif args.command == 'upload_disallow':
            UPLOAD_ALLOWED = False
            config['upload_allowed'] = "False"
        elif args.command == 'print_current':
            lp.print_latest_file()
        elif args.command == 'print_test':
            lp.print("./test.png")
        elif args.command == 'print_diagnostics':
            str = ""
            exec = subprocess.Popen("ip addr show dev eth0 | grep 'inet ' | awk '{print $2}'", shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
            output = exec.communicate()[0]
            str += "eth0: %s\n"%output
            exec = subprocess.Popen("ip addr show dev wlan0 | grep 'inet ' | awk '{print $2}'", shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
            output = exec.communicate()[0]
            str += "wlan0: %s\n"%output
            
            exec = subprocess.Popen("lpq", shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
            output = exec.communicate()[0]
            str += "%s\n"%output

            exec = subprocess.Popen("iwconfig | grep wlan0 | tr -s ' '", shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
            output = exec.communicate()[0]
            str += "wifi: %s\n"%output
            
            doprint = subprocess.Popen(f'echo -en "{str}" | lp -d PRINTER', shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
            output = doprint.communicate()[0]
            lp.counter.increment()
            print(output)
            
            

            
        elif args.command == 'set_instagram_hashtag':
            # always remove '#':
            if args.instagram_hashtag[0] == '#':
                args.instagram_hashtag = args.instagram_hashtag[1:]
            # Let thread have new hashtag
            insta.hashtag = args.instagram_hashtag
            # Write to config so that restart has this hashtag
            config['instagram_hashtag'] = args.instagram_hashtag            
        if args.command == 'set_instagram_interval':
            # Let thread have new hashtag
            insta.interval = int(args.instagram_interval)
            # Write to config so that restart has this interval
            config['instagram_interval'] = args.instagram_interval
            
        if args.command == 'clear_data':
            insta.clear_data_dir()

        # update any changed config values:
        config_write()
        thisurl = web.ctx.env.get('HTTP_REFERER', '/')
        raise web.seeother(thisurl)
        
    def GET(self):
        global UPLOAD_ALLOWED
        global insta

        print("sub hashtag", insta.hashtag)
        
        # get disk space in GB
        total, used, free = shutil.disk_usage(insta.data_path)
        SPACE_TOTAL = total // (2**30)
        SPACE_USED = used  // (2**30)
        SPACE_FREE = free // (2**30)
        data_size = insta.size_of_data_dir()

        return f"""<html><head><title>version: {VERSION}</title><meta charset="utf-8"></head><body>
        <style>
        * {{ font-size: 10pt; font-family: sans-serif, sans; }}
        _input, _button, select {{ font-size: 9pt; margin: 0px; padding: 0px; }}
        select {{ background-color: white; border: solid 1px #ccc; border-radius: 0; padding: 0 4; margin: 1 0; outline:0px;
                 -webkit-appearance: none; -moz-appearance: none; appearance: none; }}
        #debug {{opacity: 0.3;}}
        td {{ padding: 8px 18px; vertical-align: top; }}
        h2, h3 {{ margin: 14px 0px 4px 0px }}
        a {{ _text-decoration: none; color: inherit}}
        .help {{ font-size: 8pt }}
        .helptext {{ visibility: hidden;   position: absolute;
  z-index: 1;
  width: 200px;
  background-color: black;
  color: #fff;
  padding: 15px;
  border-radius: 6px;
  font-size: 10pt;
}}
        .help:hover .helptext {{ visibility: visible; }}
        </style>
        <script>
        window.onload = function () {{
            var password = window.localStorage.getItem('password')
            if (password)
                document.getElementsByName('password')[0].value = password;
        }}
        function save_password() {{ 
            var password = document.getElementsByName('password')[0].value;
            window.localStorage.setItem('password', password);
        }}
        </script>
        
    <table style="float:left;_border: solid black">
    <td valign=top bgcolor="#eee">
    <form method="POST">
        <table>
        <tr><td colspan=3><h2>Settings</h2></td></tr>
        <tr><td>admin password</td><td><input type=password name=password onchange=save_password()></td><td></td></tr>
        
        <tr><td colspan=3><h3>Instagram</h2></td></tr>
        <tr><td>started: <b>{insta.is_alive() and not insta.paused}</b>
        <span class=help>(help)<span class=helptext>Start to enable downloading new images for "hashtag" at every "interval" of seconds. Current list of downloaded images can be found at the <a href=/ target=_blank>index page</a>. If auto-printing is enabled then they will also be printed. </span></span>
        </td><td colspan=2><button name=command value=instagram_start>start</button>
                    <button name=command value=instagram_stop>stop</button>
        </td></tr>
        <tr><td>Wait for printer: <b>{insta.printer_wait}</b>
        <span class=help>(help)<span class=helptext>When set to true, new images will not be downloaded while printer is busy printing</span></span>
        </td><td colspan=2><button name=command value=printer_wait_enable>wait</button>
                    <button name=command value=printer_wait_disable>do not wait</button>
        </td></tr>
        <tr><td>hashtag</td>
            <td><input type=input name=instagram_hashtag value=\"{insta.hashtag}\"></td>
            <td><button name=command value=set_instagram_hashtag>set</button></td>
        </tr>
        <tr><td>interval</td>
            <td><input type=input name=instagram_interval value=\"{insta.interval}\"></td>
            <td><button name=command value=set_instagram_interval>set</button></td>
        </tr>

        <tr><td colspan=3><h3>Printer</h2></td></tr>
        <tr><td>Auto-print: <b>{lp.auto_print}</b>
        <span class=help>(help)<span class=helptext>Auto-print new instagram images for "hashtag" when they are downloaded.</span></span>
        </td><td colspan=2><button name=command value=auto_print_allow>enable</button>
        <button name=command value=auto_print_disallow>disable</button></td></tr>
        <tr><td>Printer margin: <b>{lp.margin_enabled}</b>
        <span class=help>(help)<span class=helptext>when enabled a margin will be added after each print.</span></span>
        </td><td colspan=2><button name=command value=printer_margin_enable>enable</button>
        <button name=command value=printer_margin_disable>disable</button></td></tr>
        <tr><td>Serial baud: <b>{lp.serial_baud}</b>
        <span class=help>(help)<span class=helptext>9600 is for the exposed serial printer and 19200 is for the encased serial printer. The USB printer when connected will override all of these.</span></span>
        </td><td colspan=2><button name=command value=printer_serial_baud_9600>9600 (exposed printer)</button><br>
        <button name=command value=printer_serial_baud_19200>19200 (enclosed printer)</button></td></tr>
        <tr><td>Print current image <span class=help>(help)<span class=helptext>Print the latest image found from the downloaded instagram images. See the current list of images on the <a href=/ target=_blank>index page</a></span></span></td><td colspan=2><button name=command value=print_current>print current</button></tr>
        
        <tr><td>Print <a href=test.png target=_blank>test</a> image now</td><td colspan=2><button name=command value=print_test>print test.png</button></tr>
        
        <tr><td>Print diagnostic info</td><td colspan=2><button name=command value=print_diagnostics>print diagnostics</button></tr>
        
        <tr><td colspan=3><h3>Other</h2></td></tr>
        <tr><td><a href=/upload target=_blank>/upload</a> allowed: <b>{UPLOAD_ALLOWED}</b> <span class=help>(help)<span class=helptext>If enalbed anyone can upload an image which will be printed by going to the <a href=/upload target=_blank>/upload url</a>. </span></span>
        </td><td colspan=2><button name=command value=upload_allow>allow</button>
        <button name=command value=upload_disallow>disallow</button></td></tr>
        
        
        <tr><td>clear up disk space:</td><td><button name=command value=clear_data>clear instagram data</button></td></tr>
        <tr><td><a href=/showlog target=_blank>show log</a></td></tr>
        </table>

    </form>
    </td>
    </table>
    
    <table style="_border: solid #eee">
    <td valign=bottom>
        <table>
        <tr><td colspan=2><h2>Status</h2></td></tr>
        <tr><td>Instagram&nbsp;running</td><td><b>{insta.is_alive() and not insta.paused}</b></td></tr>
        <tr><td>Instagram&nbsp;wait for printer</td><td><b>{insta.printer_wait}</b></td></tr>
        <tr><td>Instagram&nbsp;hashtag</td><td><b><a href='https://www.instagram.com/explore/tags/{insta.hashtag}' target=_blank>{insta.hashtag}</a></b></td></tr>
        <tr><td>Instagram interval</td><td><b>{insta.interval}</b></td></tr>
        <tr><td>Instagram interval</td><td><b>{insta.interval}</b></td></tr>
        <tr><td>Instagram&nbsp;limits</td><td>Read up on <a href=https://developers.facebook.com/docs/instagram-api/overview/#rate-limiting>instagram rate limits</a></td></tr>
        <tr><td>Printer auto print</td><td><b>{lp.auto_print}</b></td></tr>
        <tr><td>Printer margin</td><td><b>{lp.margin_enabled}</b></td></tr>
        <tr><td>Printer serial baud</td><td><b>{lp.serial_baud}</b></td></tr>
        <tr><td>Allow /upload</td><td><b>{UPLOAD_ALLOWED}</b></td></tr>
        <tr><td valign=top>Disk space:</td><td>Total: {SPACE_TOTAL} GB<br>Used: {SPACE_USED} GB<br>Free: <b>{SPACE_FREE} GB</b> </b></td></tr>
        <tr><td valign=top>Instagram/Upload space:</td><td><b>{data_size}</b></td></tr>
        <tr><td>Version:</td><td> {VERSION}</td></tr>
        </table>
        </td>

        </table>
    </td>

    </table>
    <pre id=debug></pre>
        </html>
        """
    

def debug(message):
    if not DEBUG:
        return
    print (message)





def get_filepaths(directory, filetypes=['jpg','jpeg','png']):
    file_paths = []  # List which will store all of the full filepaths.
    # Walk the tree.
    for root, directories, files in os.walk(directory):
        for filename in files:
            for filetype in filetypes:
                # assume a '.'
                typelength = len(filetype)+1
                if filename[-typelength:].lower() == '.'+filetype:
                    # Join the two strings in order to form the full filepath.
                    filepath = os.path.join(root, filename)
                    file_paths.append(filepath)  # Add it to the list.
    # sort by mtime
    file_paths.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    return file_paths  # Self-explanatory.

# Ignore this. Instead we use buit in /static
# http://webpy.org/cookbook/staticfiles
# mkdir static; cd static; ln -s ../instagram_data .
# class image:
#     def GET(self, file=None):
#         # Static files (style sheets, index.html)
#         print("get file",file)
#         if file:
#             with open(insta.data_path+'/'+file, 'r') as f:
#                 return f.read()

class showlog:
    def GET(self):
        # tac reverses:
        p = subprocess.Popen("tail -1000 '%s' | tac"%logfile,shell=True, stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        output = p.communicate()[0]
        return output

class upload:
    def GET(self):
        if not UPLOAD_ALLOWED:
            return """<html>
            <head>
            <style>
            * { font-size:14pt; font-family: sans-serif, sans;}
            </style>
            </head>
            <body>Upload disabled</body></html>
            """
        return f"""   
        <html><head>
        <style>
        * {{ font-size: 18pt; font-family: sans-serif, sans; }}
        body {{ margin-left: 18px; margin-top: 18px;}}
        button, input {{ 
            font-size: inherit; 
            margin-bottom: 18px;
            }}
        </style>
        </head>
        <body><center>
        <table><td>
        <form method="POST" enctype="multipart/form-data" action="/upload">
        <input type="file" name="newfile" /><br>
        <input type="submit" value="Upload"/>
        </form>
        </table></td>
        </body></html>"""

    def POST(self):
        if not UPLOAD_ALLOWED:
            return """<html>
            <head><meta _http-equiv="refresh" content="5">
            <style>
            * { font-size:14pt; font-family: sans-serif, sans;}
            </style>
            </head>
            <body>Upload disabled</body></html>
            """
        x = web.input(newfile={},delete=[])
        # newfile should have type <type 'instance'> if it is not empty
        if 'newfile' in x and type(x.newfile) != dict: # to check if the file-object is created
            if not os.path.exists(UPLOAD_PATH):
                os.mkdir(UPLOAD_PATH)
            print("dir",dir(x.newfile))
            print(x.newfile.file)
            print(x.newfile.type)
            print(x.newfile.filename)
            print(x.newfile.name)
            filepath=x.newfile.filename.replace('\\','/') # replaces the windows-style slashes with linux ones.
            filename=filepath.split('/')[-1] # splits the and chooses the last part (the filename with extension)
            fout = open(UPLOAD_PATH +'/'+ filename,'wb') # creates the file where the uploaded file should be stored
            fout.write(x.newfile.file.read()) # writes the uploaded file to the newly created file.
            fout.close() # closes the file, upload complete.
            raise web.seeother('/')
        else:
            return "error with upload"

class index:
    def GET(self, file=None):
        # Static files (style sheets, index.html)
        if file:
            #print "have file", file
            f = open('static/'+file, 'r')
            return f.read()

        if UPLOAD_ALLOWED:
            refresh = ""
            upload_html = """
            <style>*, td, input, button { font-size: 18pt; font-family: sans-serif, sans; }</style><table style=""><td><form method="POST" enctype="multipart/form-data" action="/upload">
            <input type="file" name="newfile" /><br>
            <input type="submit" value="Upload"/>
            </form></table></td>"""
        else:
            refresh = "<head><meta http-equiv=refresh content=5></head>"
            upload_html=""
            
        data_path = insta.data_path
        data_uri = insta.data_uri
        file_list = get_filepaths(data_path)
        # print("file_list",file_list,data_path)
        file_html = ""
        for f in file_list[:20]:
            f = f.replace(data_path,data_uri)
            file_html += f'<a href="/static/{f}"><img src="/static/{f}" height=80%></a><br>\n'
            # file_html += f'<a href="/static/{f}">{f}</a><br>\n'

        web.header('Cache-control', 'no-cache, no-store, must-revalidate')
        web.header('Pragma', 'no-cache')
        #web.header('Expires', '0')
        #web.header('Cache-Control', 'post-check=0, pre-check=0', False)
        return f"""<html>{refresh}<center>{upload_html}{file_html}""" 


try:
    from html import escape  # python 3.x
except ImportError:
    from cgi import escape  # python 2.x

# First arg on cmdline would be port
#app = web.application(urls, globals())
# Do this to set port in code
class myApp(web.application):
    def run(self, port=80, *middleware):
        func = self.wsgifunc(*middleware)
        return web.httpserver.runsimple(func, ('0.0.0.0', port))

app = myApp(urls, globals(), autoreload=False)

if __name__ == "__main__":
    if os.geteuid() != 0:
        print("PORT 8000 (not run as root")
        app.run(port=8000)
    else:
        app.run()
