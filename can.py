__author__ = 'mw'

import socket
import struct
import threading
import queue
from enum import Enum


class Can(object):
    def __init__(self, interface):
        self.queue_send = queue.Queue()
        self.queue_debug = queue.Queue()
        self.can_frame_fmt = "=IB3x8s"
        self.packer = CanPacker()
        self.socket = socket.socket(socket.AF_CAN, socket.SOCK_RAW, socket.CAN_RAW)
        can_filter, can_mask = 0x600, 0x600
        can_filter = struct.pack("=II", can_filter, can_mask)
        self.socket.setsockopt(socket.SOL_CAN_RAW, socket.CAN_RAW_FILTER, can_filter)
        self.socket.bind((interface, ))
        self.t_recv_connection = threading.Thread(target=self.recv_connection)
        self.t_recv_connection.setDaemon(1)
        self.t_recv_connection.start()
        self.t_send_connection = threading.Thread(target=self.send_connection)
        self.t_send_connection.setDaemon(1)
        self.t_send_connection.start()

    def build_can_frame(self, can_id, data):
        can_dlc = len(data)
        data = data.ljust(8, b'\x00')
        return struct.pack(self.can_frame_fmt, can_id, can_dlc, data)

    def dissect_can_frame(self, frame):
        can_id, can_dlc, data = struct.unpack(self.can_frame_fmt, frame)
        return can_id, data[:can_dlc]

    def recv_can(self):
        frame, addr = self.socket.recvfrom(16)
        can_id, can_msg = self.dissect_can_frame(frame)
        return can_id, can_msg

    def send_can(self, can_id, can_msg):
        frame = self.build_can_frame(can_id, can_msg)
        self.socket.send(frame)

    def recv_connection(self):
        while 1:
            can_id, can_msg = self.recv_can()
            #msg_frame = self.packer.unpack(can_id, can_msg)
            self.queue_debug.put_nowait((can_id, can_msg.decode('latin-1')))     # Todo:überprüffen ob voll

    def send_connection(self):
        while 1:
            can_id, can_msg = self.queue_send.get()
            self.send_can(can_id, can_msg)

    def send(self, can_id, can_msg):
        self.queue_send.put_nowait((can_id, can_msg))


class CanPacker(object):
    def __init__(self):
        self.unpacker = {
            MsgTypes.Position_Robot_1: self.unpack_position_protocol,
            MsgTypes.Position_Robot_2: self.unpack_position_protocol,
            MsgTypes.Position_Enemy_1: self.unpack_position_protocol,
            MsgTypes.Position_Enemy_2: self.unpack_position_protocol
        }

        self.packer = {
            MsgTypes.Position_Robot_1: self.pack_position_protocol,
            MsgTypes.Position_Robot_2: self.pack_position_protocol,
            MsgTypes.Position_Enemy_1: self.pack_position_protocol,
            MsgTypes.Position_Enemy_2: self.pack_position_protocol
        }

    def pack(self, msg_frame):
        protocol = self.packer[msg_frame['type']]
        can_msg = protocol(msg_frame)
        priority = 0x3  # Todo: unterscheiden zwischen debug und normal
        sender = MsgSender.Hauptsteuerung.value
        can_id = (priority << 9) + (msg_frame['type'].value << 3) + sender
        return can_id, can_msg

    #def unpack(self, can_id, can_msg):
    #    mask = 0b00111111000
    #    type_nr = (can_id & mask) >> 3
    #    msg_type = MsgTypes(type_nr)
    #    protocol = self.unpacker[msg_type]
    #    msg_frame = protocol(can_msg)
    #    msg_frame['type'] = msg_type
    #    sender = can_id & 0b00000000111
    #    msg_frame['sender'] = MsgSender(sender)
    #    return msg_frame

    def unpack(self, can_id, can_msg):
        #mask = 0b00111111000
        #type_nr = (can_id & mask) >> 3
        #msg_type = MsgTypes(type_nr)
        protocol = MsgEncoding.Position_Robot_1.value
        encoding, dictionary = protocol.value
        data = struct.unpack(encoding, can_msg)
        msg_frame = {}
        for i, line in enumerate(data):
            if not isinstance(dictionary[i], str):
                booleans = self.decode_booleans(line, len(dictionary[i]))
                for ii, bool_value in enumerate(booleans):
                    msg_frame[dictionary[i][ii]] = bool_value
            else:
                msg_frame[dictionary[i]] = line
        return msg_frame

    def pack_position_protocol(self, msg_frame):
        packer = struct.Struct('!BHHH')
        data_correct = self.encode_booleans((msg_frame['angle_correct'], msg_frame['position_correct']))
        can_msg = packer.pack(data_correct, msg_frame['angle'], msg_frame['y_position'], msg_frame['x_position'])
        return can_msg

    def unpack_position_protocol(self, msg):
        packer = struct.Struct('!BHHH')
        data = packer.unpack(msg)
        data_correct, angle, y_position, x_position = data
        position_is_correct, angle_is_correct = self.decode_booleans(data_correct, 2)
        msg_dict = {
            'position_correct': position_is_correct,
            'angle_correct': angle_is_correct,
            'angle': angle,
            'y_position': y_position,
            'x_position': x_position,
        }
        return msg_dict

    @staticmethod
    def encode_booleans(bool_lst):
        res = 0
        for i, bval in enumerate(reversed(bool_lst)):
            res += int(bval) << i
        return res

    @staticmethod
    def decode_booleans(intval, bits):
        res = []
        for bit in reversed(range(bits)):
            mask = 1 << bit
            res.append((intval & mask) == mask)
        return res


class MsgTypes(Enum):
    EmergencyShutdown = 0
    Emergency_Stop = 1
    Game_End = 2
    Position_Robot_1 = 3
    Position_Robot_2 = 4
    Position_Enemy_1 = 5
    Position_Enemy_2 = 6
    Close_Range_Dedection = 7
    Goto_Position = 8
    Drive_Status = 9


class MsgSender(Enum):
    Hauptsteuerung = 0
    Navigation = 1
    Antrieb = 2
    Peripherie = 3
    Debugging = 7


class EncodingTypes(Enum):
    #position_protocol = ('!BHHH', ('x_position', 'y_position', 'angle', ('position_correct', 'angle_correct')))
    position_protocol = ('!BHHH', (('angle_correct', 'position_correct'), 'angle', 'y_position', 'x_position'))


class MsgEncoding(Enum):
    Position_Robot_1 = EncodingTypes.position_protocol
    Position_Robot_2 = EncodingTypes.position_protocol
    Position_Enemy_1 = EncodingTypes.position_protocol
    Position_Enemy_2 = EncodingTypes.position_protocol