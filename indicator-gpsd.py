#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# GPS applet for Unity with Sierra Wireless MC8355 - Gobi 3000(TM) Module GPS power toggle
# reads gpsd default tcp\ip socket at 127.0.0.1:2947
# before using this applet please make sure GPS module is installed and run:
# apt-get install gpsd
# dpkg-reconfigure gpsd
# then add yourself into dialout group (maybe you'll need to reboot):
# sudo adduser USERNAME dialout
#
# gpsd docs: http://catb.org/gpsd/gpsd_json.html
import time

__author__ = 'Roman Rakul <alteist@gmail.com>'
__license__ = 'BSD'
__version__ = '0.0.1'
# BSD terms apply: see the file COPYING in the distribution root for details.

# you can check if GPS_DEV is right by executing:
# sudo su -
# echo "\$GPS_START" > /dev/ttyUSB2
# cat /dev/ttyUSB2
# if you see something like:
# GPGSV,3,1,12,03,47,085,29,05,06,323,22,06,34,063,27,07,58,309,31
# then this applet will have power control over GOBI3000 GPS
# press CTRL+C to stop stream from ttyUSB
GPS_DEV = "/dev/ttyUSB2"

# when you close connection to gpsd, it still reads data from GPS device for some time (I think it's 60 seconds)
# and I didn't find a way to stop it immediately to turn off power of the GOBI3000 GPS
# and the device cannot be turned off if someone uses it
# so I added this timeout (65 seconds in ms)
GPS_OFF_TIMEOUT = 65000
# Note: I think gpsd has to manage power state of the GPS device itself,  if someone wants to send patches to the author
# here is the clue for Sierra Wireless MC8355 - Gobi 3000(TM) Module:
# lsusb:
# Bus 002 Device 003: ID 1199:9013 Sierra Wireless, Inc.
# turn on:
# echo "\$GPS_START" > /dev/ttyUSB2
# turn off:
# echo "\$GPS_STOP" > /dev/ttyUSB2

# cat /etc/default/gpsd to check these if there are non-default settings for these:
GPSD_HOST = "127.0.0.1"
GPSD_PORT = 2947

import os
import gobject
import gtk
import appindicator
import sys
import gps
from socket import error as SocketError

class GPS(appindicator.Indicator):
    # If GPS enabled on indicator start, also used to store current state
    __gps_on = False
    __gps_off_timeout_handler = None
    __gps_disable_stage2_timeout_handler = None
    __gpsd_daemon_handler = None
    __w1 = 0
    __w2 = 0
    __w3 = 0

    # Entry point
    def __init__(self):
        appindicator.Indicator.__init__(self,
            "indicator-gps",
            "/home/stinger/gps-off.png",
            appindicator.CATEGORY_HARDWARE)
        self.set_status(appindicator.STATUS_ACTIVE)
        self.set_attention_icon ("/home/stinger/gps-on.png",)
        self.redraw_ui()

    # open Google maps in default browser
    def gmaps(self, menuitem, select, gpsdata):
        latlon = "%s,%s" % (gpsdata.lat,gpsdata.lon)
        os.system('x-www-browser "http://maps.google.com/maps?ll=%s&q=%s"' % (latlon,latlon))

    # open Yandex maps in default browser
    def ymaps(self, menuitem, select, gpsdata):
        lonlat = "%s,%s" % (gpsdata.lon,gpsdata.lat)
        os.system('x-www-browser "http://maps.yandex.ru/?ll=%s&q=%s&z=13&l=map"' % (lonlat,lonlat))

    # "Quit" button action
    def quit(self, widget):
        sys.exit(0)

    # Called each time new GPS data is available from gpsd, after any user action and on indicator init
    def redraw_ui(self, gpsdata=None):
        self.menu = gtk.Menu()

        if self.__gps_on:
            # if disable is safe
            if not self.__gps_disable_stage2_timeout_handler:
                # Disable
                self.gpsDisable = gtk.MenuItem("Disable GPS")
                self.menu.append(self.gpsDisable)
                self.gpsDisable.connect("activate", self.gps_disable)

                # ---
                self.menu.append(gtk.SeparatorMenuItem())

            if gpsdata.mode < 2:
                # State
                self.gpsState = gtk.MenuItem("GPS On (no fix)")
                self.menu.prepend(self.gpsState)

                self.menu.append( gtk.MenuItem("Waiting for GPS data from gpsd...") )
            else:
                # State
                self.gpsState = gtk.MenuItem("GPS On (%sD fix)" % gpsdata.mode)
                self.menu.prepend(self.gpsState)

                # GPS data live
                # TODO: make error estimations for all data optional
                # for now, GPS can be already fixed by small amount of sats, but applet will not show it until there is epy

                # Latitude
                if hasattr(gpsdata, 'lat') and hasattr(gpsdata, 'epy'):
                    self.menu.append( gtk.MenuItem("Latitude: %s° (±%sm)" % (gpsdata.lat,gpsdata.epy)) )

                # Longtitude
                if hasattr(gpsdata, 'lon') and hasattr(gpsdata, 'epx'):
                    self.menu.append( gtk.MenuItem("Longtitude: %s° (±%sm)" % (gpsdata.lon,gpsdata.epx)) )

