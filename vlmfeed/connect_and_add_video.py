#!/usr/bin/env python
"""
connect via telent to a VLC VLM interface
check if a media source has a queue of media and is playing
add media sources from a dump if the queue is short
play using the media source if it is stopped
"""

from time import time
import telnetlib
import os
import random
import magic
import logging
from pathlib import Path

# localization
VLM_PORT = '4212'
VLM_HOST = '127.0.0.1'
VLM_PASSWD = 'admin'
NAME = "shows"  # of broadcast element to control
SHOWS_DIR = os.path.join(Path.home(), 'Videos')
MY_NAME = 'cna-video'

# tuning params
DEBUG = True
TELNET_LINE_POLL_INTERVAL_SEC = 0.01
TELNET_TIMEOUT_SEC = 1
TOO_FEW_VIDEOS_IN_QUEUE = 2

logger = logging.getLogger(MY_NAME)

# thinks i think i know about the VLM interface
PROMPT = '> '
# TODO: validate character encoding of VLM interface
ENCODING = 'utf8'
# TODO - parse login header
LOGIN_HEADER_EXAMPLE = 'VLC media player 3.0.5 Vetinari\n'


def main():
    import argparse
    from sys import stdout    
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-H', '--host', help='hostname for VLM', default=VLM_HOST)
    parser.add_argument('-p', '--port', type=int, help='port number for VLM', default=VLM_PORT)
    parser.add_argument('-P', '--password', help='login password for VLM', default=VLM_PASSWD)
    parser.add_argument('-n', '--name', help='name of media source to use in VLM', default=NAME)
    parser.add_argument('-d', '--dump', help='path to search for new videos in', default=SHOWS_DIR)
    parser.add_argument('-v', '--verbose', action='count',
                        help='verbose operation')
    parser.add_argument('-l', '--logfile', type=argparse.FileType('a'),
                        default=stdout, help='log file')    
    args = parser.parse_args()
    if isinstance(args.verbose, type(None)):
        verbosity = logging.WARNING
    elif args.verbose >= 2:
        verbosity = logging.DEBUG
    elif args.verbose == 1:
        verbosity = logging.INFO
    else:
        msg = 'Unsupported number of verbose flags "{}"'
        raise RuntimeError(msg.format(args.verbose))
    initLogger(logger, args.logfile, verbosity)            
    connect_and_play(host=args.host, port=args.port, password=args.password, name=args.name,
                     showsdir=args.dump)
    return

def connect_and_play(host=VLM_HOST, port=VLM_PORT, password=VLM_PASSWD,
                     name=NAME, showsdir=SHOWS_DIR):
    handle = connect(host=host, port=port, password=password)
    # TODO: handle/escape characters in file name
    handle.add_videos_if_queue_short(TOO_FEW_VIDEOS_IN_QUEUE, name, showsdir)
    handle.play(name)
    if not DEBUG:
        handle.close()
    return handle


def connect(host, port, password):
    logger.info(f'Connecting to VLM on {host}:{port}')
    handle = VLM(host=host, port=port)
    handle.read_until_line('Password: ', timeout=TELNET_TIMEOUT_SEC)
    handle.write_line(password)
    handle.read_until_line(PROMPT, timeout=TELNET_TIMEOUT_SEC)
    return handle

def get_random_show(showsdir=SHOWS_DIR):
    logger.info(f'Finding a random video file in "{showsdir}"')
    showpaths = [os.path.join(showsdir,d) for d in os.listdir(showsdir)
                  if os.path.isdir(os.path.join(showsdir,d))]
    showpath = random.choice(showpaths)
    logger.info(f'Finding a random video file in "{showpath}"')
    videopaths = list()
    for dirpath, dirnames, filenames in os.walk(showpath):
        for fn in filenames:
            filepath = os.path.join(dirpath, fn)
            if 'video' in magic.from_file(filepath, mime=True):
                videopaths.append(filepath)
    return random.choice(videopaths)


def initLogger(logger, fh, verbosity=logging.WARNING):
    """
    Configures the logger for my perfered semantics

    logger is the logging.GetLogger object to configure
    fh is  the file like object to output the log to
    verbosity is one of the enumerated logging levels
              from the library
    """
    loggerhandler = logging.StreamHandler(fh)
    format_ = '%(asctime)s, %(name)s, %(levelname)s, %(message)s'
    loggerformatter = logging.Formatter(format_)
    loggerhandler.setFormatter(loggerformatter)
    logger.addHandler(loggerhandler)
    logger.setLevel(verbosity)
    logger.info('%s started', MY_NAME)
    logger.debug("Logging to file: {}".format(str(fh)))
    return


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

if __name__ == '__main__':
    main()
