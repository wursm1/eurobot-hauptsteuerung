from eurobot.libraries import can

__author__ = 'mw'

import sys
import time


def main():
    """ This module generates CAN test traffic. """
    if len(sys.argv) != 2:
            print('Provide CAN device name (can0, vcan0 etc.)')
            sys.exit(0)
    can_connection = can.Can(sys.argv[1], can.MsgSender.Debugging)

    x = 0
    y = 0
    angle = 0
    while True:
        angle += 10
        x += 5
        y += 5
        can_msg = {
            'type': can.MsgTypes.Position_Robot_1,
            'position_correct': True,
            'angle_correct': False,
            'angle': angle,
            'y_position': y,
            'x_position': x
        }
        can_connection.send(can_msg)

        can_msg = {
            'type': can.MsgTypes.Position_Enemy_1,
            'position_correct': False,
            'angle_correct': True,
            'angle': angle + 100,
            'y_position': y + 100,
            'x_position': x + 100
        }
        can_connection.send(can_msg)
        print(angle)
        time.sleep(1/100)

if __name__ == "__main__":
    main()


