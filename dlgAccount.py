import os
import webbrowser
from PyQt5 import QtCore
from PyQt5.QtWidgets import QWidget, QGridLayout, QHBoxLayout, QVBoxLayout, QScrollArea, QPushButton, QLineEdit, QGroupBox, QLabel, QMessageBox
from PyQt5.QtGui import QIcon
import dlgMenu
import dlgLoginUrl
from comSwitch import MySwitch
import connectDB
import global_var

#import websockets.legacy.server
#import websockets.legacy.client
from td.client import TDClient

class HomeWindow(QWidget):
    switch_menu = QtCore.pyqtSignal()
    ctrl_delete_project = 0
    projectmodel = []
    projectLayout = {}
    accountLayout = {}

    def __init__(self):
        super().__init__()
        global_var.opendDlg = True

        self.projectmodel = connectDB.getProject()

        mainLayout = QGridLayout()
        self.createTopToolbar()
        mainLayout.setColumnStretch(0, 1)
        mainLayout.addLayout(self.topLayout, 1, 1)
        
        listBox = QVBoxLayout()
        scroll = QScrollArea()
        listBox.addWidget(scroll)
        scroll.setWidgetResizable(True)
        scrollContent = QWidget(scroll)
        self.scrollLayout = QVBoxLayout(scrollContent)
        scrollContent.setLayout(self.scrollLayout)
        for x in self.projectmodel:
            self.scrollLayout.addWidget(self.createProjectGroupBox(x['pk'], x['is_allow'], x['users'], "Project "+str(x['vindex']+1)))
        #self.scrollLayout.addStretch(1)
        scroll.setWidget(scrollContent)
        mainLayout.addLayout(listBox, 0, 0, 1, 2)

        self.setLayout(mainLayout)
        self.resize(900, 768)
        self.setWindowTitle("TRADE COPIER - TRADE ACCOUNT")

    def createTopToolbar(self):
        self.topLayout = QHBoxLayout()
        addAccountBtn = QPushButton("&Add Project")
        addAccountBtn.setFixedHeight(32)
        # addAccountBtn.setFixedWidth(160)
        addAccountBtn.setStyleSheet("background-color : {color}; color: #FFF; font-weight: bold; font-size: 18px;".format(color=global_var.color_blue))
        addAccountBtn.clicked.connect(self.createProject)
        self.topLayout.addWidget(addAccountBtn)
        menuBtn = QPushButton("&Back")
        menuBtn.setFixedHeight(32)
        # menuBtn.setFixedWidth(160)
        menuBtn.setStyleSheet("background-color : {color}; color: #FFF; font-weight: bold; font-size: 18px;".format(color=global_var.color_grey))
        self.switch_menu.connect(self.toMenu)
        menuBtn.clicked.connect(self.switch_menu.emit)
        self.topLayout.addWidget(menuBtn)
        self.topLayout.addStretch(1)
    
    def createProjectGroupBox(self, pm_proj_id, allow, users, title="Project"):
        newProject = QGroupBox(title)
        newProject.setStyleSheet("color: #FFF; font-weight: bold; font-size: 20px;")
        self.projectLayout[pm_proj_id] = QVBoxLayout()
        btnLayout = QHBoxLayout()
        allowBtn = MySwitch(72, 28, 13, 34)
        if allow == 1:
            allowBtn.setChecked(True)
        else:
            allowBtn.setChecked(False)
        allowBtn.clicked.connect(lambda: self.changeAllowProject(pm_proj_id, allowBtn.isChecked()))
        delProjBtn = QPushButton("")
        delProjBtn.setFixedHeight(32)
        delProjBtn.setFixedWidth(40)
        delProjBtn.setStyleSheet("background-color : {color}; color: #FFF; font-weight: bold; font-size: 18px;".format(color=global_var.color_red))
        delProjBtn.setToolTip("Delete Project")
        delProjBtn.setIcon(QIcon('delete.png'))
        delProjBtn.clicked.connect(lambda: self.deleteProject(pm_proj_id))
        addAccBtn = QPushButton("")
        addAccBtn.setFixedHeight(32)
        addAccBtn.setFixedWidth(40)
        addAccBtn.setToolTip("Add Account")
        addAccBtn.setIcon(QIcon('create.png'))
        addAccBtn.setStyleSheet("background-color : {color}; color: #FFF; font-weight: bold; font-size: 18px;".format(color=global_var.color_blue))
        addAccBtn.clicked.connect(lambda: self.createAccount(pm_proj_id))
        btnLayout.addStretch(1)
        btnLayout.addWidget(allowBtn)
        btnLayout.addWidget(addAccBtn)
        btnLayout.addWidget(delProjBtn)
        self.projectLayout[pm_proj_id].addLayout(btnLayout)
        index = 0
        if len(users) > 0 :
            for x in users:
                if x['is_main'] == 0:
                    index = index + 1
                self.projectLayout[pm_proj_id].addWidget(self.createAccountGroupBox(x, index))
        
        newProject.setLayout(self.projectLayout[pm_proj_id])
        return newProject

    def createAccountGroupBox(self, usermeta, index=1):
        title = "Sub Account"+str(index)
        if usermeta['is_main'] == 1:
            title = "Main Account"
        self.accountLayout[usermeta['id']] = QGroupBox(title)
        self.accountLayout[usermeta['id']].setStyleSheet("color: #FFF; font-weight: bold; font-size: 14px;")
        #newAccount.setCheckable(True)
        #newAccount.setChecked(True)

        nameEdit = QLineEdit(usermeta['acc_name'])
        nameEdit.setFixedHeight(28)
        nameEdit.setStyleSheet("font-size: 18px; color: #000; font-weight: normal;")
        nameEdit.editingFinished.connect(lambda: self.changeUsermeta(nameEdit.text(), 'acc_name', usermeta['id']))
        nameLabel = QLabel("Account Name:")
        nameLabel.setStyleSheet("font-size: 16px;")
        leverageEdit = QLineEdit(usermeta['leverage'])
        leverageEdit.setFixedHeight(28)
        leverageEdit.setStyleSheet("font-size: 18px; color: #000; font-weight: normal;")
        leverageEdit.editingFinished.connect(lambda: self.changeUsermeta(leverageEdit.text(), 'leverage', usermeta['id']))
        leverageLabel = QLabel("Leverage:")
        leverageLabel.setStyleSheet("font-size: 16px;")
        spreadEdit = QLineEdit(usermeta['spread'])
        spreadEdit.setFixedHeight(28)
        spreadEdit.setStyleSheet("font-size: 18px; color: #000; font-weight: normal;")
        spreadEdit.editingFinished.connect(lambda: self.changeUsermeta(spreadEdit.text(), 'spread', usermeta['id']))
        spreadLabel = QLabel("Spread:")
        spreadLabel.setStyleSheet("font-size: 16px;")
        spreadSwitch = MySwitch(66, 22, 10, 32)
        if int(usermeta['auto_spread']) == 1:
            spreadSwitch.setChecked(True)
        else:
            spreadSwitch.setChecked(False)
        spreadSwitch.clicked.connect(lambda: self.changeAutoSpreadAccount(usermeta['id'], spreadSwitch.isChecked()))
        spreadLayout = QHBoxLayout()
        spreadLayout.addWidget(spreadLabel)
        spreadLayout.addWidget(spreadEdit)
        spreadLayout.addWidget(spreadSwitch)
        
        balanceEdit = QLineEdit(usermeta['max_balance'])
        balanceEdit.setFixedHeight(18)
        balanceEdit.setStyleSheet("font-size: 13px; color: #000; font-weight: normal;")
        balanceEdit.editingFinished.connect(lambda: self.changeUsermeta(balanceEdit.text(), 'max_balance', usermeta['id']))
        balanceLabel = QLabel("Maximum Balance:")
        balanceLabel.setStyleSheet("font-size: 12px;")
        maxfirstentryEdit = QLineEdit(usermeta['max_first_entry'])
        maxfirstentryEdit.setFixedHeight(18)
        maxfirstentryEdit.setStyleSheet("font-size: 13px; color: #000; font-weight: normal;")
        maxfirstentryEdit.editingFinished.connect(lambda: self.changeUsermeta(maxfirstentryEdit.text(), 'max_first_entry', usermeta['id']))
        maxfirstentryLabel = QLabel("Max First Entry:")
        maxfirstentryLabel.setStyleSheet("font-size: 12px;")
        keyEdit = QLineEdit(usermeta['client_id'])
        keyEdit.setFixedHeight(18)
        keyEdit.setStyleSheet("font-size: 13px; color: #000; font-weight: normal;")
        keyEdit.editingFinished.connect(lambda: self.changeUsermeta(keyEdit.text(), 'client_id', usermeta['id']))
        keyLabel = QLabel("Client ID:")
        keyLabel.setStyleSheet("font-size: 12px;")

        ctrlBtnLayout = QHBoxLayout()
        onoffLabel = QLabel("Copy:")
        onoffLabel.setStyleSheet("font-size: 16px;")
        allowBtn = MySwitch(72, 26, 12, 34)
        if usermeta['is_allow'] == 1:
            allowBtn.setChecked(True)
        else:
            allowBtn.setChecked(False)
        allowBtn.clicked.connect(lambda: self.changeAllowAccount(usermeta['id'], allowBtn.isChecked()))
        registerBtn = QPushButton("")
        registerBtn.setFixedHeight(24)
        # registerBtn.setFixedWidth(160)
        registerBtn.setStyleSheet("background-color : {color}; color: #FFF; font-weight: bold; font-size: 18px;".format(color=global_var.color_blue))
        registerBtn.setToolTip("Register")
        registerBtn.setIcon(QIcon('register.png'))
        registerBtn.clicked.connect(lambda: self.registerAccount(usermeta['id']))
        deleteBtn = QPushButton("")
        deleteBtn.setFixedHeight(24)
        # deleteBtn.setFixedWidth(160)
        deleteBtn.setStyleSheet("background-color : {color}; color: #FFF; font-weight: bold; font-size: 18px;".format(color=global_var.color_red))
        deleteBtn.setToolTip("Delete")
        deleteBtn.setIcon(QIcon('delete.png'))
        deleteBtn.clicked.connect(lambda: self.deleteAccount(usermeta['project_id'], usermeta['id']))
        ctrlBtnLayout.addWidget(onoffLabel)
        ctrlBtnLayout.addWidget(allowBtn)
        ctrlBtnLayout.addWidget(registerBtn)
        ctrlBtnLayout.addWidget(deleteBtn)

        layout = QGridLayout()
        layout.addWidget(nameLabel, 0, 0, 1, 2)
        layout.addWidget(nameEdit, 0, 2, 1, 2)
        layout.addWidget(leverageLabel, 0, 4, 1, 1)
        layout.addWidget(leverageEdit, 0, 5, 1, 1)
        layout.addLayout(spreadLayout, 0, 6, 1, 3)
        layout.addLayout(ctrlBtnLayout, 0, 9, 1, 3)

        layout.addWidget(balanceLabel, 1, 0, 1, 2)
        layout.addWidget(balanceEdit, 1, 2, 1, 1)
        layout.addWidget(maxfirstentryLabel, 1, 3, 1, 2)
        layout.addWidget(maxfirstentryEdit, 1, 5, 1, 1)
        layout.addWidget(keyLabel, 1, 6, 1, 1)
        layout.addWidget(keyEdit, 1, 7, 1, 4)

        self.accountLayout[usermeta['id']].setLayout(layout)
        return self.accountLayout[usermeta['id']]

    def toMenu(self):
        self.tgt = dlgMenu.MenuWindow()
        self.hide()
        self.tgt.show()
    
    def closeEvent(self, event):
        self.hide()
        global_var.opendDlg = False
        event.ignore()

    def createProject(self):
        id = connectDB.createProject()
        userid = connectDB.createUser(id, 1)
        users = [{
            'id':userid,
            'project_id':id,
            'acc_name':'',
            'client_id':'',
            'max_balance':'',
            'leverage':'1',
            'spread':'',
            'auto_spread':0,
            'max_first_entry':'',
            'is_main':1,
            'is_allow':1,
            'vindex':0
        }]
        self.projectmodel.append({
            'pk':id,
            'is_allow':1,
            'vindex':len(self.projectmodel),
            'users':users
        })
        self.scrollLayout.addWidget(self.createProjectGroupBox(id, 1, users, "Project "+str(len(self.projectmodel))))

    def changeAllowProject(self, pk, val):
        if val:
            connectDB.updateProject(pk, 'is_allow', 1)
        else:
            connectDB.updateProject(pk, 'is_allow', 0)

    def deleteProject(self, pk):
        self.ctrl_delete_project = pk
        qm = QMessageBox()
        ret = qm.question(self,'', "Are you sure to delete this project?", qm.Yes | qm.No)
        if ret == qm.Yes:
            connectDB.deleteUsersByPrjId(pk)
            connectDB.deleteProject(pk)
            index = 0
            match = 0
            flag = False
            for x in self.projectmodel:
                print("{index} - {m} - {std}".format(index=index, m=x['pk'], std=pk))
                if x['pk'] == pk:
                    print('-'*80)
                    print(index)
                    print('-'*80)
                    self.scrollLayout.itemAt(index).widget().setParent(None)
                    flag = True
                    match = index
                if flag:
                    x['vindex'] = x['vindex']-1
                index = index + 1
            if flag:
                self.projectmodel = self.projectmodel[:match] + self.projectmodel[match+1:]
    

    def createAccount(self, prj_id):
        is_main = 0
        if connectDB.hasMainAccount(prj_id) == None:
            userid = connectDB.createUser(prj_id, 1)
            is_main = 1
        else:
            userid = connectDB.createUser(prj_id, 0)
        user = {
            'id':userid,
            'project_id':prj_id,
            'acc_name':'',
            'client_id':'',
            'max_balance':'',
            'leverage':'1',
            'spread':'',
            'auto_spread':0,
            'max_first_entry':'',
            'is_main':is_main,
            'is_allow':1,
            'vindex':0
        }
        index = 0
        for x in self.projectmodel:
            if x['pk'] == prj_id:
                user['vindex'] = len(self.projectmodel[index]['users'])
                self.projectmodel[index]['users'].append(user)
                self.projectLayout[prj_id].addWidget(self.createAccountGroupBox(user, user['vindex']))
            index = index + 1
        
    def changeAllowAccount(self, pk, val):
        if val:
            connectDB.updateUser(pk, 'is_allow', 1)
        else:
            connectDB.updateUser(pk, 'is_allow', 0)
    
    def changeAutoSpreadAccount(self, pk, val):
        if val:
            connectDB.updateUser(pk, 'auto_spread', 1)
        else:
            connectDB.updateUser(pk, 'auto_spread', 0)

    def deleteAccount(self, prj_id, userid):
        qm = QMessageBox()
        ret = qm.question(self,'', "Are you sure to delete this account?", qm.Yes | qm.No)
        if ret == qm.Yes:
            index = -1
            k = 0
            for x in self.projectmodel:
                if x['pk'] == prj_id:
                    index = k
                    break
                k = k + 1
            if index != -1:
                k = 0
                uindex = -1
                for x in self.projectmodel[index]['users']:
                    if x['id'] == userid:
                        self.projectmodel[index]['users'] = self.projectmodel[index]['users'][:k]+self.projectmodel[index]['users'][k+1:]
                        self.accountLayout[userid].setParent(None)
                        connectDB.deleteUser(userid)
                        uindex = k
                    k = k + 1
                if uindex != -1:
                    for x in range(uindex, len(self.projectmodel[index]['users'])):
                        self.projectmodel[index]['users'][x]['vindex'] = self.projectmodel[index]['users'][x]['vindex'] - 1

    def changeUsermeta(self, text, column, userid):
        connectDB.updateUser(userid, column, text)
    
    def registerAccount(self, userid):
        global_var.current_login_userid = userid
        user = connectDB.getUser(userid)
        client_id = user['client_id']
        TDSession = TDClient(
            client_id=client_id,
            redirect_uri='http://127.0.0.1:3000',
            credentials_path='./token/'+client_id+'.json'
        )

        if(os.path.isfile(TDSession.credentials_path) and TDSession._silent_sso()):
            TDSession.authstate = True
            QMessageBox.about(self, "Status", "You are registered.")
        else:
            url = TDSession.grab_url()
            webbrowser.get().open(url)
            self.w = dlgLoginUrl.LoginUrlWindow()
            self.w.show()

