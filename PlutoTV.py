#!/usr/bin/python3
# -*- coding: utf-8 -*-
#############################################################################
from PyQt5.QtCore import (QPoint, Qt, QUrl, QProcess, QFile, QDir, QSettings, 
                          QStandardPaths, QRect, QSize, QTimer)
from PyQt5.QtGui import QIcon, QDesktopServices
from PyQt5.QtWidgets import (QAction, QApplication, QMainWindow, QMessageBox, QGridLayout, 
                             QMenu, QInputDialog, QLineEdit, QFileDialog, QVBoxLayout, 
                             QFormLayout, QSlider, QPushButton, QDialog, QWidget, QLabel)

import mpv
import os
import sys
from requests import get
from datetime import datetime, timedelta
import locale
from subprocess import check_output, STDOUT, CalledProcessError

mytv = "pluto_logo.png"
menuicon = "menuicon.png"
ratio = 1.777777778

class Message(QWidget):
    def __init__(self, title, message, parent=None):
        QWidget.__init__(self, parent)
        self.setLayout(QGridLayout())
        self.titleLabel = QLabel(title, self)
        self.titleLabel.setStyleSheet("color: #729fcf; font-size: 18px; font-weight: bold; padding: 0;")
        self.messageLabel = QLabel(message, self)
        self.messageLabel.setStyleSheet("color: #729fcf; font-size: 12px; font-weight: normal; padding: 0;")
        self.buttonClose = QPushButton(self)
        self.buttonClose.setIcon(QIcon.fromTheme("window-close"))
        self.buttonClose.setFlat(True)
        self.buttonClose.setFixedSize(32, 32)
        self.buttonClose.setIconSize(QSize(16, 16))
        self.layout().addWidget(self.titleLabel)
        self.layout().addWidget(self.messageLabel, 2, 0)
        self.layout().addWidget(self.buttonClose, 0, 1)

class Notification(QWidget):
    def __init__(self, parent = None):        
        super(QWidget, self).__init__(parent = None)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)      
        self.setStyleSheet("background: #000000; padding: 0;")
        self.mainLayout = QVBoxLayout(self)
        

    def setNotify(self, title, message, timeout):
        self.m = Message(title, message)
        self.mainLayout.addWidget(self.m)
        self.m.buttonClose.clicked.connect(self.onClicked)
        self.show()
        QTimer.singleShot(timeout, 0, self.closeMe)
        
    def closeMe(self):
        self.close()
        self.m.close()
    
    def onClicked(self):
        self.close()
