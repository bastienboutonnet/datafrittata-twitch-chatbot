#! /usr/bin/env python3

"""
datafrittata-twitch-chatbot: chatbot for Twitch that is developed on stream.
"""

import sys

if __name__ == "__main__":
    # Does the user use the correct version of Python
    # Reference:
    #  If Python version is 3.9.6
    #               major --^
    #               minor ----^
    #               micro ------^
    major = sys.version_info[0]
    minor = sys.version_info[1]
    micro = sys.version_info[2]

    pyversion = str(major) + "." + str(minor) + "." + str(micro)

    if major != 3 or major == 3 and minor < 7:
        print("This chatbot does need at least Python version 3.7 to work.")
        print("You're using Python version %s" % (pyversion))
        sys.exit(1)

    import chatbot

    chatbot.main()
