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
from .vlm import VLM
from .constants import MY_NAME, DEBUG

# localization
VLM_PORT = '4212'
VLM_HOST = '127.0.0.1'
VLM_PASSWD = 'admin'
NAME = "shows"  # of broadcast element to control
SHOWS_DIR = os.path.join(Path.home(), 'Videos')

# tuning params
TELNET_TIMEOUT_SEC = 1
TOO_FEW_VIDEOS_IN_QUEUE = 2

logger = logging.getLogger(MY_NAME)

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


if __name__ == '__main__':
    main()
