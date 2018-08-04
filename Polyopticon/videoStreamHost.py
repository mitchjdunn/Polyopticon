import io
import socket
import struct
from PIL import Image
import numpy as np
import cv2

s = socket.socket()
IP = "192.168.1.6"
ports= [4545,4546]
try:
    s.connect((IP, ports[0]))
except:
    s.connect((IP,ports[1]))
connection = s.makefile('rb')
try:
    while True:
        # Read the length of the image as a 32-bit unsigned int. If the
        # length is zero, quit the loop
        image_len = struct.unpack('<L', connection.read(struct.calcsize('<L')))[0]
        while not image_len:
            image_len = struct.unpack('<L', connection.read(struct.calcsize('<L')))[0]
        # Construct a stream to hold the image data and read the image
        # data from the connection
        stream = io.BytesIO()
        stream.write(connection.read(image_len))
        data = np.fromstring(stream.getvalue(), dtype=np.uint8)
        # Rewind the stream, open it as an image with PIL and do some
        # processing on it
        image = cv2.imdecode(data,1)
        cv2.imshow('img', image)
        cv2.waitKey(1)
finally:
    connection.close()
    s.close()
