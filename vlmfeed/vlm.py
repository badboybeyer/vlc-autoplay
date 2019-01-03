#!/usr/bin/env python
"""
The VLM class represents a telnet connection to the VLC VLM.
The class contains helper functions to extend the telnetlib functionality.
"""

from .constants import MY_NAME, DEBUG

# tuning params
TELNET_LINE_POLL_INTERVAL_SEC = 0.01

# thinks i think i know about the VLM interface
PROMPT = '> '
# TODO: validate character encoding of VLM interface
ENCODING = 'utf8'
# TODO - parse login header
LOGIN_HEADER_EXAMPLE = 'VLC media player 3.0.5 Vetinari\n'

logger = logging.getLogger(MY_NAME)

class VLM(telnetlib.Telnet):
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

    def status(self, name):
        logger.info(f'Getting status of {name} media object')
        self.write_line(f'show {name}')
        lines = self.read_until_line(PROMPT)
        result = dict()
        lastlvl = -1
        stack = [result]
        lastkey = None
        for line in lines.splitlines():
            lvl = (len(line) - len(line.lstrip())) // 4
            # this fails for sub data, should replace with RE ~ /$       [a-z]/
            if lvl <= 1:
                continue
            if lvl > lastlvl and not isinstance(lastkey, type(None)):
                if not isinstance(stack[-1][lastkey], type(None)):
                    raise RuntimeError('The status parser does not expect sub-levels '
                                       'to items with data (or a colon)')
                stack[-1][lastkey] = dict()
                stack.append(stack[-1][lastkey])
            if lvl < lastlvl:
                stack.pop()
            key = line.split(':')[0].strip()
            if ':' in line:
                stack[-1][key] = ':'.join(line.split(':')[1:]).strip()
            else:
                stack[-1][key] = None
            lastlvl = lvl
            lastkey = key
        return result

    def is_playing(self, name):
        s = self.status(name)
        try:
            ans = s['instances']['instance']['state'] == 'playing'
        except TypeError:
            ans = False
        return ans

    def left_to_play(self, name=NAME):
        s = self.status(name)
        if isinstance(s['inputs'], type(None)):
            playlistlength = 0
        else:
            playlistlength = len(s['inputs'])
        try:
            playlistindex = int(s['instances']['instance']['playlistindex'])
        except TypeError:
            playlistindex = 0
        ans = playlistlength - playlistindex
        logger.info(f'{ans:d} tracks in {name} queue and unplayed')
        return ans 

    def add_videos_if_queue_short(self, minqueuelen, name=NAME, showsdir=SHOWS_DIR):
        if self.left_to_play(name) < minqueuelen:
            videopath = get_random_show(showsdir)
            logger.info(f'Adding "{videopath}" to {name} queue')
            self.write_line(f'setup {name} input "file://{videopath}"')
            self.read_until_line(PROMPT, timeout=TELNET_TIMEOUT_SEC)
        return

    def play(self, name=NAME):
        if not self.is_playing(name):
            self.write_line(f'control {name} play')
            logger.info(f'Playing {name} media')
            self.read_until_line(PROMPT, timeout=TELNET_TIMEOUT_SEC)
        return

    def close(self):
        self.write_line(f'logout')
        return super(VLM, self).close()
