# Polyopticon

##Usage

All code is written and run with Python3.6

whiteboard.py will spawn a master whiteboard that is used to control all slave whiteboards on the same network.
whiteboardSlave.py will spawn a slave whiteboard.
All actions done on the master will be sent to the slave.
When a slave is run on a Raspberry Pi with a camera it will automatically start to stream video to the master and tell the master to start the image recognition process.
Once this process is started calibration will happen automatically and the user can start inputting via infrared pen.
If the camera needs to be adjusted a recalibration can be initiated from the master whiteboard


##Dependencies
This project utilizes packages installed from both pip and the OS package manager.

All Systems:
`pip3 install -r requirements.txt`

Ubuntu Based Systems:
`apt install python3-tk python3-pil python-pil.imagetk`

RHEL Based Systems:
`dnf install python3-pillow python3-pillow-tk python3-tkinter`
