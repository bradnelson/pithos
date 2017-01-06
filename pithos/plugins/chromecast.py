# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: nil; -*-
### BEGIN LICENSE
# Copyright (C) 2015 Brad Nelson
#This program is free software: you can redistribute it and/or modify it 
#under the terms of the GNU General Public License version 3, as published 
#by the Free Software Foundation.
#
#This program is distributed in the hope that it will be useful, but 
#WITHOUT ANY WARRANTY; without even the implied warranties of 
#MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR 
#PURPOSE.  See the GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License along 
#with this program.  If not, see <http://www.gnu.org/licenses/>.
### END LICENSE

from pithos.plugin import PithosPlugin
import logging
import math

from gi.repository import Gst, GstPbutils, GObject, Gtk, Gdk, Pango, GdkPixbuf, Gio, GLib

#from __future__ import print_function
from pprint import pprint
import time
import pychromecast
from pychromecast.controllers import BaseController


APP_ID = 'io.github.Pithos'


class ChromecastPlugin(PithosPlugin):
    preference = 'enable_chromecast'
    description = 'Cast media to local Chromecast devices'

    def on_enable(self):
        self.playstate_changed_handle = self.window.connect('play-state-changed', self._playstate_changed)
        self.song_changed_handle = self.window.connect('song-changed', self._song_changed)
        self.volume_changed_handle = self.window.player.connect("notify::volume", self._volume_changed)
        self.buffering_finished_handle = self.window.connect("buffering-finished", self._buffering_finished)
        self.exiting_handle = self.window.connect("exiting", self._close_chromecast_connection)
        
        # Add a popup alert telling the user to check the Pithos menu for more options.
        
        
        return
        
    def on_disable(self):
        return
    
    def on_prepare(self):
        
        #  Prepare UI with additional menu for Chromecast
        menu = Gio.Application.get_default().get_app_menu()
        it = menu.iterate_item_links(menu.get_n_items() - 1)
        assert(it.next())
        last_section = it.get_value()
        
        chromecast1 = Gio.MenuItem.new("Living room Chromecast", 'win.one')
        chromecast2 = Gio.MenuItem.new("Some Other Caster", 'win.two')
        #chromecastSection = Gio.MenuItem.new_section('Chromecast', (chromecast1, chromecast2))
        
        chromecast_menu = Gio.MenuItem.new(('Chromecast'), 'win.chromecast')
        #chromecast_menu.set_submenu(chromecast1)
        last_section.prepend_item(chromecast_menu)
        


        #dummyChromeCast = Gio.MenuItem.new(('Living room Chromecast'), '')
        
        #shortcuts_item.append(dummyChromeCast)
        
        #action = Gio.SimpleAction.new("quit", None)
        #action.connect("activate", self.quit_cb)
        #self.add_action(action)

        self.volume = 1
        self.playstate = False
        print("Connecting to Chromecast, please wait...")
        
        self.cast = pychromecast.get_chromecast(friendly_name="Living room Chromecast")
        self.mc = self.cast.media_controller
        
        #pprint(self.cast.device)
        #pprint(self.cast.status)

    def _song_changed(self, window, song):
        print("\nCasting song %s - %s" %(song.artist, song.songName))
        self.mc.play_media(url=song.audioUrl, 
                           content_type="audio/mpeg", 
                           title="Supercalifragilisticexpialodocious %s - %s" %(song.artist, song.songName), 
                           thumb=song.artRadio)
        self.playstate = True
        #  Don't allow both local and Chromecast media to play simultaneously. 
        self.window.player.set_state(Gst.State.PAUSED)
        #pprint(self.mc.status)

    def _playstate_changed(self, window, state):
        #  Change the play state of the Chromecast.
        #  Playing if state is true, paused if false
        print("Playstate changed: %d" %state)
        if state != self.playstate:
            if state:
                #  Don't allow both local and Chromecast media to play simultaneously
                self.window.player.set_state(Gst.State.PAUSED)
                self.mc.play();
            else:
                self.mc.pause();
            self.playstate = state

    def _volume_changed(self, player, spec):
        # Forward updated volume level to the Chromecast, if it has changed
        new_volume = round(math.pow(player.props.volume, 1.0/3.0), 4)
        if (self.volume != new_volume):
            self.volume = new_volume
            self.cast.set_volume(new_volume)

    def _close_chromecast_connection(self, window, state):
        #  Shut down the Chromecast app if Pithos is being closed.
        self.cast.quit_app()
        
    def _buffering_finished(self, window, blah):
        #  Stop the local audio stream if we're casting
        self.window.player.set_state(Gst.State.PAUSED)

    # Capture the loss of Chromecast connection somewhere and pause playing if this happens.