##############################################################################################
class EPG_Grabber():
    def __init__(self):
        
        now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.000Z')
        later = (datetime.now() + timedelta(minutes=45)).strftime('%Y-%m-%dT%H:%M:%S.000Z')

        url = f"http://api.pluto.tv/v2/channels?start={now}&stop={later}"
        r = get(url)

        ### to json 
        if r:
            self.data = r.json() 

    def getValues(self, channel):
        theList = []
        for i in self.data:
            if i['name'] == channel:
                pr = i['timelines']
                for a in pr:
                    title = str(a.get('title'))
                    st = a.get('start')
                    start = st[11:16]
                    
                    theList.append(f"{start} Uhr\n{title}")
        return theList
        
    def getValuesDetails(self, channel):
        theList = []
        for i in self.data:
            if i['name'] == channel:
                pr = i['timelines'][0]["episode"]["series"].get("description")
                theList.append(f"{pr}")

        return theList

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        
        check = self.check_libmpv("libmpv")
        if not check:
            print("libmpv nicht gefunden\n")
            self.msgbox("libmpv nicht gefunden\nBenutze 'sudo apt-get install libmpv1'")
            sys.exit()
        else:
            print("libmpv gefunden")
            
        mpv_check = self.check_mpv("mpv")
        if not mpv_check:
            print("python-mpv nicht gefunden\nBenutze 'pip3 install python-mpv'")
            self.msgbox("python-mpv nicht gefunden\nBenutze 'pip3 install python-mpv'")
            sys.exit()
        else:
            print("python-mpv gefunden")
        
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setStyleSheet("QMainWindow {background-color: 'black';}")
        self.osd_font_size = 28
        self.colorDialog = None
        self.settings = QSettings("PlutoTV", "settings")
        self.own_list = []
        self.pluto_list = []
        self.own_key = 0
        self.default_key = 0
        self.default_list = []
        self.urlList = []
        self.channel_list = []
        self.link = ""
        self.menulist = []
        self.recording_enabled = False
        self.is_recording = False
        self.recname = ""
        self.timeout = "60"
        self.tout = 60
        self.outfile = "/tmp/TV.mp4"
        self.myARD = ""
        self.channelname = ""
        self.mychannels = []
        self.plutochannels = []
        self.channels_menu = QMenu()

        self.processR = QProcess()
        self.processR.started.connect(self.getPID)
        self.processR.finished.connect(self.timer_finished)
        self.processR.finished.connect(self.recfinished)
        self.processR.isRunning = False
        
        self.processW = QProcess()
        self.processW.started.connect(self.getPID)
        self.processW.finished.connect(self.recfinished)
        self.processW.isRunning = False
                         
        self.container = QWidget(self)
        self.setCentralWidget(self.container)
        self.container.setAttribute(Qt.WA_DontCreateNativeAncestors)
        self.container.setAttribute(Qt.WA_NativeWindow)
        self.container.setContextMenuPolicy(Qt.CustomContextMenu);
        self.container.customContextMenuRequested[QPoint].connect(self.contextMenuRequested)
        self.setAcceptDrops(True)
        
        self.mediaPlayer = mpv.MPV(log_handler=self.logger,
                           input_cursor=False,
                           osd_font_size=self.osd_font_size,
                           cursor_autohide=2000, 
                           cursor_autohide_fs_only=True,
                           osd_color='#d3d7cf',
                           osd_blur=2,
                           osd_bold=True,
                           wid=str(int(self.container.winId())), 
                           config=False, 
                           profile="libmpv") 
        # profile=xxx hier einen zum eigenen System passenden Eintrag wählen
        # opengl-hq, sw-fast, low-latency, gpu-hq, encoding, libmpv, builtin-pseudo-gui,pseudo-gui, default    

                         
        self.mediaPlayer.set_loglevel('fatal')
        self.mediaPlayer.cursor_autohide = 2000
        
        self.own_file = "favoriten.txt"
        if os.path.isfile(self.own_file):
            self.mychannels = open(self.own_file).read()
            ### remove empty lines
            self.mychannels = os.linesep.join([s for s in self.mychannels.splitlines() if s])
            with open(self.own_file, 'w') as f:
                f.write(self.mychannels)
                
        self.pluto_file = "pluto.txt"
        if os.path.isfile(self.pluto_file):
            self.plutochannels = open(self.pluto_file).read()
            ### remove empty lines
            self.plutochannels = os.linesep.join([s for s in self.plutochannels.splitlines() if s])
            with open(self.pluto_file, 'w') as f:
                f.write(self.plutochannels)

        self.fullscreen = False

        self.setMinimumSize(320, 180)
        self.setGeometry(100, 100, 480, round(480 / ratio))

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

        self.setWindowTitle("Pluto TV Player & Recorder")
        self.setWindowIcon(QIcon("og-logo-v5.png"))

        self.myinfo = """<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><!--StartFragment--><span style=" font-size:xx-large; font-weight:600;">Pluto TV</span></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">©2020<br /><a href="https://github.com/Axel-Erfurt"><span style=" text-decoration: underline; color:#0000ff;">Axel Schneider</span></a></p>
<h3 style=" margin-top:14px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-size:large; font-weight:600;">Tastaturkürzel:</span></h3>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">q = Beenden<br />f = Vollbild an/aus</p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">Mausrad = Größe ändern</p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">↑ = lauter</p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">↓ = leiser</p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">m = Ton an/aus</p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">h = Mauszeiger an / aus</p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">r = Aufnahme mit Timer</p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">w = Aufnahme ohne Timer<br />s = Aufnahme beenden</p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">-----------------------------------------</p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">1 bis 0 = Favoriten (1 bis 10)</p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">j = was gerade läuft</p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">e = EPG Details</p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">-----------------------------------------</p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">Doppelklick = Vollbild an/aus"""
        print("Willkommen beim TV Player & Recorder")
        if self.is_tool("ffmpeg"):
            print("ffmpeg gefunden\nAufnahme möglich")
            self.recording_enabled = True
        else:
            self.msgbox("ffmpeg nicht gefunden\nkeine Aufnahme möglich")
   
        self.show()
        self.readSettings()            
        self.createMenu()
        self.showNotification(f"Pluto TV\n{self.channelname}", 2000) 
        self.getEPG_detail()
        
    def showNotification(self, message, timeout):
        self.notification = Notification()
        self.notification.setNotify("Pluto TV", message, timeout)
        r = QRect(self.x() + round(self.width() / 2) - round(self.notification.width() / 2), 
                                        self.y() + 26, self.notification.m.messageLabel.width() + 30, self.notification.m.messageLabel.height())
        self.notification.setGeometry(r)
        
        
    def check_libmpv(self, mlib):
        cmd =  f'ldconfig -p | grep {mlib}'
        
        try:
            result = check_output(cmd, stderr=STDOUT, shell=True).decode("utf-8")
        except CalledProcessError:
            return False
            
        if not mlib in result:
            return False
        else:
            return True
            
    def check_mpv(self, mlib):
        cmd =  f'pip3 list | grep {mlib}'
        
        try:
            result = check_output(cmd, stderr=STDOUT, shell=True).decode("utf-8")
            
            if not mlib in result:
                return False
            else:
                return True
            
        except CalledProcessError as exc:
            result = exc.output
            return False
        
    def logger(self, loglevel, component, message):
        print('[{}] {}: {}'.format(loglevel, component, message), file=sys.stderr)
        
    def editOwnChannels(self):
        QDesktopServices.openUrl(QUrl(f"file://{self.own_file}"))
        
    def addToOwnChannels(self):
        if not self.channelname == "":
            if os.path.isfile(self.own_file):
                with open(self.own_file, 'a') as f:
                    f.write(f"\n{self.channelname},{self.link}")
                    self.showNotification("neue Favoriten sind nach einem Neustart verfügbar", 3000)
            else:
                self.msgbox(f"{self.own_file} existiert nicht!")
            
    def readSettings(self):
        print("lese Konfigurationsdatei ...")
        if self.settings.contains("geometry"):
            self.setGeometry(self.settings.value("geometry", QRect(26, 26, 200, 200)))
        else:
            self.setGeometry(100, 100, 480, 480 / ratio)
        if self.settings.contains("lastUrl") and self.settings.contains("lastName"):
            self.link = self.settings.value("lastUrl")
            self.channelname = self.settings.value("lastName")
            self.mediaPlayer.play(self.link)
            print(f"aktueller Sender: {self.channelname}\nURL: {self.link}")
        else:
            if len(self.own_list) > 0:
                self.play_own(0)
        if self.settings.contains("volume"):
            vol = self.settings.value("volume")
            print("setze Lautstärke auf", vol)
            self.mediaPlayer.volume = (int(vol))
        
    def writeSettings(self):
        print("schreibe Konfigurationsdatei ...")
        self.settings.setValue("geometry", self.geometry())
        self.settings.setValue("lastUrl", self.link)
        self.settings.setValue("lastName", self.channelname)
        self.settings.setValue("volume", self.mediaPlayer.volume)
        self.settings.sync()
        
    def mouseDoubleClickEvent(self, event):
        self.handleFullscreen()
        event.accept()
            
    def getBufferStatus(self):
        print(self.mediaPlayer.bufferStatus())

    def createMenu(self):              
        myPlutoMenu = self.channels_menu.addMenu("Pluto TV")
        myPlutoMenu.setIcon(QIcon(mytv))
        if len(self.plutochannels) > 0:
            for ch in sorted(self.plutochannels.splitlines()):
                name = ch.partition(",")[0]
                url = ch.partition(",")[2]
                self.pluto_list.append(f"{name},{url}")
                a = QAction(name, self, triggered=self.playPlutoTV)
                a.setIcon(QIcon(menuicon))
                a.setData(url)
                myPlutoMenu.addAction(a)
                
        myMenu = self.channels_menu.addMenu("Favoriten")
        myMenu.setIcon(QIcon.fromTheme("favorites"))
        if len(self.mychannels) > 0:
            for ch in self.mychannels.splitlines():
                name = ch.partition(",")[0]
                url = ch.partition(",")[2]
                self.own_list.append(f"{name},{url}")
                a = QAction(name, self, triggered=self.playTV)
                a.setIcon(QIcon.fromTheme("favorites"))
                a.setData(url)
                myMenu.addAction(a)

        self.mediaPlayer.show_text("Willkommen", duration="4000", level=None) 
        self.getEPG()
        #############################
        
        if self.recording_enabled:
            self.channels_menu.addSection("Aufnahme")
    
            self.tv_record = QAction(QIcon.fromTheme("media-record"), "Aufnahme mit Timer (r)", triggered = self.record_with_timer)
            self.channels_menu.addAction(self.tv_record)

            self.tv_record2 = QAction(QIcon.fromTheme("media-record"), "Aufnahme ohne Timer (w)", triggered = self.record_without_timer)
            self.channels_menu.addAction(self.tv_record2)

            self.tv_record_stop = QAction(QIcon.fromTheme("media-playback-stop"), "Aufnahme beenden (s)", triggered = self.stop_recording)
            self.channels_menu.addAction(self.tv_record_stop)
    
            self.channels_menu.addSeparator()

        self.about_action = QAction(QIcon.fromTheme("help-about"), "Info / Tastenbelegung (i)", triggered = self.handleAbout, shortcut = "i")
        self.channels_menu.addAction(self.about_action)
        
        self.channels_menu.addSection("Einstellungen")

        self.color_action = QAction(QIcon.fromTheme("preferences-color"), "Bildeinstellungen (c)", triggered = self.showColorDialog)
        self.channels_menu.addAction(self.color_action)

        self.channels_menu.addSeparator()

        self.channels_menu.addSeparator()

        self.channels_menu.addSection("Favoriten")        
        self.addChannelAction = QAction(QIcon.fromTheme("add"), "zu Favoriten hinzufügen", triggered = self.addToOwnChannels)
        self.channels_menu.addAction(self.addChannelAction)
        
        self.channels_menu.addSeparator()
        
        self.quit_action = QAction(QIcon.fromTheme("application-exit"), "Beenden (q)", triggered = self.handleQuit)
        self.channels_menu.addAction(self.quit_action)
        
    def showTime(self):
        t = str(datetime.now())[11:16]
        self.mediaPlayer.show_text(t, duration="4000", level=None) 
        
    def tv_programm_now(self):
        self.epg = EPG_Grabber()
        print("ch =", self.channelname)
        msg = self.epg.getValues(self.channelname)    
        print('\n'.join(msg))
        self.mediaPlayer.osd_font_size = 40
        self.mediaPlayer.show_text('\n'.join(msg), duration="3000", level=None)      
        

    def recfinished(self):
        print("Aufnahme beendet 1")

    def is_tool(self, name):
        tool = QStandardPaths.findExecutable(name)
        if tool != "":
            return True
        else:
            return False

    def getPID(self):
        print("pid", self.processR.processId())

    def record_without_timer(self):
        if not self.recording_enabled == False:
            if QFile(self.outfile).exists:
                print("lösche Datei " + self.outfile) 
                QFile(self.outfile).remove
            else:
                print("Die Datei " + self.outfile + " existiert nicht") 
            self.recname = self.channelname
            print("Aufnahme in /tmp")
            self.is_recording = True
            cmd = f'ffmpeg -loglevel quiet -stats -y -i {self.link.replace("?sd=10&rebase=on", "")} -bsf:a aac_adtstoasc -vcodec copy -c copy -crf 50 "{self.outfile}"'
            print(cmd)
            self.processW.isRunning = True
            self.processW.startDetached(cmd)


    def record_with_timer(self):
        if not self.recording_enabled == False:
            if QFile(self.outfile).exists:
                print("lösche Datei " + self.outfile) 
                QFile(self.outfile).remove
            else:
                print("Die Datei " + self.outfile + " existiert nicht") 
            infotext = '<i>temporäre Aufnahme in Datei: /tmp/TV.mp4</i> \
                            <br><b><font color="#a40000";>Speicherort und Dateiname werden nach Beenden der Aufnahme festgelegt.</font></b> \
                            <br><br><b>Beispiel:</b><br>60s (60 Sekunden)<br>120m (120 Minuten)'
            dlg = QInputDialog()
            tout, ok = dlg.getText(self, 'Länge der Aufnahme', infotext, \
                                    QLineEdit.Normal, "90m", Qt.Dialog)
            if ok:
                self.tout = str(tout)
                self.recordChannel()
            else:
                print("Aufnahme abgebrochen")

    def recordChannel(self):
        self.processR.isRunning = True
        self.recname = self.channelname
        cmd = f'timeout {str(self.tout)} ffmpeg -y -i {self.link.replace("?sd=10&rebase=on", "")} -bsf:a aac_adtstoasc -vcodec copy -c copy -crf 50 "{self.outfile}"'
        print(cmd)
        print("Aufnahme in /tmp mit Timeout: " + str(self.tout))
        self.is_recording = True
        self.processR.start(cmd)
