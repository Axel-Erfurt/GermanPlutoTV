#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys 
import requests
import time
import requests
from datetime import datetime, timedelta
import locale
from datetime import date
from PyQt5.QtWidgets import QMainWindow, QWidget, QApplication, QAction, QToolBar, QLineEdit
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings
from bs4 import BeautifulSoup

chList = ['Pluto TV Kids', 'Pluto TV History+', 'Pluto TV Animals+', 'Pluto TV Inside+', 'World Poker Tour', 'FailArmy', 'Pluto TV Explore', 'Pluto TV Sports', 'IGN', 'MinecrafTV', 'Pluto TV Fight', 'Glory Kickboxing', 'MST3K', 'The Pet Collective', 'Rifftrax', 'Action Sports', 'Fireplace', 'Pluto TV Nature', 'Pluto TV Movies', 'MTV Pluto TV', 'MTV The Shores', 'MTV Dating', 'The Asylum Channel', 'Pluto TV Kids Jr.', 'Pluto TV Sitcoms+', 'Pluto TV Indies', 'Ice Pilots', 'MTV Christmas Songs', 'MTV Teen Mom', 'MTV The Hills', 'SpongeBob Schwammkopf', 'Pluto TV Movies+(DE)', 'Pluto TV Surf', 'CC Pluto TV', 'CC Made in Germany', 'Totally Turtles', 'Slow TV', 'Pluto TV Mistletoe', 'Pluto TV Sitcoms', 'Pluto TV Animals', 'Pluto TV History', 'Pluto TV Inside', 'Pluto TV Dogs', 'Pluto TV Documentaries', 'Pluto TV Lives', 'Pluto TV Cats 24/7', 'MTV Catfish TV Show', 'Inspector Gadget', 'Simsalabim Sabrina', 'Mario vs. Sonic', 'Pluto TV Drama', 'Pluto TV Food', 'Pluto TV Romance', 'Pluto TV Christmas', 'Unbeaten Esports', 'Pluto TV Family', 'Comedy Central+', 'MTV Pluto TV+', 'Pluto TV Drama+', 'Pluto TV Retro Drama', 'Strongman', 'Pluto TV Retro Toons', 'Pluto TV Comedy', 'Pluto TV Thrillers', 'Dora TV', 'Being Human', 'Pluto TV Crime', 'MTV Catfish TV Show+', 'CC Made in Germany+', 'Sanctuary', 'Dark Matter', 'Pluto TV Fitness', 'Pluto TV Yoga', 'Beyblade Burst', "Blue's Clues", 'iCarly', 'Bubble Guppies', 'Sam & Cat', 'Victorious', 'Blaze', 'Pluto TV Chefkoch', 'MTV Teen (OV)', 'MTV Dating (OV)', 'MTV The Hills (OV)', 'MTV Cribs', 'Totally Turtles (OV)', 'People are Awesome', 'Pluto TV Home', 'Wipeout (OV)', 'Nick Rewind', 'Nick Pluto TV', 'Nick Jr. Pluto TV', 'Auction Hunters', 'Storage Wars', 'MTV Cribs+', 'Insight TV', 'Teen Nick', 'InWonder', 'InTrouble', 'Focus TV Reportage', 'Nick Pluto TV+', 'Nick Rewind+', 'Spongebob Schwammkopf+', 'iCarly+', 'Emma, einfach magisch!', 'Auto Motor Sport', 'Nick Christmas', 'Holiday Lights', 'Beat Club', 'Pluto TV Paranormal']

class Grabber():

    def __init__(self):
        ### html header
        self.header = """<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
                      <html><head><meta name="qrichtext" content="1" /><meta http-equiv="Content-Type" \
                      content="text/html; charset=UTF-8" /><style type="text/css">
                      p, li { white-space: pre-wrap; }
                      </style></head>
                      <style>
                      table {width: auto; \
                      background-color: #2e3436; margin-top: 10px;}
                      th  {padding-left:10px; color: #729fcf;}   
                      td {padding-left:10px; padding-right:10px; \
                      color: #d3d7cf; overflow:hidden; table-layout:fixed;}
                      body {width: 700px; margin: 12px; background-color: #2e3436;font-family:'Helvetica'; \
                      font-size: 100%; font-weight:400;}
                      hr {border-style: ridge;}</style>"""

        ### html body
        self.body = "</p></body></html>"

        loc = locale.getlocale()
        locale.setlocale(locale.LC_ALL, loc)
        self.dt = f"{date.today():%A, %-d.%B %Y}"
        self.titleList = []
        
        now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.000Z')
        later = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%S.000Z')


        myday = f"{date.today():%d}"
        print("Tag:", self.dt)

        ### json von Hoerzu laden
        url = f"http://api.pluto.tv/v2/channels?start={now}&stop={later}"
        self.response = requests.get(url)
        
        ### to json 
        self.data = self.response.json() 


    ### Daten jedes in dictList enthaltenen Senders verarbeiten und zu HTML konvertieren
    def getValues(self, id):                                                
        for i in self.data:
            if i['name'] == id:
                
                pmdlist = []
                pr = i['timelines']
                for a in pr:
                    title = a.get('title')
                    st = a.get('start')
                    start = st[11:16]
                    self.titleList.append("<tr>")
                    self.titleList.append("<td>")                
                    pmd = f"{start}&emsp;{title}<br>" 
                    pmdlist.append(pmd) 
                
                pmld = '\n'.join(pmdlist)
                
                self.titleList.append(f'<table>')
                                    
                self.titleList.append(f"<tr><td>{pmld}</td></tr></table>")

    ### Gesamtliste erstellen
    def makeList(self):
        print("Kanäle:", len(chList))
        self.titleList.append(self.header)
        m = f"<font color='#729fcf'><h4><i>{self.dt}</i></h4></font>"
        self.titleList.append(f'<p style="font-size: 30px; \
                            line-height: 1px; color: #babdb6;text-shadow: \
                            1px 1px 1px #555753;">TV Programm</p>')
        self.titleList.append(m)
        
        i = 0
        for ch in chList:
            self.titleList.append(f'<font color="#729fcf"><h2 padding-bottom="0" margin-bottom="0" \
                             id="{ch}"><a href="#"></a>&nbsp;&nbsp;&nbsp;&nbsp;{ch} \
                             &nbsp;&nbsp;&nbsp;&nbsp;<a href="#"></a></h2></font>')
            i += 1
            self.getValues(ch)
        
        
        self.titleList.append(self.body)
        t = '\n'.join(self.titleList)

        return t
