# mpnotd  
MPD Notification Daemon  
  
Watches MPD for status changes and displays notifications.  
  
  
### Requirements  
python3  
python-mpd2  
notify2  
beautifulsoup4   
Pillow  
  
### Recommended
dunst  
  
### Usage  
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
  
> [mpnotd]  
> host = localhost  
> port = 6600  
> auth = password (leave blank for now password) 
> time = 10                  
> music = /path/to/music   
  
