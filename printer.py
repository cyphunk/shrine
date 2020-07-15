import threading
import cups
import time
import os
# This thread can also be instructed to 
# print new files that show up in a 
# certain directory
# Assumes printer named PRINTER already setup


def get_filepaths(directory, filetypes=['jpg','jpeg','png']):
    file_paths = []  # List which will store all of the full filepaths.
    # Walk the tree.
    for root, directories, files in os.walk(directory):
        for filename in files:
            for filetype in filetypes:
                # assume a '.'
                typelength = len(filetype)+1
                if filename[-typelength:] == '.'+filetype:
                    # Join the two strings in order to form the full filepath.
                    filepath = os.path.join(root, filename)
                    file_paths.append(filepath)  # Add it to the list.
    # sort by mtime
    file_paths.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    return file_paths  # Self-explanatory.

# Class to track number of prints so we can know when to replace print head
cwd = os.path.dirname(os.path.abspath(__file__))

counter_file = cwd+'/.print_counter.txt'

class Counter:
    def __init__(self,file):
        self.file = file
        if os.path.exists(self.file):
            with open(self.file, 'r') as f:
                try:
                    self.counter = int(f.read())
                except:
                    self.counter = 0
        else:
            self.counter = 0
    def get(self):
        return self.counter        
    def set(self, new_count):
        self.counter = int(new_count)
        self.write()
    def increment(self):
        self.set(self.counter+1)
    def write(self):
        with open(self.file, 'w') as f:
            f.write(str(self.counter))

class Printer(threading.Thread):
    def __init__(self, name=None, interval=2, auto_print_dir=None, auto_print=False,kwargs=None):
        threading.Thread.__init__(self)
        self._lp = cups.Connection()
        self.daemon = True
        self.counter = Counter(counter_file)
        self.name = name
        self.margin_enabled = True
        self._printer_option_key = "FeedDist"
        self._printer_option_margin = "4feed15mm"
        self._printer_option_nomargin = "0feed3mm"
        self.interval = interval
        self.auto_print_dir = auto_print_dir
        self.auto_print= auto_print
        self._kill = False
        self._lock = threading.Lock()
        # track last printed file to be sure to only print new
        self._monitor_last_printed_file = None
        self._warned_already = None
        # check if there is a file noting last printed file, useful for reset
        self._monitor_state_file = cwd+'/.monitor_last_printed_file.txt' 
        if os.path.exists(self._monitor_state_file):
            self.monitor_read_state()
        
    def set_interval(self,interval):
        with self._lock:
            self.interval = interval
    def margin_enable(self):
        self.margin_enabled = True
    def margin_disable(self):
        self.margin_enabled = False
    # def set_default(self):
    #     self.name = self._lp.getDefault()
    #     if self.name == None:
    #         printers = self._lp.getPrinters()
    #         self.name = list(printers.keys())[0]
    #     print("printer:",self.name)
    def busy(self):
        jobs = self._lp.getJobs()
        if len(jobs.keys()) > 0:
            return True
        else:
            return False
            

    def clear_counter(self):
        self.counter.set(0)
    def get_counter(self):
        return self.counter.get()
        
    def reset(self):
        # does not work
        #self._lp.cancelAllJobs()
        for job in self._lp.getJobs():
            lp.cancelJob(job)


    def status(self):
        busy = self.busy()
        count = self.get_counter()
        return f"Printer:\nName: {self.name}\nBusy: {busy}\nCount: {count}\nMonitor: {self.auto_print}\nMonitor dir: {self.auto_print_dir}\nMonitor previous printed file: {self._monitor_last_printed_file}"


    def auto_print_save_stage(self, latest):
        self._monitor_last_printed_file = latest
        with open(self._monitor_state_file, 'w') as f:
            f.write(
                self._monitor_last_printed_file)
    def monitor_read_state(self):
        with open(self._monitor_state_file, 'r') as f:
            self._monitor_last_printed_file = f.read()
        
        
    def kill(self):
        self._kill = True

    def print(self,file):
        # return printid or false
        if not self.busy():
            self.counter.increment()
            if self.margin_enabled:
                opt = {}
            else:
                opt = {self._printer_option_key: self._printer_option_nomargin}
            return self._lp.printFile(self.name, file, "print_title", opt)
        return False # busy
    def print_latest_file(self):
        files = get_filepaths(self.auto_print_dir)
        if len(files) <= 0:
            print("print latest:\nno files in\n",self.auto_print_dir)
            return False
        latest = files[0]
        if self.print(latest):
            print("print latest:\nprinted new file\n",latest)
            self.auto_print_save_stage(latest)
            return True # success
        else:
            print("print latest:\ntried to print file but printer busy?\n",latest)
            return False        
    def print_latest_file_if_new(self):
        files = get_filepaths(self.auto_print_dir)
        if len(files) <= 0:
            if self._warned_already != "no_files":
                print("print latest:\nno files in\n",self.auto_print_dir)
                self._warned_already = "no_files"
            return False
        latest = files[0]
        if latest == self._monitor_last_printed_file:
            # limit number of times we show this:
            if self._warned_already != "already_printed":
                print("print latest:\nfile already printed\n",latest)
                self._warned_already = "already_printed"
            return False # latest file already printed
        elif self.print(latest):
            print("print latest:\nprinted new file\n",latest)
            self.auto_print_save_stage(latest)
            self._warned_already = None
            return True # success
        else:
            if self._warned_already != "busy":
                print("print latest:\ntried to print file but printer busy?\n",latest)
                self._warned_already = "busy"
            return False
        
    def run(self):
        # This is the monitor_dir loop
        lastexec = 0
        while True:
            # kill called 
            if self._kill == True:
                break
            if self.auto_print == False:
                time.sleep(0.1)
                continue
            with self._lock:
                now = time.time()
                if now > lastexec + self.interval:
                    lastexec = now 
                    self.print_latest_file_if_new()
            time.sleep(0.1)
        print("run finished")

