#!/usr/bin/env python3 

from tkinter import *
import io
from tkinter.filedialog import askopenfilename, asksaveasfile
from PIL import Image, ImageTk
import threading
import socket 
import traceback
from time import sleep
from tkinter.colorchooser import askcolor
import base64
import struct
from whiteboardView import WhiteboardView

class VideoSocket():
    def __init__(self, debug=False):
        self.ip = "0.0.0.0"
        self.ports = [4545,4546,4547,4548]
        self.debug = debug
        self.s = socket.socket() 

    def close(self):
        self.s.close()
    def bind(self):
        for port in self.ports:
            try:
                self.s.bind((self.ip, port))
                if self.debug:
                    print('bound to port {}'.format(port))
                return
            except Exception as e:
                if self.debug:
                    print('failed to bind of port {}.'.format(port))
                    print(e)
        self.s.close()
        if self.debug:
            print('Failed to bind to all ports')                

    
    def sendImages(self):
        try:
            import picamera
        except:
            if self.debug:
                print("No module picamera. Slave should be run on raspberry pi.")
            self.close()
            return
        self.bind()
        self.s.listen(0)
        connection = self.s.accept()[0].makefile('wb')
        
        try:
            camera = picamera.PiCamera(framerate = 30)
            camera.resolution = (1280,720)
            camera.rotation =270
            #camera.exposure_mode = 'spotlight'
            while True:
                stream = io.BytesIO()
                for _ in camera.capture_continuous(stream, 'jpeg', use_video_port = True):
                    size = struct.pack('<L', stream.tell())
                    if self.debug:
                        print('image size: {}'.format(size))
                    connection.write(size)
                    connection.flush()
                    stream.seek(0)
                    connection.write(stream.read())
                    stream.seek(0)
                    stream.truncate()
        finally:
            connection.close()
            self.s.close()

class DrawSocket(object): 
    def __init__(self, paint, debug=False):
        # Setup server socket
        self.debug = debug
        self.paint = paint
        self.port = 15273
        self.connected = False
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.serverSocket.bind(('0.0.0.0', self.port))
        # listen for clients in another thread
        threading.Thread(target = self.listen).start()
        # self.listen()
    
    def close(self):
        self.serverSocket.close()

    # Accepts new sockets from server socket
    def listen(self):
        self.serverSocket.listen(5)
        while True:
            client, address = self.serverSocket.accept()
            # client.settimeout(60)
            # threading.Thread(target = self.listenToClient,args = (client,address)).start()
            self.listenToClient(client, address)

    # Recv data from client and translate that to lines in the Tk app
    def listenToClient(self, client, address):
        self.connected = True
        if self.debug:
            print("New client connected")
        size = 2048
        data = b''
        while True:
            try:
                data = data + client.recv(size)
                if data is b'' or data.decode("utf-8").rstrip() is '':
                    if self.debug:
                        self.connected = False
                        print("no data, client dead")
                    return 

                string = data.decode("utf-8")
                lines = string.split(sep='\n')

                if not string.endswith('\n'):
                    if self.debug:
                        print("adding line to next buffer")
                    data = str.encode(lines[-1])
                    lines = lines[:-1]
                else:
                    data = b''

                for line in lines:
                    self.paint.handle(line)

            except Exception as e:
                print('client disconnected due to error') 
                print(e)
                traceback.print_exc()
                client.close()
                self.connected = False
                return False

    def socketConnected(self):
        return self.connected
    
class BroadcastListener(object): 
    def __init__(self, paint, debug=False):
        self.debug= debug 
        if self.debug:
            print("Setting up broadcast listener")
        self.paint = paint
        self.client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        self.client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.client.bind(("", 15272))
        threading.Thread(target = self.listen).start()

    def listen(self):
        while True:
            data, addr = self.client.recvfrom(1024)
            if self.debug:
                print("received message: %s, from: %s"%(data, addr))
            if 'whiteboard' in data.decode("utf-8"):
                self.paint.addSlave(addr[0])
    def close(self):
        self.client.close()