##################################################################

class Browser(QMainWindow):
 
    def __init__(self):
      QMainWindow.__init__(self)
      
      self.grabber = Grabber()
      self.stationActs = []
    
      self.setGeometry(0, 0, 1000, 950)
 
      self.html = QWebEngineView()
      self.html.page().settings().setAttribute(QWebEngineSettings.ShowScrollBars,False)
      self.setCentralWidget(self.html)
      
      self.my_html = self.grabber.makeList()
      self.createMenu() 
      self.loadURL()
      
    def findWord(self):
        find = self.findfield.text()
        print(find)
        self.html.findText(find)

      
    def createMenu(self):
        i = 0
        self.tb = QToolBar("Sender")
        self.tb.setMovable(False)
        self.tb.setContextMenuPolicy(Qt.PreventContextMenu)
        self.tb.setStyleSheet("QToolBar {border: 0px,}")
        self.findfield = QLineEdit()
        self.findfield.setPlaceholderText("suchen ...")
        self.findfield.setStyleSheet("background: #2e3436; color: #eeeeec;")
        self.findfield.setClearButtonEnabled(True)
        self.findfield.returnPressed.connect(self.findWord)
        self.tb.addWidget(self.findfield)
        self.addToolBar(Qt.LeftToolBarArea, self.tb)
        self.tb.setStyleSheet("QToolBar {background: #2e3436;} QToolButton {font-size: 8pt; color: #729fcf;} QToolButton::hover { background: #edd400; color: #2e3436;}")

        self.tb2 = QToolBar("Sender")
        self.tb2.setMovable(False)
        self.tb2.setContextMenuPolicy(Qt.PreventContextMenu)
        self.tb2.setStyleSheet("QToolBar {border: 0px,}")
        self.addToolBar(Qt.RightToolBarArea, self.tb2)
        self.tb2.setStyleSheet("QToolBar {background: #2e3436;} QToolButton {font-size: 8pt; color: #729fcf;} QToolButton::hover { background: #edd400; color: #2e3436;} QToolBar::separator {background: #729fcf; height: 1px;}")
        
        tbnames1 = []
        tbindexes = []
        x = 0
        for ch in chList:
            title = ch
            id = x
            #print(x)
            tbnames1.append(title)
            tbindexes.append(ch)
            x += 1
            
        for x in range(len(tbnames1[:55])):
            title = tbnames1[x]
            id = tbindexes[x]                 
            chm_action = QAction(title, self, triggered = self.showFromMenu)
            self.stationActs.append(chm_action)
            self.stationActs[i].setData(id)
            self.tb.addAction(chm_action)
            i =+ 1

        #i = 0            
        for x in range(55, len(tbnames1)):
            title = tbnames1[x]
            id = tbindexes[x]                 
            chm_action = QAction(title, self, triggered = self.showFromMenu)
            self.stationActs.append(chm_action)
            self.stationActs[i].setData(id)
            self.tb2.addAction(chm_action)
            i =+ 1
            
        self.tb2.addSeparator()
        
    def showFromMenu(self):
        action = self.sender()
        if action:
            ind = action.data()
            name = action.text()
            print("Name:", name, "Ind:", ind)
            url = f"file:///tmp/tv_pluto.html#{name}"
            self.html.load(QUrl(url))
         
        
    def loadURL(self):
        ### temporäre Datei erstellen in /tmp
        with open('/tmp/tv_pluto.html', 'w') as f:
            url = 'file://' + f.name
            f.write(self.my_html)
            f.close()
            self.html.load(QUrl(url))
            self.html.setFocus()
 
if __name__ == "__main__":
 
    app = QApplication(sys.argv)
    main = Browser()
    main.show()
sys.exit(app.exec_())
