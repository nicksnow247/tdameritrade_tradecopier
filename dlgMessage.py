from PyQt5 import QtCore
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QDesktopWidget, QWidget, QVBoxLayout, QHBoxLayout, QLabel

import global_var

def filterChar(a):
    b = ''
    c = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '-', '.']
    f = 0
    for x in a:
        if x in c:
            if x == '.':
                if f == 1:
                    return ''
                f = 1
            if x == '-':
                if b != '':
                    return ''
            b = b + x
    return b

def removeSameCategMessage(key, myhash):
    if key is None:
        return
    keys = list(global_var.messages.keys())
    for x in keys:
        f = 1
        for y in key:
            if y not in global_var.messages[x] or global_var.messages[x][y] != key[y]:
                f = 0
        if f == 1 and x != myhash:
            global_var.messages.pop(x, None)

class MessageWindow(QWidget):
    switch_menu = QtCore.pyqtSignal()
    switch_profit = QtCore.pyqtSignal()
    switch_stoploss = QtCore.pyqtSignal()
    title = ''
    dlghash = ''
    duration = 0
    removecateg = None

    def __init__(self, title, backcolor=global_var.color_info_back, dlghash=None, duration=0, categ=None):
        super().__init__()
        global_var.opendDlg = True
        self.dlghash = dlghash
        self.removecateg = categ
        tduration = str(duration)
        tduration = filterChar(tduration)
        if tduration == '':
            self.duration = 0
        else:
            self.duration = float(tduration)
        mainLayout = QVBoxLayout()

        hlay1 = QHBoxLayout()
        titleLabel = QLabel(title)
        titleLabel.setStyleSheet("font-size: 16px;")
        self.title = title
        hlay1.addWidget(titleLabel, 1)
        mainLayout.addLayout(hlay1)

        self.setLayout(mainLayout)
        self.resize(320, 80)

        ag = QDesktopWidget().availableGeometry()
        sg = QDesktopWidget().screenGeometry()
        widget = self.geometry()
        x = ag.width() - widget.width()
        y = 2 * ag.height() - sg.height() - widget.height()
        self.move(x, y)

        self.setStyleSheet("background-color: {color};".format(color=backcolor))
        self.setWindowTitle("TRADE COPIER - NOTIFICATION")

        self.timer_act = QTimer(self)
        self.timer_act.timeout.connect(self.onTimerAct)
        self.timer_act.start(200)

        if self.duration != 0:
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.onTimer)
            self.timer.start(self.duration*1000)
    
    def onTimerAct(self):
        self.activateWindow()
        self.timer_act.stop()

    def onTimer(self):
        if self.dlghash is not None:
            removeSameCategMessage(self.removecateg, self.dlghash)
            if self.dlghash in global_var.messages:
                global_var.messages[self.dlghash]['opened'] = 0
            # global_var.messages.pop(self.dlghash, None)
        global_var.opendDlg = False
        self.hide()
        self.timer.stop()
    
    # def hideMyDlg(self):
    #     global_var.opendDlg = False
    #     self.hide()

    def closeEvent(self, event):
        self.hide()
        if self.dlghash is not None:
            removeSameCategMessage(self.removecateg, self.dlghash)
            if self.dlghash in global_var.messages:
                global_var.messages[self.dlghash]['opened'] = 0
            # global_var.messages.pop(self.dlghash, None)
        global_var.opendDlg = False
        print(global_var.messages)
        event.ignore()

