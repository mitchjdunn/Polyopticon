# Polyopticon

##Usage

All code is written and run with Python3.6
Running whiteboard.py will spawn a master whiteboard that is used to control all slave whiteboards on the same network.
whiteboardSlave.py will spawn a slave whiteboard.
All actions done on the master will be sent to the slave.
A slave run on a raspberry pi with a camera will automatically start to stream video to the master and tell the master to start the image recognition process.

##Dependencies
* 
