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
import re
import soupsieve
from bs4 import BeautifulSoup

if settings.debug:
    settings.volume = 0

running = 1
playerRunning = 0


def SongFinished(event):
    global playerRunning
    playerRunning = 0


def playFile(song):
    global playerRunning
    playerRunning = 1
    instance = vlc.Instance()
    player = instance.media_player_new()
    media = instance.media_new_path(song)
    player.audio_set_volume(settings.volume)
    player.set_media(media)
    events = player.event_manager()
    events.event_attach(vlc.EventType.MediaPlayerEndReached, SongFinished)
    player.play()
    while playerRunning == 1:
        time.sleep(0.1)

def ensureConnection():
    works = 0
    while works == 0:
        try:
            gTTS("test")
            works = 1
            pass
        except:
            print("no connection, retrying in 5 seconds...")
            time.sleep(5)
            pass


def speech(text):
    print("want to say: " + text)
    tts = gTTS(text, lang='en', slow=False)
    tts.save('temp.mp3')
    playFile('temp.mp3')


def getNameRequested(text):
    soup = BeautifulSoup(text, "html.parser")
    list = [link.get_text() for link in soup.select("td")]
    request = list.index("Requested for")
    name = list[request + 1].split(" ")[0].split(".")[0]
    return name


def getNamePR(text, pattern):
    match = re.search(pattern, text)
    if match:
        found = match.group(1)
        return found
    else:
        return "Dude"


def checkEmails(debug):
    mail = imaplib.IMAP4_SSL(settings.email['imap_server'], 993)
    mail.login(settings.email['user'], settings.email['pw'])
    mail.select("Inbox")

    typ, message_numbers = mail.uid('search', None,'(UNSEEN)')

    for num in message_numbers[0].split():
        typ, data = mail.uid('fetch', num, 'RFC822')
        if typ != 'OK':
            print("ERROR getting message", num)

        msg = email.message_from_string(data[0][1])
        subject = msg['Subject']
        if debug: print("Subject: " + subject)

        while msg.is_multipart():
            msg = msg.get_payload(0)

        content = msg.get_payload(decode=True)
        if "created a new pull request" in content:
            print("    --> PR found!")
            playFile(settings.sound['pullrequest'])
            name = getNamePR(content, '\n(.+?) created a new pull request').lstrip()
            print("==> " + name)
            name = name.split(" ")[0].split(".")[0]
            speech(name + ' created a new pull request!')
        elif "[PR build succeeded] " + settings.project_name in subject:
            print("    --> SUCCEEDED BUILD")
            name = getNameRequested(content)
            print("==> " + name)
            speech('Yes, build succeeded! Congrats, ' + name + ' to your great work!')
        elif "[PR build failed] " + settings.project_name in subject:
            print("    --> FAILED BUILD")
            name = getNameRequested(content)
            speech("Oh no! " + name + ", you need to fix your build!")
        elif "gtts" in subject:
            firstline = content.split('\n', 1)[0]
            speech(firstline)

        if debug == False:
            mail.store(num, '+FLAGS', '\SEEN')

    mail.close()
    mail.logout()


ensureConnection()
speech('starting up...')
while running == 1:
    print("checking for mails...")
    checkEmails(settings.debug)
    time.sleep(settings.email['interval'])
