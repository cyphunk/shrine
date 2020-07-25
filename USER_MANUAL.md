The "shrine" prints out instagram photos and can be configured for different printer types and various print styles.

# Start
Assuming shrine has been setup and worked once use these steps to pull it out of the box and get it started again.

These steps can be summarized as: 
- Setup "Petwo" wifi internet repeater  
  http://192.168.8.1
- Test "Petwo" network has internet (use phone)
- Connect printer to shrine
- Turn on shrine
- Configure shrine  
  http://lwa/admin

Detailed steps:

1.    Wifi: configure internet link on router
      1.  Power up Shrine Wifi Router  
      Plugin the small Shrine Wifi router to a seperate usb power source. Do not use the usb of raspberry pi.
      2.  Connect to "Petwo" wifi  
      Using your own workstation connect to the Shrine Wifi network "Petwo" with password written on device.
      3.  Access Router Admin interface: http://192.168.8.1  
      user: admin  
      password: the same as the wifi network password (writtein on device)
      4.  Connect router to internet abled wifi in house  
          - Go to ["Internet Settings (screenshot)"](./.readme_images/router-ui-1.png) through the globe icon   
          - Click ["New Connection"](./.readme_images/router-ui-2.png)  
          - Select ["Repeater"](./.readme_images/router-ui-3.png) and choose or enter SSID and password of the house Wifi
          - Notice ["Internet Settings"](.readme_images/router-ui-4.png) should after a minute show the connection settings
2.    Wifi: test that "Petwo" network has internet (use phone or laptop. Password written on router)
3.    Shrine: Connect printer  
      Connect printer before turning on shrine  
      There are 3 different printer types. Connect one connect to device. If you change printer you have to restart shrine.  
      NOTE: The two non-USB printers have connector cables that attach to the Raspberry Pi as shown in [image1](./.readme_images/printer-connector-1.jpg) and [image2](/.readme_images/printer-connector-2.jpg). Note that the Red Wire should be connect to the pin with the Red Tape.
4.    Power on shrine  
      After 20 seconds it should print test information.
      - If information looks like random characters or garbage text, it means the shrine was configured for a different printer type then previously used. You will have to skip to the configure step and change printer type, and then possibly restart shrine.
      - If it prints a status message [status message (photo)](./.readme_images/printer-startup-status.jpg) but the IP address is empty, this means the network is not ready. Wait 60 seconds and will continue to attemp to connect to the Petwo network and show the IP address when it succeeds. If it fails after 2 minutes then restart.
5.    Shrine: Configure - go to http://lwa/admin  
      At top is admin password location. The password is the same as used for connecting to wifi.
      1.  Configure Printer type  
      If when starting the shrine the printer prints out the status message then you can skip this step as the printer is already configured. If you see no printing or printing of garbage text then you should set the printer in the configuration.  
      If USB Printer connected you should not have to change any configuration. If *medium enclosed serial printer* is connected you need to be sure the "Serial baud rate" is set to 19200. If the *small exposed serial printer* is connected the baud should be 9600. Set the proper baud and restart shrine.
      1.  Configure Instagram hashtag

Additional:

6.    Shrine: See found images: http://lwa
7.    Shrine: Upload test image: http://lwa/upload  
      this option and be inabled or disabled in admin