#!/usr/bin/env python
"""
The vlc-cli class represents a telnet connection to the VLC console.
The class contains helper functions to extend the telnetlib functionality.
"""

from time import time
import logging
import re
import telnetlib
from .constants import MY_NAME, DEBUG, TELNET_TIMEOUT_SEC, PROMPT
from .selector import get_random_media

# tuning params
TELNET_LINE_POLL_INTERVAL_SEC = 0.01

# thinks i think i know about the console interface
# TODO: validate character encoding of console interface
ENCODING = 'utf8'
# TODO - parse login header
LOGIN_HEADER_EXAMPLE = 'VLC media player 3.0.5 Vetinari\n'

logger = logging.getLogger(MY_NAME)

# this re is a bit too brittle and doing more than it needs, simplifying:
# playlist_re = re.compile(r'^\|  (?P<playing>[* ])(?P<n>[0-9]+) - (?P<title>.+)'
#                          r'( \((?P<duration>[0-9]{2}:[0-9]{2}:[0-9]{2})\)|)'
#                          r'( \[played (?P<played>[0-9]+) times?\]$|)')
playlist_re = re.compile(r'^\|  (?P<playing>[* ])(?P<n>[0-9]+) - .+'
                         r'( \[played (?P<played>[0-9]+) times?\]|$)')


class VLCCLI(telnetlib.Telnet):
    # TODO: force the prompt using set prompt
    def write_line(self, line):
        if DEBUG:
            logger.debug(f"out: '{line}'")
        self.write(f'{line}\n'.encode(ENCODING))
        return

    def read_line(self, eol='\n', timeout=None):
        buf = self.read_until(eol.encode(ENCODING), timeout).decode(ENCODING)
        if DEBUG:
            logger.debug(f"in : '{buf.rstrip()}'")
        return buf

    def read_until_line(self, expected, eol='\n', timeout=None):
        buf = ''
        begin = time()
        while True:
            line = self.read_line(eol, TELNET_LINE_POLL_INTERVAL_SEC)
            buf += line
            if expected in line:
                break
            if not isinstance(timeout, type(None)):
                if time() - begin > timeout:
                    break
        return buf

    def is_playing(self):
        logger.info(f'Querying player state')
        self.write_line(f'is_playing')
        lines = self.read_until_line(PROMPT)
        result = None
        for line in lines.splitlines():
            if line.strip() == '0':
                result = False
                break
            elif line.strip() == '1':
                result = True
                break
        if isinstance(result, type(None)):
            raise RuntimeError(f'Failed to parse playing status in command '
                               f'response: "{lines}"')
        return result

    def playlist(self):
        logger.info(f'Querying playerlist')
        self.write_line(f'playlist')
        lines = self.read_until_line(PROMPT)
        result = list()
        state = "unknown"
        for line in lines.splitlines():
            def line_state(begin, desired):
                return line.startswith(begin) and state == desired
            # I am sure this is very brittle
            if line_state('+----[ Playlist - playlist ]', 'unknown'):
                state = 'begin'
            elif line_state('| 1 - Playlist', 'begin'):
                state = 'playlist'
            elif line_state("|  ", 'playlist'):
                match = playlist_re.search(line.strip())
                if isinstance(match, type(None)):
                    raise RuntimeError(f'Failed to parse playlist entry: '
                                       f'"{line.strip()}"')
                d = match.groupdict()
                d['playing'] = d['playing'] == '*'
                result.append(d)
            elif line_state('| 2 - Media Library', 'playlist'):
                state = 'finished'
                break
            elif line.startswith(PROMPT):
                raise RuntimeError(f'Failed to parse playlist command response'
                                   f' "{lines}"')
        return result

    def delete(self, id_):
        logger.info(f'deleteing file id {int(id_):d} from queue')
        self.write_line(f'delete {int(id_):d}')
        return

    def left_to_play(self):
        p = self.playlist()
        result = 0
        currentlyplaying = False
        for item in p:
            if isinstance(item['played'], str) and not item['playing']:
                self.delete(item['n'])
            elif item['playing']:
                currentlyplaying = True
            elif currentlyplaying:
                result += 1
        if not currentlyplaying:
            result = len(p)
        logger.info(f'{result:d} tracks in queue and unplayed')
        return result

    def add_medias_if_queue_short(self, minqueuelen, mediadir):
        while self.left_to_play() < minqueuelen:
            mediapath = get_random_media(mediadir)
            logger.info(f'Adding "{mediapath}" queue')
            # TODO: we may need to quote some characters in the mediapath
            self.write_line(f'enqueue file://{mediapath}')
            self.read_until_line(PROMPT, timeout=TELNET_TIMEOUT_SEC)
        return

    def play(self):
        if not self.is_playing():
            self.write_line(f'play')
            logger.info(f'Playing')
            self.read_until_line(PROMPT, timeout=TELNET_TIMEOUT_SEC)
        return

    def close(self):
        self.write_line(f'logout')
        return super(VLCCLI, self).close()
