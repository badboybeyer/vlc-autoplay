#!/usr/bin/env python
"""
The vlc-cli class represents a telnet connection to the VLC console.
The class contains helper functions to extend the telnetlib functionality.
"""

from .constants import MY_NAME, DEBUG

# tuning params
TELNET_LINE_POLL_INTERVAL_SEC = 0.01

# thinks i think i know about the console interface
PROMPT = '> '
# TODO: validate character encoding of console interface
ENCODING = 'utf8'
# TODO - parse login header
LOGIN_HEADER_EXAMPLE = 'VLC media player 3.0.5 Vetinari\n'

logger = logging.getLogger(MY_NAME)

playlist_re = re.compile(r'^\|  (?P<playing>[* ])(?P<n>[0-9]+) - (?P<title>.+) \((?P<duration>[0-9]{2}:[0-9]{2}:[0-9]{2})\)($| \[played (?P<played>[0-9]+) times?\]$)')

class VLCCLI(telnetlib.Telnet):
    def write_line(self, line):
        if DEBUG:
            logger.debug(f"out: '{line}'")
        self.write(f'{line}\n'.encode(ENCODING))
        return

    def read_line(self, eol='\n', timeout=None):
        buf = self.read_until(eol.encode(ENCODING), timeout).decode(ENCODING)
        if DEBUG:
            logger.debug(f"in : '{buf}'")
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
            raise RuntimeError(f'Failed to parse playing status in command response: "{lines}"')
        return result

    def playlist(self):
        logger.info(f'Querying playerlist')
        self.write_line(f'playlist')
        lines = self.read_until_line(PROMPT)
        result = list()
        state = "unknown"
        for line in lines.splitlines():
            # I am sure this is very brittle
            if line.startswith('+----[ Playlist - playlist ]') and state == 'unknown':
                state = 'begin'
            elif line.startswith('| 1 - Playlist') and state == 'begin':
                state = 'playlist'
            elif line.startswith("|  ") and state == 'playlist':
                d = playlist_re.search(line).groupdict()
                d['playing'] = d['playing'] == '*'
                result.append(d)
            elif line.startswith('| 2 - Media Library') and state == 'playlist':
                state = 'finished'
                break
            elif line.startswith(PROMPT):
                raise RuntimeError(f'Failed to parse playlist command response "{lines}"')
        return result
    
    def delete(self, id_):
        self.write_line(f'delete {id_:n}')
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
        logger.info(f'{result:d} tracks in queue and unplayed')
        return result

    def add_videos_if_queue_short(self, minqueuelen, showsdir=SHOWS_DIR):
        if self.left_to_play() < minqueuelen:
            videopath = get_random_show(showsdir)
            logger.info(f'Adding "{videopath}" to {name} queue')
            # TODO: we may need to quote some characters in the videopath
            self.write_line(f'enqueue file://{videopath}')
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
