#!/usr/bin/env python
"""
selector are methods that search a media library and select a media to play
"""
import logging
import os
import random
import magic
from .constants import MY_NAME, VIDEO_MEDIA

logger = logging.getLogger(MY_NAME)
MAX_DESCENT_FAILURES = 5


def get_random_media(mediadir, mediatypes=VIDEO_MEDIA):
    logger.info(f'Finding a random media file in "{mediadir}"')
    mediapaths = list()
    for entry in os.scandir(mediadir):
        if entry.is_dir():
            mediapaths.append(entry)
        elif entry.is_file():
            class_ = magic.from_file(entry.path, mime=True).split('/')[0]
            if class_ in mediatypes:
                mediapaths.append(entry)
    if not len(mediapaths):
        raise RuntimeError(f'Could not find any media in "{mediadir}"')
    fails = 0
    while fails < MAX_DESCENT_FAILURES:
        result = random.choice(mediapaths)
        if result.is_dir():
            try:
                result = get_random_media(result.path)
            except RuntimeError:
                fails += 1
                result = None
            else:
                break
        else:
            result = result.path
            break
    if isinstance(result, type(None)):
        raise RuntimeError(f'Exceded max retries why searching for media in '
                           f'subdirs of "{mediadir}"')
    return result
