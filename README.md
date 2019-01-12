# mpnotd
MPD Notification Daemon  
  
### Requirements
python3  
python-mpd2  
notify2  
beautifulsoup4   
  
### Usage
Write config file:  
  `mpnotd --writeini`  
  
Enable systemd service:  
  `systemctl --user start mpnotd`  
  `systemctl --user enable mpnotd`  
  
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
> auth = password  
> time = 10                  
> music = /path/to/music   
  
