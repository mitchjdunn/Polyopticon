# Polyopticon

##Usage

All code is written and run with Python3.6

whiteboard.py will spawn a master whiteboard that is used to control all slave whiteboards on the same network.
whiteboardSlave.py will spawn a slave whiteboard.
All actions done on the master will be sent to the slave.
A slave run on a raspberry pi with a camera will automatically start to stream video to the master and tell the master to start the image recognition process.

##Dependencies

`pip3 install -r requirements.txt`

Ubuntu:
`apt install python3-tk python3-pil python-pil.imagetk`

DNF/YUM:
`dnf install python3-pillow python3-pillow-tk python3-tkinter`
