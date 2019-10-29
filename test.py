import instagram
insta = instagram.Instagram()
insta.hashtag="foodporn"
insta.interval=10
insta.printer_name="PRINTER"
insta.printer_wait=True
import printer
lp = printer.Printer()
lp.name="PRINTER"
lp.auto_print_dir = insta.data_path
lp.auto_print=True
insta.start()
lp.start()
import time
while True:
    time.sleep(1)
    print("busy",lp.busy())