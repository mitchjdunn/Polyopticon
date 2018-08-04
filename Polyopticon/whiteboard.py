from tkinter import *
import io
from tkinter.filedialog import askopenfilename
from PIL import Image 
from PIL import ImageTk
import threading
import socket 
import traceback
from time import sleep
from tkinter.colorchooser import askcolor
import base64

class DrawSocket(object): 
    def __init__(self, paint):
        # Setup server socket
        self.paint = paint
        self.port = 15273
        self.connected = False
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.serverSocket.bind(('0.0.0.0', self.port))
        # listen for clients in another thread
        threading.Thread(target = self.listen).start()
        # self.listen()

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
        print("New client connected")
        size = 2048
        data = b''
        while True:
            try:
                data = data + client.recv(size)
                if data is b'' or data.decode("utf-8").rstrip() is '':
                    print("no data, client dead")
                    return 

                string = data.decode("utf-8")
                lines = string.split(sep='\n')

                if not string.endswith('\n'):
                    # print("adding line to next buffer")
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
    def __init__(self, paint):
        print("Setting up broadcast listener")
        self.paint = paint
        self.client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        self.client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.client.bind(("", 15272))
        threading.Thread(target = self.listen).start()

    def listen(self):
        while True:
            data, addr = self.client.recvfrom(1024)
            print("received message: %s, from: %s"%(data, addr))
            if 'whiteboard' in data.decode("utf-8"):
                self.paint.addSlave(addr[0])

class Paint(object):

    def __init__(self, master=False):
        self.slaveAttached = False
        self.slaveIP = None
        self.master = master
        self.sendQueue = []
        # Setup the Tk interface
        self.color = 0
        self.currentColor = 0
        self.root = Tk()
        self.slavesocket = None
        self.colors = ['red', 'blue', 'white', 'green', 'purple', 'orange']

        self.canvas = Canvas(self.root, bg='black')# , width=600, height=600)
        self.canvas.pack(fill=BOTH, expand=YES, padx = 5, pady = 5)

        self.penButton = Button(self.root, text='pen', command=self.usePen, bg="dark blue", fg = "white")
        self.penButton.configure(width = 10, height = 6, bd=0) 
        self.canvas.create_window(10, 10, anchor=NW, window=self.penButton)

        self.colorButton = Button(self.root, text='color',command=self.chooseColor, bg="dark blue", fg = "white")
        self.colorButton.configure(width = 10, height = 6, bd = 0) 
        self.canvas.create_window(10, 90, anchor=NW, window=self.colorButton)

        self.eraserButton = Button(self.root, text='eraser', command=self.useEraser, bg="dark blue", fg = "white")
        self.eraserButton.configure(width = 10, bd = 0, height = 6)
        self.canvas.create_window(10, 170, anchor=NW, window=self.eraserButton)

        self.sizes = [1, 3, 5, 8, 10, 20]
        self.currentSize = 0
        self.sizeButton = Button(self.root, text='Size (1)', command=self.changeSize, bg="dark blue", fg = "white")
        self.sizeButton.configure(width = 10, bd = 0, height = 6)
        self.canvas.create_window(10, 250, anchor=NW, window=self.sizeButton)

        self.history = ""

        print("setting up socket")
        if master: 
            BroadcastListener(self) 

            self.menubar = Menu(self.root)
        
            self.filemenu = Menu(self.menubar, tearoff=0)
            self.filemenu.add_command(label="Upload Picture", command=self.insertImage)
            self.filemenu.add_command(label="Save Picture", command=self.saveCanvasToFile)
            self.filemenu.add_separator()
            self.filemenu.add_command(label="Exit", command=self.root.quit)
            self.menubar.add_cascade(label="File", menu=self.filemenu)
            self.root.config(menu=self.menubar)
        else:
            d = DrawSocket(self)
            threading.Thread(target = self.waitForMaster, args=[d] ).start()

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
        # TODO 
        pass


    def waitForMaster(self, drawsocket):
        broadcast = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
        broadcast.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
        broadcast.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        while True:
            print("starting broadcasts")
            while not drawsocket.socketConnected():
                print("pinging for master")
                broadcast.sendto(str.encode('whiteboard'), ('255.255.255.255', 15272))
                sleep(3)
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
                    # print("SEND {}".format(line))
                    socket.send(line)
                    currentPos = currentPos + 1
                except Exception as e:
                    print("slave is dead")
                    print(e)
                    return
                
            
    def startLoop(self): 
        self.setup()
        self.root.mainloop()
        
    def changeSize(self):
        self.currentSize = (self.currentSize + 1) % len(self.sizes)
        self.sizeButton.configure(text="Size (%d)"%self.sizes[self.currentSize])
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

    # TODO
    def checkForButtonPress(self, x, y):
        return False

    def clearDrawing(self):
        self.root.update()
        self.canvas.create_rectangle(0, 0, self.canvas.winfo_width, self.canvas.winfo_height, fill='black')
    def handle(self, line):
        if line.rstrip() is '':
            return

        # if i am the master send to the slave also to keep him up to date
        if self.master: 
            self.sendToSlave(line)

        if line.startswith('down'):
            print('got down')
            coords = line.split(sep=',')
            if not self.checkForButtonPress(coords[1], coords[2]):
                print("setting prev")
                print(coords)
                self.prev = (coords[1], coords[2])
                print(self.prev)
        elif line.startswith("up"):
            print('got up')
            coords = line.split(sep=',')
            self.prev = None
        elif line.startswith("color"):
            print('got color')
            self.setColor(int(line.split(sep=',')[1]))
        elif line.startswith("size"):
            print('got size')
            self.setSize(line.split(sep=',')[1])
        elif line.startswith("image"):
            print('received image')
            b64str = line.split(sep=',')[1]
            print(b64str) 
            self.insert64image(b64str)
        elif self.prev is not None:
            # print(line)
            coords = line.split(sep=',')
            try:
                self.normalizedDrawLine(self.prev[0], self.prev[1], coords[0], coords[1])
                self.prev = (coords[0], coords[1])
            except IndexError as e:
                print('bad coords, ignoring')
        else:
            print('+ unknown message')
            print(line)
            print('- unknown message')
            

    def sendToSlave(self, line): 
        line = line.rstrip() + '\n'
        # print("SEND {}".format(line))
        self.sendQueue.append(str.encode(line))

    # only single slave supported rn
    # connecting a new slave will kill the other slave :O
    def addSlave(self, ipaddr):
        print("adding slave {}".format(ipaddr)) 
        self.slaveIP = ipaddr
        slavesocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        slavesocket.connect((ipaddr, 15273))
        
        slaveAttached = True
        # make sure slave gets the write pen type off the bat
        threading.Thread(target = self.slaveSendThread, args = [slavesocket]).start()
#        sleep(0.001)
#        self.sendToSlave("color,{}".format(self.color))
#        self.sendToSlave("size,{}".format(self.lineWidth))

if __name__ == '__main__':
    print("Setting up tk")
    p = Paint(master=True)
    p.startLoop()
