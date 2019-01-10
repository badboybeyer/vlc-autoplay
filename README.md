# vlc-autoplay
Add media from a library rando-magically to a VLC playlist using the RC or telnet interface

## Installation

'''shell
$ pip install vlc-autoplay
'''

## Useage

Start VLC and enable the console interface. For example:

'''shell
$ cvlc --intf rc --cli-host=telnet://127.0.0.1:4212
'''

Run vlc-autoplay to add media and start playback. For example:

'''shell
$ connect_and_add_media -H 127.0.0.1 -p 4212 -d /path/to/media 
'''

