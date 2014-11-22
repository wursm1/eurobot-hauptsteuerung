__author__ = 'mw'

from PyQt4 import QtGui, QtCore

import ethernet
import datetime
import can
import copy


class Table(QtGui.QTableWidget):
    def __init__(self, header):
        super().__init__(1, len(header))
        self.setHorizontalHeaderLabels(header)
        self.verticalHeader().setVisible(False)
        #self.resizeColumnsToContents()
        #self.resizeRowsToContents()

    def add_row(self, data, color, autoscroll):
        max_row_count = 10000
        row_count = self.rowCount()
        self.hideRow(row_count)
        row_count += 1
        self.setRowCount(row_count)
        for i in range(len(data)):
            newitem = QtGui.QTableWidgetItem(data[i])
            if color is not None:
                red, green, blue = color
                newitem.setBackground(QtGui.QColor(red, green, blue))
            self.setItem(row_count - 2, i, newitem)
        if row_count > max_row_count:
            self.removeRow(0)
        self.showColumn(row_count)
        if autoscroll is True:
            slide_bar = self.verticalScrollBar()
            slide_bar.setValue(slide_bar.maximum())
        print(row_count)


class CanTableControl(QtGui.QWidget):
    def __init__(self):
        super().__init__()
        self.running = False
        self.autoscroll_box = QtGui.QCheckBox('Autoscroll')
        self.run_button = QtGui.QPushButton('run')
        self.run_button.setCheckable(True)
        #self.connect(autoscroll_box, QtCore.SIGNAL('stateChanged(int)'), self.table.change_autoscroll)
        self.colors = {
            can.MsgTypes.Position_Robot_1: (0, 255, 0),
            can.MsgTypes.Position_Robot_2: (255, 0, 0),
            can.MsgTypes.Position_Enemy_1: (255, 0, 0),
            can.MsgTypes.Position_Enemy_2: (255, 0, 0)
        }

        grid = QtGui.QGridLayout()
        grid.setSizeConstraint(QtGui.QLayout.SetMinAndMaxSize)
        grid.addWidget(self.autoscroll_box, 0, 0)
        grid.addWidget(self.run_button, 0, 1)

        self.type_chechboxes = []
        for i, msg_type in enumerate(can.MsgTypes):
            checkbox = QtGui.QCheckBox(msg_type.name)
            checkbox.setChecked(True)
            self.type_chechboxes.append(checkbox)
            grid.addWidget(checkbox, i / 2 + 1, i % 2)
        self.setLayout(grid)

    def test(self):
        self.running = True

    def add_data(self, msg_frame):
        msg_frame_copy = copy.copy(msg_frame)
        if self.run_button.isChecked():
            if self.type_chechboxes[msg_frame_copy['type'].value].isChecked():
                table_sender = str(msg_frame_copy['sender'])
                table_type = str(msg_frame_copy['type'].name)
                table_color = self.colors[msg_frame_copy['type']]
                del msg_frame_copy['type']
                del msg_frame_copy['sender']
                table_msg = str(msg_frame_copy)
                current_time = datetime.datetime.now().strftime("%M:%S.%f")[0:-3]
                new_row = [current_time, table_sender, table_type, table_msg]

                self.emit(QtCore.SIGNAL('new_can_Table_Row'), new_row, table_color, self.autoscroll_box.isChecked())


class EditHost(QtGui.QWidget):
    def __init__(self):
        super().__init__()
        host_label = QtGui.QLabel('Host:')
        self.host_line = QtGui.QLineEdit('localhost')
        port_label = QtGui.QLabel('Port:')
        self.port_line = QtGui.QLineEdit('42233')
        self.host_button = QtGui.QPushButton('Connect')

        grid = QtGui.QGridLayout()
        grid.addWidget(host_label, 0, 0)
        grid.addWidget(self.host_line, 0, 1)
        grid.addWidget(port_label, 1, 0)
        grid.addWidget(self.port_line, 1, 1)
        grid.addWidget(self.host_button, 1, 2)
        self.setLayout(grid)


class TcpConnection(QtCore.QThread):
    def __init__(self, host, port):
        QtCore.QThread.__init__(self)
        self.packer = can.CanPacker()
        self.host = host
        self.port = port

    def run(self):
        tcp = ethernet.Client(self.host, int(self.port))
        while True:
            data = tcp.read_block()
            if tcp.connected is False:
                break
            can_id = data[0]
            can_msg = data[1].encode('latin-1')
            msg_frame = self.packer.unpack(can_id, can_msg)
            self.emit(QtCore.SIGNAL('tcp_data'), msg_frame)
        self.emit(QtCore.SIGNAL('tcp connection lost'))


class SendCan(QtGui.QWidget):
    def __init__(self):
        super().__init__()
        self.msg_type_label = QtGui.QLabel('Message Type:')
        self.msg_label = QtGui.QLabel('Message:')
        self.msg_line_label = QtGui.QLineEdit('123456')
        self.msg_type_combo = QtGui.QComboBox()
        msg_types = ["Game_end", "Position", "Close_range_dedection", "Goto_position"]
        self.msg_type_combo.addItems(msg_types)

        hbox = QtGui.QHBoxLayout()
        for i in range(2):
            line = QtGui.QLineEdit('123')
            hbox.addWidget(line)

        grid = QtGui.QGridLayout()
        grid.addWidget(self.msg_type_label, 0, 0)
        grid.addWidget(self.msg_type_combo, 0, 1)

        vbox = QtGui.QVBoxLayout()
        vbox.addLayout(grid)
        vbox.addLayout(hbox)

        self.setLayout(vbox)
