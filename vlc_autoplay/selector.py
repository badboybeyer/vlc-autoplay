#!/usr/bin/env python
"""
selector are methods that search a media library and select a media to play
"""
import logging
import os
import random
import magic
from .constants import MY_NAME

logger = logging.getLogger(MY_NAME)


def get_random_media(mediadir):
    logger.info(f'Finding a random media file in "{mediadir}"')
    showpaths = [os.path.join(mediadir, d) for d in os.listdir(mediadir)
                 if os.path.isdir(os.path.join(mediadir, d))]
    showpath = random.choice(showpaths)
    logger.info(f'Finding a random media file in "{showpath}"')
    mediapaths = list()
    for dirpath, dirnames, filenames in os.walk(showpath):
        for fn in filenames:
            filepath = os.path.join(dirpath, fn)
            class_ = magic.from_file(filepath, mime=True).split('/')[0]
            if class_ in ('video', 'image', 'audio'):
                mediapaths.append(filepath)
    if len(mediapaths):
        result = random.choice(mediapaths)
    else:
        result = random.choice(mediadir)
    return result