#                # Altitude
#                if hasattr(gpsdata, 'epv'):
#                    self.menu.append( gtk.MenuItem("Altitude: %sm (±%sm)" % (gpsdata.alt,gpsdata.epv)) )
#
#                # Azimuth
#                if hasattr(gpsdata, 'epd'):
#                    self.menu.append( gtk.MenuItem("Azimuth: %s° (±%s)" % (gpsdata.track,gpsdata.epd)) )
#                else:
#                    self.menu.append( gtk.MenuItem("Azimuth: %s°" % gpsdata.track) )
#
#                # XY-Speed
#                if hasattr(gpsdata, 'eps'):
#                    self.menu.append( gtk.MenuItem("XY-Speed: %sm/s (±%sm/s)" % (gpsdata.speed,gpsdata.eps)) )
#                else:
#                    self.menu.append( gtk.MenuItem("XY-Speed: %sm/s" % gpsdata.speed) )
#
#                # V-Speed
#                if hasattr(gpsdata, 'epc'):
#                    self.menu.append( gtk.MenuItem("V-Speed: %sm/s (±%sm/s)" % (gpsdata.climb,gpsdata.epc)) )
#                else:
#                    self.menu.append( gtk.MenuItem("V-Speed: %sm/s" % gpsdata.climb) )

                # ----
                self.menu.append(gtk.SeparatorMenuItem())

#                # Open GMaps
#                open_gmaps = gtk.MenuItem("Open location in Google Maps")
#                open_gmaps.connect("activate", self.gmaps, 'gpsdata', gpsdata)
#                self.menu.append(open_gmaps)
#
#                # Open YMaps
#                open_ymaps = gtk.MenuItem("Open location in Yandex Maps")
#                open_ymaps.connect("activate", self.ymaps, 'gpsdata', gpsdata)
#                self.menu.append(open_ymaps)
        else:
            self.gpsState = gtk.MenuItem("GPS is Off")
            self.menu.append(self.gpsState)

            if not self.__gps_disable_stage2_timeout_handler:
                self.gpsEnable = gtk.MenuItem("Enable GPS")
                self.menu.append(self.gpsEnable)
                self.gpsEnable.connect("activate", self.gps_enable)

        self.quit_item = gtk.MenuItem("Quit")
        self.quit_item.connect("activate", self.quit)
        self.menu.append(self.quit_item)

        self.menu.show_all()
        self.set_menu(self.menu)

