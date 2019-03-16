========
wikiwall
========
.. image:: https://travis-ci.com/kylepw/wikiwall.svg?branch=master
    :target: https://travis-ci.com/kylepw/wikiwall
.. image:: https://readthedocs.org/projects/wikiwall/badge/?version=latest
	:target: https://wikiwall.readthedocs.io/en/latest/?badge=latest
	:alt: Documentation Status
.. image:: https://coveralls.io/repos/github/kylepw/wikiwall/badge.svg?branch=master
	:target: https://coveralls.io/github/kylepw/wikiwall?branch=master

*wikiwall* is a CLI that downloads a random image from Wikiart's Hi-Res page and sets it as your desktop background in macOS.

.. image:: https://github.com/kylepw/wikiwall/blob/master/docs/_static/example.gif
	:align: center

Features
--------
- Easily customize your desktop with new hi-res artwork from the command line.
- Update your wallpaper periodically with your favorite scheduler.

Requirements
------------
- Python 3.6 or higher
- macOS

Installation
------------
::

	$ pip3 install wikiwall

If you want, set your wallpaper to change every night with launchd: ::

	$ git clone https://github.com/kylepw/wikiwall.git && cd wikiwall
	$ sed -i.bak -e "s|WIKIWALL|$(which wikiwall)|g" wikiwall.plist
	$ cp wikiwall.plist ~/Library/LaunchAgents
	$ launchctl load ~/Library/LaunchAgents/wikiwall.plist

Usage
-----
::

	$ wikiwall --help
	Usage: wikiwall [OPTIONS] COMMAND [ARGS]...

  	  Set desktop background in macOS to random WikiArt image.

	Options:
  	  --dest TEXT      Download images to specified destination.
  	  --limit INTEGER  Number of files to keep in download directory. Set to -1
   	                   for no limit. Default is 10.
  	  --debug          Show debugging messages.
  	  --help           Show this message and exit.

	Commands:
  	  show  Show previous downloads in Finder.

Todo
----
- Set wallpaper on a desktop not currently being viewed.
- Add support for other operating systems.
- Provide preview of image before setting as background.

License
-------
`MIT License <https://github.com/kylepw/wikiwall/blob/master/LICENSE>`_
