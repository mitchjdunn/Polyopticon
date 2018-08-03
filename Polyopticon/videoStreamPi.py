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
    print("fag")
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
        print(1)
        for foo in camera.capture_continuous(stream, 'jpeg',burst=True):

            size = struct.pack('<L', stream.tell())
            print(2)
            connection.write(size)
            print(size)
            print(3)
            connection.flush()

            print(4)
            stream.seek(0)
            print(5)
            connection.write(stream.read())

            print(6)
            stream.seek(0)
            print(7)
            stream.truncate()

            print(8)
finally:
    connection.close()
    s.close()

