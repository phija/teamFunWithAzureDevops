#!/usr/bin/env python
# encoding: utf8

import imaplib
import base64
import email
import sys
from sys import argv
import vlc
import time
from gtts import gTTS
import os

volume = 100
playerRunning = 0


def SongFinished(event):
    global playerRunning
    playerRunning = 0


def playFile(song):
    print("want to play " + song)
    global playerRunning
    playerRunning = 1
    instance = vlc.Instance()
    player = instance.media_player_new()
    media = instance.media_new_path(song)
    player.audio_set_volume(volume)
    player.set_media(media)
    events = player.event_manager()
    events.event_attach(vlc.EventType.MediaPlayerEndReached, SongFinished)
    player.play()
    while playerRunning == 1:
        time.sleep(0.1)


def speech(text, language='en'):
    tts = gTTS(text, lang=language, slow=False)
    tts.save('speech.mp3')
    playFile('speech.mp3')


if len(argv) > 2:
    speech(argv[1], argv[2])
elif len(argv) > 1:
    speech(argv[1])
else:
    print('usage: ./speech.py [text-to-say] [language]')
