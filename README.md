walkmap
=======

walkmap is a tool that currently plots the walking time from the Stata
Center at MIT to most places in Cambridge, MA. It also allows users to
"take the T" (the Red Line) between Kendall and Davis. It is a simple
implementation of Dijkstra's algorithm.

Running
-------

To generate the map, run:

$ make

To clean up the map, run:

$ make clean

To clean up everything, including the JSON, run:

$ make deepclean

Copyright
---------

For the source code, see LICENSE. The map data is copyrighted by
OpenStreetMap contributors; full license information is available at
http://www.openstreetmap.org/copyright.

Preview
-------

See the SVG (2.3 MB) at

	https://www.ocf.berkeley.edu/~qmn/assets/walkmap.svg

or the PNG (859 KB) at

	https://www.ocf.berkeley.edu/~qmn/assets/walkmap.png
