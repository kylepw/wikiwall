========
wikiwall
========
*wikiwall* is a CLI that downloads a random image from Wikiart's Hi-Res page and sets it as your desktop background in MacOS.

.. image:: https://github.com/kylepw/wikiwall/blob/master/example.gif
	:align: center

Features
--------
- Easily customize your desktop with new hi-res artwork from the command line.
- Update your wallpaper periodically with your favorite scheduler.

Requirements
------------
- Python 3.7 or higher
- macOS


Installation
------------ 
::

	$ pip3 install wikiwall

If you want, set your wallpaper to change every night with launchd: ::

	$ git clone https://github.com/kylepw/wikiwall.git
	$ sed -i.bak -e "s|WIKIWALL|$(which wikiwall)|g" wikiwall/wikiwall.plist
	$ cp wikiwall/wikiwall.plist ~/Library/LaunchAgents
	$ launchctl load ~/Library/LaunchAgents/wikiwall.plist


Usage
----- 
::

	$ wikiwall --help
	Usage: wikiwall [OPTIONS]

	  Set desktop background in MacOS to random WikiArt image.

	Options:
  	  --dest TEXT      Download images to specified destination.
  	  --limit INTEGER  Number of files to keep in download directory. Set to -1 for no limit. Default is 10.
  	  --debug          Show debugging messages.
  	  --help           Show this message and exit.
 
Todo
----
- Add documentation to Sphinx.
- Add support for other operating systems.

License
-------
`MIT License <https://github.com/kylepw/wikiwall/blob/master/LICENSE>`_
