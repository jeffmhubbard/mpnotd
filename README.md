# mpnotd  
MPD Notification Daemon  
  
Watches MPD for status changes and displays notifications.  
  
* Display current sing information
* Fetch and thumbnail album art
* [testing] Change CAVA color based on album art
  
### Requirements  
python3  
python-mpd2  
notify2  
dbus-python
beautifulsoup4   
Pillow  
colorthief
colormath
  
### Recommended  
dunst  
CAVA  
  
### Installation  
  
Arch Linux (AUR):  
`auracle download -r mpnotd-git`  
  
### Usage  
To start from terminal or application launcher:  
  `mpnotd`  
  
Write config file:  
  `mpnotd --writeini`  
  
Enable systemd service:  
  `systemctl --user enable mpnotd`  
  `systemctl --user start mpnotd`  
  
### Arguments  
*  --writeini:      Write config file  
*  --DEBUG:         Log debug messages  
*  -h or --help:    Print help  
  
### Configuration  
After running `mpnotd --writeini`, you can edit your config
file at `~/.config/mpnotd/config`
  
```
[mpnotd]  
# Hostname or IP of MPD server  
host = localhost  

# Port of MPD server  
port = 6600  

# Password for MPD server (leave blank for now password) 
auth = password  

# Notification timeout (may be ignored by some servers)  
timeout = 10  

# Path to local music collection (should be same as MPD music dir)  
music = /path/to/music   

# Enable CavaColors, 0 disabled, 1 dominant color, 2 palette match
cava = 1

# CavaColors palette
cava_colors = #ff0000,#00ff00,#0000ff
```
