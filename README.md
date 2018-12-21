# mpnotd
MPD Notification Daemon  
  
### Requirements
python3  
python-mpd2  
notify2  
beautifulsoup4   

### Usage
  
Show current track info:  
  `mpnotd`  
  
Start as daemon and notify on MPD changes:  
  `mpnotd --daemon`  
  
Write config file:  
  `mpnotd --writeini`  
  
### Options
*  -d or --daemon:  Start as daemon  
*  --writeini:      Write config file  
*  --DEBUG:         Log debug messages  
*  -h or --help:    Print help  

### Configuration file

> [mpnotd]  
> host = localhost          MPD hostname or IP address  
> port = 6600               MPD port  
> auth = password           Server password or leave blank  
> time = 10                 Time in seconds to display notification  
> music = /path/to/music    Path to local music directory  