#    def update_gpsdata(self, gpsdata):
#        if hasattr(gpsdata, 'lat') and hasattr(gpsdata, 'epy') and self.gpsState.get_active():
#            self.redraw_ui(gpsdata)

    # gpsd default tcp\ip socket connection setup
    def run(self):
        print "run"
        #return True
        try:
            self.__gpsd_daemon_handler = gps.gps(
                host = GPSD_HOST,
                port = GPSD_PORT,
                mode = gps.WATCH_ENABLE|gps.WATCH_JSON|gps.WATCH_SCALED,
                verbose = None
            )
            self.watch(self.__gpsd_daemon_handler, GPS_DEV)
            return True
        except SocketError:
            self.gps_disable()
            #self.__gps_on = False
            #self.toggle_gps(self.gpsState)
            w = gtk.MessageDialog(
                type=gtk.MESSAGE_ERROR,
                flags=gtk.DIALOG_DESTROY_WITH_PARENT,
                buttons=gtk.BUTTONS_OK
            )
            w.set_title('socket error')
            w.set_markup(
                "could not connect to gpsd socket. make sure gpsd is running."
            )
            w.run()
            w.destroy()
            return False
        except KeyboardInterrupt:
            self.gps_disable()
            #self.gpsState.set_active(False)
            #self.toggle_gps(self.gpsState)
            return False

    # setup event watcher for gpsd
    def watch(self, daemon, device):
        print "watch"
        self.daemon = daemon
        self.device = device
        self.__w1 = gobject.io_add_watch(daemon.sock, gobject.IO_IN, self.handle_response)
        self.__w2 = gobject.io_add_watch(daemon.sock, gobject.IO_ERR, self.handle_hangup)
        self.__w3 = gobject.io_add_watch(daemon.sock, gobject.IO_HUP, self.handle_hangup)
        return True

    # action afted gpsd event succesfully fired
    def handle_response(self, source, condition):
        print "handle_response"
        if self.__gps_on:
            if self.daemon.read() == -1:
                self.handle_hangup(source, condition)
            if self.daemon.data['class'] == 'TPV':
                #self.update_gpsdata()
                self.redraw_ui(gpsdata=self.daemon.data)
        else:
            print "some error in response handling"
            quit()
        return True

    # fallback action if some problem with gpsd
    def handle_hangup(self, dummy, unused):
        #self.daemon.close()
        self.gps_disable()
        #self.gpsState.set_active(False)
        #self.toggle_gps(self.gpsState)

        w = gtk.MessageDialog(
            type=gtk.MESSAGE_ERROR,
            flags=gtk.DIALOG_DESTROY_WITH_PARENT,
            buttons=gtk.BUTTONS_OK
        )
        w.set_title('gpsd error')
        w.set_markup("gpsd has stopped sending data. try sudo /etc/init.d/gpsd restart")
        w.run()
        w.destroy()
        return True

    def gps_disable(self, dummy=None):
        print "gps_disable"
        self.__gps_on = False
        self.set_status(appindicator.STATUS_ACTIVE)

        gobject.source_remove(self.__w1)
        gobject.source_remove(self.__w2)
        gobject.source_remove(self.__w3)
        self.__gps_disable_stage2_timeout_handler = gtk.timeout_add( 10000, self.gps_disable_stage2)

        self.redraw_ui()
        return True

    def gps_disable_stage2(self):
        print "gps_disable_stage2"
        # stop communication with gpsd
        if self.__gpsd_daemon_handler:
            self.__gpsd_daemon_handler.close()
            self.__gpsd_daemon_handler = None

        # reset GPS power off timeout
        if self.__gps_off_timeout_handler:
            gtk.timeout_remove(self.__gps_off_timeout_handler)
        # stop GOBI 3000 GPS in GPS_OFF_TIMEOUT (65s by default)
        self.__gps_off_timeout_handler = gtk.timeout_add( GPS_OFF_TIMEOUT, self.gps_power_down)

        # make GPS disableable
        gtk.timeout_remove(self.__gps_disable_stage2_timeout_handler)
        self.__gps_disable_stage2_timeout_handler = None

        self.redraw_ui()

    def gps_power_down(self):
        print "gps_power_down"
        os.system('echo "\$GPS_STOP" > %s' % GPS_DEV)
        if self.__gps_off_timeout_handler:
            gtk.timeout_remove(self.__gps_off_timeout_handler)
        self.redraw_ui()
        return True

    def gps_enable(self, dummy=None):
        print "gps_enable"
        if not self.__gpsd_daemon_handler and not self.__gps_disable_stage2_timeout_handler:
            # disable the GPS disabler =)
            if self.__gps_off_timeout_handler:
                gtk.timeout_remove(self.__gps_off_timeout_handler)
                self.__gps_off_timeout_handler = None
            else: # start GOBI 3000 GPS
                os.system('echo "\$GPS_START" > %s' % GPS_DEV)
            # start communication with gpsd
            if self.run():
                self.__gps_on = True
                self.set_status(appindicator.STATUS_ATTENTION)
                self.redraw_ui()
            else:
                print "some error with run()"
                quit()
            return True
        else:
            print "daemon handler already present"
            self.redraw_ui()
            #quit()
            #self.gps_enable()

gobject.type_register(GPS)

if __name__ == "__main__":
    ind = GPS()
    gtk.main()
