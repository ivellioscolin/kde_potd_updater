# KDE Plasma POTD Updater

kdeplasma-addons POTD is an excellent addon which lets you keep your wallpaper and lock screen background up-to-date. However it's not flawless when you find:
- POTD in lock screen can't get updated due to internet access isn't allowed in lock screen.
- Only activated POTD provider gets updated, so you can't leverage the POTD picture for other usage, i.e. as an auto-updated greeter background.

The script has implemented all POTD providers as kdeplasma-addons does. With the script, you can create an autostart script or scheduled task to update the selected POTD, or manually. By default, the script will download POTDs to plasma wallpaper and screen lock directory, which can be modified.

Supported POTD provider:
- Astronomy Picture of the Day
- Bing's Picture of the Day
- Earth Science Picture of the Day
- Flickr Picture of the Day
- National Geographic
- NOAA Environmental Visualization Laboratory Picture of the Day
- Wikimedia Picture of the Day

Usage:
```python
python kde_potd_updater.py apod|bing|epod|flickr|natgeo|noaa|wcpotd [save]