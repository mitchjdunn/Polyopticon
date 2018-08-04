import io
import socket
import struct
import time
import picamera

ports=[4545,4546]
s = socket.socket()
try:
    s.bind(("0.0.0.0", ports[0]))
except:
    s.bind(("0.0.0.0", ports[1]))
s.listen(0)

connection = s.accept()[0].makefile('wb')

try:
    camera = picamera.PiCamera(framerate=30)
    #camera.resolution = (854,480)
    camera.resolution = (1280,720)
    camera.start_preview()
    camera.exposure_mode = 'spotlight'

    time.sleep(2)
    while True:
        stream=io.BytesIO()
        for foo in camera.capture_continuous(stream, 'jpeg',burst=True):
            size = struct.pack('<L', stream.tell())
            connection.write(size)
            connection.flush()
            stream.seek(0)
            connection.write(stream.read())
            stream.seek(0)
            stream.truncate()
finally:
    connection.close()
    s.close()

