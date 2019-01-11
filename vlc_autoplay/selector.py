#!/usr/bin/env python
"""
selector are methods that search a video library and select a video to play
"""
import logging
import os
import random
import magic
from .constants import MY_NAME

logger = logging.getLogger(MY_NAME)


def get_random_show(showsdir):
    logger.info(f'Finding a random video file in "{showsdir}"')
    showpaths = [os.path.join(showsdir, d) for d in os.listdir(showsdir)
                 if os.path.isdir(os.path.join(showsdir, d))]
    showpath = random.choice(showpaths)
    logger.info(f'Finding a random video file in "{showpath}"')
    videopaths = list()
    for dirpath, dirnames, filenames in os.walk(showpath):
        for fn in filenames:
            filepath = os.path.join(dirpath, fn)
            if 'video' in magic.from_file(filepath, mime=True):
                videopaths.append(filepath)
    return random.choice(videopaths)
