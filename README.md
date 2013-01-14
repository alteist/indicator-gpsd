indicator-gpsd v0.0.2
==============

GPSd application indicator for Unity. Toggles data acquiring from GPSd, shows GPS data, manages GPS device power (only GOBI3000 currently).

Written and tested only on Ubuntu 12.10 (unity 6.8-6.12, gpsd 3.6).

##Disclaimer##
This is my first experience in writing code using GTK, Unity, GIT, GitHub and gpsd. Had only known Python and invested 8 hours to make first version.

##Features:##
- Ubuntu Unity integration
- One-click GPS toggle
- Live display of GPS data from gpsd via network socket (localhost by default)
- Open Google/Yandex/OpenStreet map in default browser at current location
- Has to be (no tests done yet) energy-efficient:
    - UI is updated only on new location data arrival from gpsd
    - gpsd manages active state of most GPS devices automatically, and this applet may add power management for some others through custom shell commands

##TODO:##
- Handle gpsdata elegantly
- Add "Copy GPS data to clipboard" menu item
- Tidy up code, menus and errors
- Add configuration GUI
- "Autostart with system" option
- Redraw icons
- Write dpkg stuff and make .debs for easy installation
- Settle PPA
- i18n

##gpsd and python-gps required:##
1. 
        sudo apt-get install gpsd python-gps
2. 
        sudo dpkg-reconfigure gpsd
3. 
        sudo service gpsd restart

##Download and run indicator:##
1. 
        git clone https://github.com/alteist/indicator-gpsd.git
2. 
        python path/to/indicator-gpsd.py

##Power toggle for Sierra Wireless MC8355 - Gobi 3000(TM) Module GPS (USB 1199:9013)##
1. Add yourself to dialout group:
sudo adduser USERNAME dialout
2. Restart X-session or reboot.

###Troubleshoot Gobi 3000 power toggle###
1. If you didn't add yourself to dialout group:

        sudo su -

2. 
    echo "\$GPS_START" > /dev/ttyUSB2
3. 
        cat /dev/ttyUSB2
4. if you see something like:

        GPGSV,3,1,12,03,47,085,29,05,06,323,22,06,34,063,27,07,58,309,31
then this applet will have power control over GOBI3000 GPS.
Press **CTRL+C** to stop stream from ttyUSB.

5. 
    echo "\$GPS_STOP" > /dev/ttyUSB2

###Note###
I think gpsd has to manage power state of the GPS device itself,  if someone wants to send patches to the author
here is the clue for Sierra Wireless MC8355 - Gobi 3000(TM) Module:

    lsusb:
    Bus 002 Device 003: ID 1199:9013 Sierra Wireless, Inc.
turn on:

    echo "\$GPS_START" > /dev/ttyUSB2
turn off:

    echo "\$GPS_STOP" > /dev/ttyUSB2

gpsd docs: http://catb.org/gpsd/gpsd_json.html

##Options:##
**GPS_OFF_TIMEOUT = 65000**
When you close connection to gpsd, it still reads data from GPS device for some time (I think it's 60 seconds)
and I haven't found a way to stop it immediately to turn off power of the GOBI3000 GPS
and the device cannot be turned off if someone uses it
so I added this timeout (65 seconds in ms)

**GPS_DEV = "/dev/ttyUSB2"**
Used only for power management in this indicator

**GPS_ON_COMMAND = "path|cmd"
GPS_OFF_COMMAND = "path|cmd"**
Not implemented yet.

**GPSD_HOST = "127.0.0.1"
GPSD_PORT = 2947**
Cat /etc/default/gpsd to check if there are non-default settings

##Debug indicator <--> gpsd part:##
Run in separate terminals:
    sudo gpsd -N -D 5 /dev/ttyUSB2
    sudo ngrep -d lo port 2947