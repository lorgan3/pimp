#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
PiMP, the PI Media Player.

PiMP is a simple media player designed for the Raspberry Pi. 
It works in console mode and use OMXPLAYER backend for hardware video 
acceleration.

Author:  Julien Pecqueur (JPEC)
Email:   jpec@julienpecqueur.net
Home:    http://raspyplayer.org
Sources: https://github.com/jpec/pimp

This software is provided without any warranty. 

If you want to improve it, modify it, correct it, please send me your 
modifications so i'll backport them on the reference tree.

Have fun.

Julien

"""

VERSION = 0.4

# Allowed movies extensions
EXTENSIONS = ["avi", "mpg", "mp4", "mkv"]

# OMXPLAYER options
# -o : output [local|hdmi]
# -t : enable subtitles [on|off]
# --align : subtitles aligment [center|left|right]
OPTIONS = '-o hdmi -t on --align center'

K_NEXT="k"
K_PREV="i"
K_NPAG="h"
K_PPAG="y"
K_PLAY="p"
K_SCAN="R"
K_QUIT="Q"
K_FIND="f"

import curses
from sys import argv
from os import listdir
from subprocess import call
from os.path import isfile
from os.path import isdir
from os.path import expanduser
from os.path import basename


def play(movie):
    "Play a movie"
    cmd = 'omxplayer {0} \"{1}\" > .omx.log'
    sub = movie[0:-3] + "srt"
    if isfile(sub):
        options = OPTIONS + ' --subtitles \"{0}\"'.format(sub)
    else:
        options = OPTIONS
    call(cmd.format(options, movie), shell=True)
    return(movie)


def scan_dir_movies_for_movies(dir_movies):
    "Scan dir_movies directory for movies and return a list."
    lst_movies = list()
    for f in listdir(dir_movies):
        p = dir_movies+"/"+f
        if f[0] == ".":
            continue
        elif isdir(p):
            lst_movies += scan_dir_movies_for_movies(p)
        elif isfile(p) and f[-3:] in EXTENSIONS:
            lst_movies.append(p)
    return(lst_movies)


def get_movies_from_dir_movies(dir_movies):
    "Get movies from dir_movies directories and return a dictionary."
    dic_movies = dict()
    if isdir(dir_movies):
        lst_paths = scan_dir_movies_for_movies(dir_movies)
        if not lst_paths:
            return(False)
        for p in lst_paths:
            dic_movies[basename(p)] = p
        return(dic_movies)


def get_movies_from_db(db):
    "Read db and return a dictionary."
    if isfile(db):
        f = open(db, "r")
        dic_movies = dict()
        for l in f.readlines():
            l = l.replace("\n", "")
            dic_movies[basename(l)] = l
        f.close()
        return(dic_movies)
    else:
        return(None)


def save_movies_to_db(db, dic_movies):
    "Save movies to db."
    f = open(db, "w")
    for e in dic_movies:
        f.write(dic_movies[e]+"\n")
    f.close()
    return(True)


class PiMP(object):

    def __init__(self, stdscr):
        "Initialization."
        self.stdscr = stdscr
        self.status = "Hi guys! What's up? ;-)"
        self.db = expanduser("~/.movies.db")
        self.parse_args()
        self.init_curses()
        self.reload_database()
        self.get_key_do_action()


    def parse_args(self):
        "Parse command line parameters."
        self.dir_movies = expanduser("~/movies")
        for a in argv:
            if isdir(a):
                self.dir_movies = a


    def init_curses(self):
        "Init curses settings."
        curses.curs_set(0)
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_RED, -1)
        y,x = self.stdscr.getmaxyx()
        self.H = y
        self.W = x


    def reload_database(self, force=None):
        "Reload database (if force, rescan directories)."
        self.init_cursor()
        self.draw_status("Loading library... Please wait!", True)
        self.load_dic_movies(force)
        self.load_lst_movies()
        self.draw_status("Library reloaded.", True)
        self.draw_window()


    def init_cursor(self):
        "Init cursor settings."
        self.cursor = dict()
        self.cursor['current'] = 0
        self.cursor['first'] = 0
        self.cursor['show'] = self.H - 2


    def load_dic_movies(self, force=False):
        "Load dic_movies."
        self.dic_movies = get_movies_from_db(self.db)
        if not self.dic_movies  or force:
            self.dic_movies = get_movies_from_dir_movies(self.dir_movies)
            save_movies_to_db(self.db, self.dic_movies)


    def load_lst_movies(self):
        "Load lst_movies."
        self.lst_movies = list()
        for movie in self.dic_movies:
            self.lst_movies.append(movie)
        self.lst_movies.sort()


    def draw_window(self):
        "Draw window."
        # Cusor of movies to display (first/last)
        first = self.cursor['first']
        last = self.cursor['first'] + self.cursor['show']
        lst_movies = self.lst_movies[first:last]
        # Title of window
        options = " - " + K_PLAY + ":Play " + K_SCAN + ":Refresh "
        options += K_PREV + ":Up " + K_NEXT + ":Down " + K_PPAG 
        options += ":PUp " + K_NPAG + ":PDown " + K_FIND + ":Find "
        options += K_QUIT + ":Quit"
        title = "PiMP V" + str(VERSION) + options
        self.draw_line_of_text(0, title, curses.A_REVERSE)
        # List of movies
        i = 1
        for movie in lst_movies:
            if movie == self.get_current_movie():
                self.draw_line_of_text(i, "> "+movie, curses.color_pair(1))
            else:
                self.draw_line_of_text(i, "  "+movie, None)
            i += 1
        # Status
        self.draw_status(self.status)
        self.stdscr.refresh()


    def draw_status(self, text, force=False):
        "Draw the status line"
        self.status = text
        self.draw_line_of_text(self.H-1, "> " + text, curses.A_REVERSE)
        if force:
            self.stdscr.refresh()


    def draw_line_of_text(self, pos, text, color):
        "Draw a line of text on the window."
        text = text[0:self.W-1]
        if color:
            text = text.ljust(self.W-1, " ")
            self.stdscr.addstr(pos, 0, text, color)
        else:
            self.stdscr.addstr(pos, 0, text)
        self.stdscr.clrtoeol()


    def get_current_movie(self):
        "Return the selected movie."
        return(self.lst_movies[self.cursor['current']])


    def scroll_to(self, offset):
        "Scroll to offset."
        if offset <= len(self.lst_movies):
            self.cursor['current'] = offset
            self.cursor['first'] = offset
            return(True)
        else:
            return(False)


    def scroll_up(self, nb_lines):
        "Scroll up the list of movies."
        if self.cursor['current'] > 0:
            self.cursor['current'] -= nb_lines
        if self.cursor['current'] < self.cursor['first']:
            self.cursor['first'] -= nb_lines


    def scroll_down(self, nb_lines):
        "Scroll down the list of movies."
        if self.cursor['current'] < len(self.lst_movies) - 1:
            self.cursor['current'] += nb_lines
        if self.cursor['current'] >= self.cursor['show'] + self.cursor['first']:
            self.cursor['first'] += nb_lines


    def play_selected_movie(self):
        "Play selected movie."
        movie = None
        movie = self.dic_movies[self.lst_movies[self.cursor['current']]]
        if movie:
            self.stdscr.clear()
            self.stdscr.refresh()
            res = play(movie)
            self.draw_status("End of movie ({0}).".format(res), True)
        else:
            self.draw_status("Oops! Cannot play selected movie.", True)


    def find_and_scroll(self):
        "Search a movie and scroll to it"
        self.draw_status("Please enter the first letter of the movie.", True)
        # get the first letter to find
        ch = chr(self.stdscr.getch())
        # find the first movie begining with this letter
        offset = 0
        find = False
        for movie in self.lst_movies:
            if str(movie[0]).upper() == str(ch).upper():
                find = True
                break
            offset += 1
        # scroll to offset
        if find and self.scroll_to(offset):
            self.draw_status("Scrolled to movies starting with '{0}'.".format(ch), True)
        else:
            self.draw_status("Oops! No movies starts with '{0}'.".format(ch), True)


    def get_key_do_action(self):
        "Event loop."
        while True:
            ch = self.stdscr.getch()
            if ch == curses.KEY_UP or ch == ord(K_PREV):
                self.scroll_up(1)
            elif ch == curses.KEY_DOWN or ch == ord(K_NEXT):
                self.scroll_down(1)
            elif ch == curses.KEY_NPAGE or ch == ord(K_NPAG):
                self.scroll_down(self.H-2)
            elif ch == curses.KEY_PPAGE or ch == ord(K_PPAG):
                self.scroll_up(self.H-2)   
            elif ch == ord(K_PLAY):
                self.play_selected_movie()
            elif ch == ord(K_SCAN):
                self.reload_database(True)
            elif ch == ord(K_QUIT):
                break
            elif ch == ord(K_FIND):
                self.find_and_scroll()
            self.draw_window()


# MAIN PROGRAM 
if __name__ == '__main__':
    app = curses.wrapper(PiMP)
# END MAIN PROGRAM 
