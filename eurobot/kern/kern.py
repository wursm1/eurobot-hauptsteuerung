__author__ = 'mw'

import sys
import time
from eurobot.libraries import can
from eurobot.kern import debug


def main():
    """ Main programm running on Robot"""
    if len(sys.argv) != 2:
        print('Provide CAN device name (can0, vcan0 etc.)')
        sys.exit(0)
    can_socket = can.Can(sys.argv[1], can.MsgSender.Hauptsteuerung)
    debugger = debug.LaptopCommunication(can_socket)
    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()