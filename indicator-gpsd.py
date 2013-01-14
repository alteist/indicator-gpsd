#!/usr/bin/env python
# -*- coding: utf-8 -*-
# indicator-gpsd v0.0.2
# https://github.com/alteist/indicator-gpsd

### BEGIN BSD LICENSE
# Copyright (c) 2013, Roman Rakul, alteist@gmail.com
# All rights reserved.
# Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
# Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
# Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
### END BSD LICENSE

import os
import gobject
import gtk
import appindicator
import sys
import gps
from socket import error as SocketError

# see README.md for help on options
GPS_OFF_TIMEOUT = 65000
GPS_DEV = "/dev/ttyUSB2"
GPSD_HOST = "127.0.0.1"
GPSD_PORT = 2947

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
            "indicator-gpsd",
            os.path.abspath('.')+"/indicator-gpsd-off.png",
            appindicator.CATEGORY_HARDWARE)
        self.set_status(appindicator.STATUS_ACTIVE)
        self.set_attention_icon (os.path.abspath('.')+"/indicator-gpsd-on.png",)
        self.redraw_ui()

    # open Google Maps in default browser
    def gmaps(self, menuitem, select, gpsdata):
        latlon = "%s,%s" % (gpsdata.lat,gpsdata.lon)
        os.system('x-www-browser "http://maps.google.com/maps?ll=%s&q=%s"' % (latlon,latlon))

    # open Yandex Maps in default browser
    def ymaps(self, menuitem, select, gpsdata):
        lonlat = "%s,%s" % (gpsdata.lon,gpsdata.lat)
        os.system('x-www-browser "http://maps.yandex.ru/?ll=%s&q=%s&z=13&l=map"' % (lonlat,lonlat))

    # open Open Street Map in default browser
    def osmaps(self, menuitem, select, gpsdata):
        os.system('x-www-browser "http://www.openstreetmap.org/index.html?lat=%s&lon=%s&zoom=13"' % (gpsdata.lat,gpsdata.lon))

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

                # Open Google Maps
                open_gmaps = gtk.MenuItem("Open location in Google Maps")
                open_gmaps.connect("activate", self.gmaps, 'gpsdata', gpsdata)
                self.menu.append(open_gmaps)

                # Open Yandex Maps
                open_ymaps = gtk.MenuItem("Open location in Yandex Maps")
                open_ymaps.connect("activate", self.ymaps, 'gpsdata', gpsdata)
                self.menu.append(open_ymaps)

                # Open Open Street Map
                open_osmaps = gtk.MenuItem("Open location in Open Street Maps")
                open_osmaps.connect("activate", self.osmaps, 'gpsdata', gpsdata)
                self.menu.append(open_osmaps)

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
