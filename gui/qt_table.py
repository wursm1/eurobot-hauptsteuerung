__author__ = 'mw'

from PyQt4 import QtGui, QtCore


class Table(QtGui.QTableWidget):
    def __init__(self, header):
        super().__init__(1, len(header))
        self.header = header
        self.setHorizontalHeaderLabels(header)
        self.verticalHeader().setVisible(False)
        #self.resizeColumnsToContents()
        #self.resizeRowsToContents()

    def add_row(self, data):
        row_count = self.rowCount()
        row_count += 1
        self.setRowCount(row_count)
        self.hideRow(row_count - 1)
        for i in range(len(data)):
            newitem = QtGui.QTableWidgetItem(data[i])
            self.setItem(row_count - 2, i, newitem)
        slide_bar = self.verticalScrollBar()
        slide_bar.setValue(slide_bar.maximum())
        self.showColumn(row_count)
        print(row_count)


class EditHost(QtGui.QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        host_label = QtGui.QLabel('Host:')
        self.host_line = QtGui.QLineEdit('localhost')
        port_label = QtGui.QLabel('Port:')
        self.port_line = QtGui.QLineEdit('42233')
        host_button = QtGui.QPushButton('Connect')
        host_button.clicked.connect(self.connect_host)

        grid = QtGui.QGridLayout()
        grid.addWidget(host_label, 0, 0)
        grid.addWidget(self.host_line, 0, 1)
        grid.addWidget(port_label, 1, 0)
        grid.addWidget(self.port_line, 1, 1)
        grid.addWidget(host_button, 1, 2)
        self.setLayout(grid)

    def connect_host(self):
        if self.parent.connected is False:
            self.parent.connect_host(self.host_line.text(), self.port_line.text())
        else:
            print("Already connected")