class Paint(object):

    def __init__(self, master=False, debug=False):
        self.debug = debug
        self.slaveAttached = False
        self.slaveIP = None
        self.master = master
        self.sendQueue = []
        # Setup the Tk interface
        self.color = 0
        self.currentColor = 0
        self.root = Tk()
        self.slavesocket = None
        self.colors = ['red', 'blue', 'green', 'purple', 'orange']
        self.sizes = [1, 3, 5, 8, 10, 20]
        self.currentSize = 0

        self.canvas = Canvas(self.root, bg='black', highlightthickness=0)# , width=600, height=600)
        self.canvas.pack(fill=BOTH, expand=YES, padx = 0, pady = 0)
        
        self.addCanvasButtons()
        self.root.config(background="dark blue")

        self.history = ""

        self.w = None
        if self.debug:
            print("setting up socket")
        if master: 
            self.broadcast = BroadcastListener(self, debug=self.debug) 

            self.menubar = Menu(self.root)
        
            self.filemenu = Menu(self.menubar, tearoff=0)
            self.filemenu.add_command(label="Clear Board", command=self.clearDrawButton)
            self.filemenu.add_command(label="Recalibrate", command=self.recalibrate)
            self.filemenu.add_separator()
            self.filemenu.add_command(label="Upload Picture", command=self.insertImage)
            self.filemenu.add_command(label="Save Picture", command=self.saveCanvasToFile)
            self.filemenu.add_separator()
            self.filemenu.add_command(label="Exit", command=self.root.quit)
            self.menubar.add_cascade(label="File", menu=self.filemenu)
            
            if self.debug:
                self.debugmenu = Menu(self.menubar, tearoff=0)
                self.debugmenu.add_command(label="Done Calib", command=self.doneCalib)
                self.debugmenu.add_command(label="calibNW", command=self.calibNW)
                self.debugmenu.add_command(label="calibNE", command=self.calibNE)
                self.debugmenu.add_command(label="calibSW", command=self.calibSW)
                self.debugmenu.add_command(label="calibSE", command=self.calibSE)
                self.menubar.add_cascade(label="Debug", menu=self.debugmenu)

            self.root.config(menu=self.menubar)
        else:
            self.d = DrawSocket(self, debug=self.debug)
            threading.Thread(target = self.waitForMaster, args=[self.d] ).start()


    def recalibrate(self):
        if not self.w is None:
            self.w.recalibrate()

    def fullClearCanvas(self):
        self.clearDrawing()
        self.canvas.delete("all")
        self.canvas.pack(fill=BOTH, expand=YES, padx=0, pady=0)
        self.canvas.create_rectangle(0, 0, self.canvas.winfo_width(), self.canvas.winfo_height(), fill='black')
    
    def calibNW(self):
        if self.master:
            self.sendToSlave('calib,nw')
        self.root.update()
        self.fullClearCanvas()
        self.canvas.create_rectangle(10, 10, 110, 110, fill='dark blue')
        self.canvas.create_text(self.canvas.winfo_width() / 2, 200, font=('Courier', 32), text="CALIBRATING...", fill="yellow")

    def calibSW(self):
        if self.master:
            self.sendToSlave('calib,sw')
            
        self.root.update()
        self.fullClearCanvas()
        self.canvas.create_rectangle(10, self.canvas.winfo_height() - 110, 110, self.canvas.winfo_height() - 10, fill='dark blue')
        self.canvas.create_text(self.canvas.winfo_width() / 2, 200, font=('Courier', 32), text="CALIBRATING...", fill="yellow")
        
    def calibSE(self):
        if self.master:
            self.sendToSlave('calib,se')
        self.root.update()
        self.fullClearCanvas()
        self.canvas.create_rectangle( self.canvas.winfo_width() - 110, self.canvas.winfo_height() - 110, self.canvas.winfo_width() - 10, self.canvas.winfo_height() - 10, fill='dark blue')
        self.canvas.create_text(self.canvas.winfo_width() / 2, 200, font=('Courier', 32), text="CALIBRATING...", fill="yellow")

    def calibNE(self):
        if self.master:
            self.sendToSlave('calib,ne')
        self.root.update()
        self.fullClearCanvas()
        self.canvas.create_rectangle(self.canvas.winfo_width() - 110, 10, self.canvas.winfo_width() - 10, 110, fill='dark blue')
        self.canvas.create_text(self.canvas.winfo_width() / 2, 200, font=('Courier', 32), text="CALIBRATING...", fill="yellow")

    def doneCalib(self):
        if self.master:
            self.sendToSlave('calib,done')
        self.fullClearCanvas()
        # self.canvas.pack(fill=BOTH, expand=YES, padx=0, pady=10)
        self.addCanvasButtons()

    def addCanvasButtons(self):
        self.penButton = Button(self.root, text='pen', command=self.usePen, bg="dark blue", fg = "white", highlightthickness=0, activebackground="light blue")
        self.penButton.configure(width = 10, height = 6, bd=0) 
        self.penButtonX = 10 
        self.penButtonY = 10
        self.canvas.create_window(10, 10, anchor=NW, window=self.penButton)

        self.colorButton = Button(self.root, text='color', command=self.chooseColor, bg="dark blue", fg = "white", highlightthickness=0, activebackground="light blue")
        self.colorButton.configure(width = 10, height = 6, bd = 0) 
        self.colorButtonX = 10
        self.colorButtonY = 140
        self.canvas.create_window(10, 90, anchor=NW, window=self.colorButton)

        self.eraserButton = Button(self.root, text='eraser', command=self.useEraser, bg="dark blue", fg = "white", highlightthickness=0, activebackground="light blue")
        self.eraserButton.configure(width = 10, bd = 0, height = 6)
        self.eraserButtonX = 10 
        self.eraserButtonY = 270 
        self.canvas.create_window(10, 170, anchor=NW, window=self.eraserButton)

        self.sizeButton = Button(self.root, text='Size (1)', command=self.changeSize, bg="dark blue", fg = "white", highlightthickness=0, activebackground="light blue")
        self.sizeButton.configure(width = 10, bd = 0, height = 6)
        self.sizeButtonX = 10 
        self.sizeButtonY = 400
        self.canvas.create_window(10, 250, anchor=NW, window=self.sizeButton)

    def insert64image(self, base64string):
        fh = open('temp.png', 'wb')
        fh.write(base64.b64decode(base64string))
        fh.close()
        self.insertImageHelper('temp.png')
        return
        image = Image.open(io.BytesIO(base64.b64decode(base64string)))
        # filething = cStringIO.StringIO(base64.b64decode(base64string))
        # image = Image.open(filething)
        # Resize the image to fit in the canvas 
        if image.size[0] > image.size[1]: 
            basewidth = self.canvas.winfo_width() - 110
            wpercent = (basewidth/float(image.size[0]))
            hsize = int((float(image.size[1])*float(wpercent)))
            image = image.resize((basewidth,hsize), Image.ANTIALIAS)
        else:
            baseheight = self.canvas.winfo_height()
            hpercent = (baseheight/float(image.size[1]))
            wsize = int((float(image.size[0])*float(hpercent)))
            image = image.resize((baseheight,wsize), Image.ANTIALIAS)
            
        print("something")
        self.canvasimage = ImageTk.PhotoImage(image)
        self.canvas.create_image(110, 0, image=self.canvasimage, anchor=NW)
        
    def insertImage(self):
        filename = askopenfilename()
        self.insertImageHelper(filename)
        
    def insertImageHelper(self, filename):
        image = Image.open(filename)
        self.root.update()

        print(image.size)
    
        # Resize the image to fit in the canvas 
        if image.size[0] > image.size[1]: 
            basewidth = self.canvas.winfo_width() - 110
            wpercent = (basewidth/float(image.size[0]))
            hsize = int((float(image.size[1])*float(wpercent)))
            image = image.resize((basewidth,hsize), Image.ANTIALIAS)
        else:
            baseheight = self.canvas.winfo_height()
            hpercent = (baseheight/float(image.size[1]))
            wsize = int((float(image.size[0])*float(hpercent)))
            image = image.resize((baseheight,wsize), Image.ANTIALIAS)
            
        print("something")
        self.canvasimage = ImageTk.PhotoImage(image)
        self.canvas.create_image(110, 0, image=self.canvasimage, anchor=NW)

        if self.master:
            with open(filename, 'rb') as f:
                b64image = base64.b64encode(f.read())
                b64image = b64image.decode("utf-8")
                print('b64 image: {}'.format(b64image))
                self.sendToSlave('image,{}'.format(b64image))

    def saveCanvasToFile(self):
        ps = self.canvas.postscript(file='export.ps', colormode = 'color')
        ps = self.canvas.postscript(colormode = 'color')

        f = asksaveasfile(mode='w', defaultextension='.jpg')
        # dialog box was cancelled
        if f is None:
            return 

        im = Image.open(io.BytesIO(ps.encode('utf-8')))
        im.save(f, quality=99)

    def waitForMaster(self, drawsocket):
        broadcast = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
        broadcast.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
        broadcast.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        while True:
            if self.debug:
                print("starting broadcasts")
            while not drawsocket.socketConnected():
                if self.debug:
                    print("pinging for master")
                broadcast.sendto(str.encode('whiteboard'), ('255.255.255.255', 15272))
                sleep(3)
            if self.debug:
                print("broadcasts stopped")
            while drawsocket.socketConnected():
                sleep(1)
        
    def slaveSendThread(self, socket):
        currentPos = 0
        while True:
            sleep(0.1)
            while currentPos < len(self.sendQueue):
                try: 
                    line = self.sendQueue[currentPos]
                    socket.send(line)
                    currentPos = currentPos + 1
                except Exception as e:
                    if self.debug:
                        print("slave is dead")
                        print(e)
                    return
                
            
    def close(self):
        if self.master:
            self.broadcast.close()
            try:
                self.w.close()
            except:
                pass
        else:
            self.d.close()
            self.v.close()
        
    def startLoop(self): 
        self.setup()
        self.root.update()
        self.canvas.create_rectangle(0, 0, 4000, 4000, fill='black')
        self.root.mainloop()
        
    def changeSize(self):
        self.currentSize = (self.currentSize + 1) % len(self.sizes)
        self.sizeButton.configure(text="Size ({})".format(self.sizes[self.currentSize]))
        self.sendToSlave('size,{}'.format(self.sizes[self.currentSize]))

    def setup(self):
        self.oldX = None
        self.oldY = None
        self.lineWidth = self.sizes[self.currentSize]
        self.eraserOn = False
        self.activateButton = self.penButton
        self.canvas.bind('<B1-Motion>', self.paint)
        self.canvas.bind('<ButtonRelease-1>', self.reset)
        self.prev = None
    
        if not self.master:
            self.v = VideoSocket(debug=self.debug)
            threading.Thread(target = self.v.sendImages).start()            
        
    def usePen(self):
        self.eraserOn = False
        self.color = (self.color + 1) % len(self.colors)
        self.activateButton = self.penButton

    def useEraser(self):
        self.eraserOn = True
        self.sendToSlave('color,black')
        self.activateButton = self.eraserButton

    def chooseColor(self):
        self.eraserOn = False
        self.color = (self.color + 1) % len(self.colors)
        self.sendToSlave('color,{}'.format(self.color))

    def activateButton(self, some_button):
        self.activateButton.config(relief=RAISED)
        some_button.config(relief=SUNKEN)
        self.activateButton = some_button

    def paint(self, event):
        self.lineWidth = self.sizes[self.currentSize]
        paintColor = 'black' if self.eraserOn else self.colors[self.color]
        if self.oldX and self.oldY:
            self.canvas.create_line(self.oldX, self.oldY, event.x, event.y,
                               width=self.lineWidth, fill=paintColor,
                               capstyle=ROUND, smooth=TRUE, splinesteps=36)
            if self.master:
                # self.root.update()
                calcx = float(event.x) / self.canvas.winfo_width() * 100
                calcy = float(event.y) / self.canvas.winfo_height() * 100
                try:
                    self.sendToSlave('{},{}'.format(calcx, calcy))
                except Exception as e:
                    pass
        elif self.master:
            # self.root.update()
            calcx = float(event.x) / self.canvas.winfo_width() * 100
            calcy = float(event.y) / self.canvas.winfo_height() * 100
            try:
                self.sendToSlave('down,{},{}'.format(calcx, calcy))
            except Exception as e:
                pass
        self.oldX = event.x
        self.oldY = event.y

    def reset(self, event):
        self.oldX, self.oldY = None, None
        self.sendToSlave('up')

    # Setter for pensize
    def setSize(self, size):
        self.lineWidth = int(size)

    # setter for pen color
    def setColor(self, color): 
        self.color = color

    def normalizedDrawLine(self, fromX, fromY, toX, toY):
        self.root.update()
        w = float(self.canvas.winfo_width())
        h = float(self.canvas.winfo_height())
        # print("canvas WxH = {} {}".format(w, h))
        
        # normalized from x 
        nfX = (float(fromX) / 100.0) * w
        # normalized from y 
        nfY = (float(fromY) / 100.0) * h 

        # normalized from x 
        ntX = (float(toX) / 100.0) * w 
        # normalized from y 
        ntY = (float(toY) / 100.0) * h 
            
        # print("drawing line line from {},{} to {},{}".format(nfX, nfY, ntX, ntY))
        self.canvas.create_line(nfX, nfY, ntX, ntY,
                               width=self.lineWidth, fill=self.colors[self.color],
                               capstyle=ROUND, smooth=TRUE, splinesteps=36)

    # x and y are the normalized coordinates 
    def checkForButtonPress(self, x, y):
        x = float(x)
        y = float(y)
        # Pen button
        bx = self.penButtonX
        by = self.penButtonY
        bw = self.penButton.winfo_width()
        bh = self.penButton.winfo_height()
        if self.normalizedPointInBox(x, y, bx, by, bx + bw, by + bh):
            # call the button press
            self.usePen()
            return True
        
        # Color button
        bx = self.colorButtonX
        by = self.colorButtonY
        bw = self.colorButton.winfo_width()
        bh = self.colorButton.winfo_height()
        if self.normalizedPointInBox(x, y, bx, by, bx + bw, by + bh):
            # call the button press
            self.chooseColor()
            return True

        # Erase button
        bx = self.eraserButtonX
        by = self.eraserButtonY
        bw = self.eraserButton.winfo_width()
        bh = self.eraserButton.winfo_height()
        if self.normalizedPointInBox(x, y, bx, by, bx + bw, by + bh):
            # call the button press
            self.useEraser()
            return True

        # Erase button
        bx = self.sizeButtonX
        by = self.sizeButtonY
        bw = self.sizeButton.winfo_width()
        bh = self.sizeButton.winfo_height()
        if self.normalizedPointInBox(x, y, bx, by, bx + bw, by + bh):
            # call the button press
            self.changeSize()
            return True

        return False

    def normalizedPointInBox(self, nx, ny, x, y, x2, y2):
        # make sure canvas width/height are up to date 
        self.root.update()
        w = self.canvas.winfo_width() 
        h = self.canvas.winfo_height()
        
        # normalize the point into the same variables
        x = float(x) / float(w) * 100.0
        y = float(y) / float(h) * 100.0
        x2 = float(x2) / float(w) * 100.0
        y2 = float(y2) / float(h) * 100.0

        return nx > x and nx < x2 and ny > y and ny < y2 
        
    def clearDrawButton(self):
        self.clearDrawing()
        if self.master:
            self.sendToSlave('clear')

    def clearDrawing(self):
        self.root.update()
        self.canvas.create_rectangle(0, 0, 4000, 4000, fill='black')

    def handle(self, line):
        if line.rstrip() is '':
            return

        # if i am the master send to the slave also to keep him up to date
        if self.master: 
            self.sendToSlave(line)

        if line.startswith('down'):
            if self.debug:
                print('got down')
            coords = line.split(sep=',')
            if not self.checkForButtonPress(coords[1], coords[2]):
                self.prev = (coords[1], coords[2])

        elif line.startswith("up"):
            if self.debug:
                print('got up')
            coords = line.split(sep=',')
            self.prev = None

        elif line.startswith("color"):
            if self.debug:
                print('got color')
            color = line.split(sep=',')[1]
            if 'black' in color:
                self.useEraser()
            else:
                self.setColor(int(color))

        elif line.startswith("size"):
            if self.debug:
                print('got size')
            self.setSize(line.split(sep=',')[1])

        elif line.startswith("image"):
            if self.debug:
                print('received image')
            b64str = line.split(sep=',')[1]
            self.insert64image(b64str)

        elif line.startswith('clear'):
            self.clearDrawing()
        elif line.startswith('calib'):
            splits = line.split(sep=',')
            if self.debug:
                print('received calib')
            if splits[1] in 'nw':
                self.calibNW()
            elif splits[1] in 'ne':
                self.calibNE()
            elif splits[1] in 'sw':
                self.calibSW()
            elif splits[1] in 'se':
                self.calibSE()
            elif splits[1] in 'done':
                self.doneCalib()

        elif self.prev is not None:
            if self.debug:
                print(line)
            coords = line.split(sep=',')
            try:
                self.normalizedDrawLine(self.prev[0], self.prev[1], coords[0], coords[1])
                self.prev = (coords[0], coords[1])
            except IndexError as e:
                if self.debug:
                    print('bad coords, ignoring')
        else:
            if self.debug:
                print('+ unknown message')
                print(line)
                print('- unknown message')
            

    def sendToSlave(self, line): 
        line = line.rstrip() + '\n'
        self.sendQueue.append(str.encode(line))

    # only single slave supported rn
    # connecting a new slave will kill the other slave :O
    def addSlave(self, ipaddr):
        if self.debug:
            print("adding slave {}".format(ipaddr)) 
        self.slaveIP = ipaddr
        slavesocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        slavesocket.connect((ipaddr, 15273))
        
        slaveAttached = True
        # make sure slave gets the write pen type off the bat
        threading.Thread(target = self.slaveSendThread, args = [slavesocket]).start()
        #start image recognition
        self.w = WhiteboardView(self, debug=self.debug, prod=True)

        threading.Thread(target=self.w.runVideo).start()
#        sleep(0.001)
#        self.sendToSlave("color,{}".format(self.color))
#        self.sendToSlave("size,{}".format(self.lineWidth))

if __name__ == '__main__':
    print("Setting up tk")
    try:
        p = Paint(master=True, debug=True)
        #w = WhiteboardView(p, debug=True,prod=True)
        #threading.Thread(target=w.runVideoFromPath, args=('test5.h264',)).start()
        p.startLoop()
    finally:
        p.close()
        #w.close()