################################################################

    def saveMovie(self):
        self.fileSave()

    def fileSave(self):
        infile = QFile(self.outfile)
        path, _ = QFileDialog.getSaveFileName(self, "Speichern als...", QDir.homePath() + "/Videos/" + self.recname + ".mp4",
            "Video (*.mp4)")
        if os.path.exists(path):
            os.remove(path)
        if (path != ""):
            savefile = path
            if QFile(savefile).exists:
                QFile(savefile).remove()
            print("saving " + savefile)
            if not infile.copy(savefile):
                QMessageBox.warning(self, "Fehler",
                    "Kann Datei nicht schreiben %s:\n%s." % (path, infile.errorString()))
            if infile.exists:
                infile.remove()

    def stop_recording(self):
        print("StateR:", self.processR.state())
        print("StateW:", self.processW.state())
        if self.is_recording == True:
            print("Aufnahme wird gestoppt")
            QProcess().execute("killall ffmpeg")
            if self.processR.isRunning:
                if self.processR.state() == 2:
                    self.processR.kill()
                    self.processR.waitForFinished()
                    self.is_recording = False
                if self.processR.exitStatus() == 0:
                    self.saveMovie()
                    self.processR.isRunning = False
            if self.processW.isRunning:
                if self.processW.state() == 2:
                    self.processW.kill()
                    self.processW.waitForFinished()
                    self.is_recording = False
                if self.processW.exitStatus() == 0:
                    self.saveMovie()
                    self.processW.isRunning = False
        else:
            print("es wird gerade nicht aufgenommen")
 
    def rec_finished(self):
        print("Aufnahme beendet")
        self.processR.kill()

    def timer_finished(self):
        print("Timer beendet")
        self.is_recording = False
        self.processR.kill()
        print("Aufnahme beendet")
        self.saveMovie()

    def handleError(self, loglevel, message):
        print('{}: {}'.format(loglevel, message), file=sys.stderr)

    def handleMute(self):
        if not self.mediaPlayer.mute:
            self.mediaPlayer.mute = True
            print("stumm")
        else:
            self.mediaPlayer.mute = False
            print("nicht stumm")

    def handleAbout(self):
        QMessageBox.about(self, "Pluto TV", self.myinfo)
        
    def getEPG(self):
        self.epg = EPG_Grabber()
        print("ch =", self.channelname)
        msg = self.epg.getValues(self.channelname)    
        self.mediaPlayer.osd_font_size = 40
        self.mediaPlayer.show_text('\n'.join(msg), duration="3000", level=None)
        
    def getEPG_detail(self):
        self.epg = EPG_Grabber()
        print("ch =", self.channelname)
        msg = self.epg.getValuesDetails(self.channelname)    
        self.mediaPlayer.osd_font_size = 30
        self.mediaPlayer.show_text('\n'.join(msg), duration="8000", level=None)

    def handleFullscreen(self):
        if self.fullscreen == True:
            self.fullscreen = False
            print("kein Fullscreen")
        else:
            self.rect = self.geometry()
            self.showFullScreen()
            QApplication.setOverrideCursor(Qt.ArrowCursor)
            self.fullscreen = True
            print("Fullscreen eingeschaltet")
        if self.fullscreen == False:
            self.showNormal()
            self.setGeometry(self.rect)
            QApplication.setOverrideCursor(Qt.BlankCursor)
        self.handleCursor()

    def handleCursor(self):
        if  QApplication.overrideCursor() ==  Qt.ArrowCursor:
            QApplication.setOverrideCursor(Qt.BlankCursor)
        else:
            QApplication.setOverrideCursor(Qt.ArrowCursor)
    
    def handleQuit(self):
        self.mediaPlayer.quit
        self.writeSettings()
        print("Auf Wiedersehen ...")
        app.quit()
        sys.exit()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Q:
            self.handleQuit()
        elif e.key() == Qt.Key_H:
            self.handleCursor()
        elif e.key() == Qt.Key_J:
            self.tv_programm_now()
        elif e.key() == Qt.Key_F:
            self.handleFullscreen()
        elif e.key() == Qt.Key_M:
            self.handleMute()
        elif e.key() == Qt.Key_I:
            self.handleAbout()
        elif e.key() == Qt.Key_U:
            self.playURL()
        elif e.key() == Qt.Key_R:
            self.record_with_timer()
        elif e.key() == Qt.Key_S:
            self.stop_recording()
        elif e.key() == Qt.Key_T:
            self.showTime()
        elif e.key() == Qt.Key_E:
            self.getEPG_detail()
        elif e.key() == Qt.Key_W:
            self.record_without_timer()
        elif e.key() == Qt.Key_C:
            self.showColorDialog()
        elif e.key() == Qt.Key_1:
            self.play_own(0)
        elif e.key() == Qt.Key_2:
            self.play_own(1)
        elif e.key() == Qt.Key_3:
            self.play_own(2)
        elif e.key() == Qt.Key_4:
            self.play_own(3)
        elif e.key() == Qt.Key_5:
            self.play_own(4)
        elif e.key() == Qt.Key_6:
            self.play_own(5)
        elif e.key() == Qt.Key_7:
            self.play_own(6)
        elif e.key() == Qt.Key_8:
            self.play_own(7)
        elif e.key() == Qt.Key_9:
            self.play_own(8)
        elif e.key() == Qt.Key_0:
            self.play_own(9)
        elif e.key() == Qt.Key_Up:
            if self.mediaPlayer.volume < 100:
                self.mediaPlayer.volume = (self.mediaPlayer.volume + 5)
                print("Lautstärke:", self.mediaPlayer.volume)
        elif e.key() == Qt.Key_Down:
            if self.mediaPlayer.volume > 5:
                self.mediaPlayer.volume = (self.mediaPlayer.volume - 5)
                print("Lautstärke:", self.mediaPlayer.volume)
        else:
            e.accept()

    def contextMenuRequested(self, point):
        self.channels_menu.exec_(self.mapToGlobal(point))
        
    def playFromKey(self, url):
        self.link = url
        self.mediaPlayer.play(self.link)

    def playTV(self):
        action = self.sender()
        self.link = action.data().replace("\n", "")
        self.channelname = action.text()
        if self.channelname in self.channel_list:
            self.default_key = self.channel_list.index(self.channelname)
        else:
            self.own_key = self.own_list.index(f"{self.channelname},{self.link}")
        print(f"aktueller Sender: {self.channelname}\nURL: {self.link}")
        self.mediaPlayer.play(self.link)
        self.mediaPlayer.show_text(self.channelname, duration="5000", level=None)
        self.getEPG()
        
    def playPlutoTV(self):
        action = self.sender()
        self.link = action.data().replace("\n", "")
        self.channelname = action.text()
        if self.channelname in self.pluto_list:
            self.default_key = self.pluto_list.index(self.channelname)
        else:
            self.own_key = self.pluto_list.index(f"{self.channelname},{self.link}")
        print(f"aktueller Sender: {self.channelname}\nURL: {self.link}")
        self.mediaPlayer.show_text(self.channelname, duration="10000", level=None)
        self.mediaPlayer.play(self.link)
        self.getEPG()
        

    def play_own(self, channel):
        if not channel > len(self.own_list) - 1:
            self.own_key = channel
            self.link = self.own_list[channel].split(",")[1]
            self.channelname = self.own_list[channel].split(",")[0]
            print("eigener Sender:", self.channelname, "\nURL:", self.link)
            self.mediaPlayer.play(self.link)
            self.mediaPlayer.show_text(self.channelname, duration="5000", level=None)
            self.getEPG()
        else:
            print(f"Kanal {channel} ist nicht vorhanden")

    def closeEvent(self, event):
        event.accept()

    def msgbox(self, message):
        QMessageBox.warning(self, "Meldung", message)
        
    def wheelEvent(self, event):
        mwidth = self.frameGeometry().width()
        mscale = round(event.angleDelta().y() / 6)
        self.resize(mwidth + mscale, round((mwidth + mscale) / ratio))
        event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() \
                      - QPoint(round(self.frameGeometry().width() / 2), \
                               round(self.frameGeometry().height() / 2)))
            event.accept()
            
    def setBrightness(self):
        self.mediaPlayer.brightness = self.brightnessSlider.value()
        
    def setContrast(self):
        self.mediaPlayer.contrast = self.contrastSlider.value()
        
    def setHue(self):
        self.mediaPlayer.hue = self.hueSlider.value()

    def setSaturation(self):
        self.mediaPlayer.saturation = self.saturationSlider.value()
        
    def showColorDialog(self):
        if self.colorDialog is None:
            self.brightnessSlider = QSlider(Qt.Horizontal)
            self.brightnessSlider.setRange(-100, 100)
            self.brightnessSlider.setValue(self.mediaPlayer.brightness)
            self.brightnessSlider.valueChanged.connect(self.setBrightness)

            self.contrastSlider = QSlider(Qt.Horizontal)
            self.contrastSlider.setRange(-100, 100)
            self.contrastSlider.setValue(self.mediaPlayer.contrast)
            self.contrastSlider.valueChanged.connect(self.setContrast)
            
            self.hueSlider = QSlider(Qt.Horizontal)
            self.hueSlider.setRange(-100, 100)
            self.hueSlider.setValue(self.mediaPlayer.hue)
            self.hueSlider.valueChanged.connect(self.setHue)

            self.saturationSlider = QSlider(Qt.Horizontal)
            self.saturationSlider.setRange(-100, 100)
            self.saturationSlider.setValue(self.mediaPlayer.saturation)
            self.saturationSlider.valueChanged.connect(self.setSaturation)

            layout = QFormLayout()
            layout.addRow("Helligkeit", self.brightnessSlider)
            layout.addRow("Kontrast", self.contrastSlider)
            layout.addRow("Farbton", self.hueSlider)
            layout.addRow("Farbe", self.saturationSlider)

            btn = QPushButton("zurücksetzen")
            btn.setIcon(QIcon.fromTheme("preferences-color"))
            layout.addRow(btn)

            button = QPushButton("Schließen")
            button.setIcon(QIcon.fromTheme("ok"))
            layout.addRow(button)

            self.colorDialog = QDialog(self)
            self.colorDialog.setWindowTitle("Bildeinstellungen")
            self.colorDialog.setLayout(layout)

            btn.clicked.connect(self.resetColors)
            button.clicked.connect(self.colorDialog.close)

        self.colorDialog.resize(300, 180)
        self.colorDialog.show()

    def resetColors(self):
        self.brightnessSlider.setValue(0)
        self.mediaPlayer.brightness = (0)

        self.contrastSlider.setValue(0)
        self.mediaPlayer.contrast = (0)

        self.saturationSlider.setValue(0)
        self.mediaPlayer.saturation = (0)

        self.hueSlider.setValue(0)
        self.mediaPlayer.hue = (0)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    locale.setlocale(locale.LC_NUMERIC, 'C')
    mainWin = MainWindow()
    sys.exit(app.exec_())
