## For newer versions of Ubuntu / Mint / Debian !

- rename mpv.py to mpv.py_old and load a newer version of mpv.py
- Open a terminal in the source folder and

```wget https://raw.githubusercontent.com/jaseg/python-mpv/main/mpv.py```

# GermanPlutoTV
Pluto TV App

Player zum Abspielen von Pluto TV Streams.

### Voraussetzungen

- python3
- PyQt5
- libmpv

### PyQt5
```sudo apt-get install python3-pyqt5 python3-pyqt5.qtmultimedia libqt5multimedia5-plugins ```

### libmpv
```sudo apt-get install libmpv```

### Starten

```cd GermanPlutoTV```

```python3 ./PlutoTV.py```

### Favoriten

per Menü hinzufügen, Löschen in der Datei favoriten.txt


### Tastaturkürzel
- q = Beenden
- f = Vollbild an/aus
- Mausrad = Größe ändern
- ↑ = lauter
- ↓ = leiser
- m = Ton an/aus
- h = Mauszeiger an / aus
- r = Aufnahme mit Timer
- w = Aufnahme ohne Timer
- s = Aufnahme beenden
- 1 bis 0 = Favoriten (1 bis 10)
- j = was gerade läuft
- e = EPG Details
- Doppelklick = Vollbild an/aus

