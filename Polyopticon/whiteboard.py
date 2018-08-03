from tkinter import *
import threading
import socket 
import traceback
from time import sleep
from tkinter.colorchooser import askcolor

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
        size = 1024
        while True:
            try:
                data = client.recv(size)
                if data:
                    for line in data.decode("utf-8").split(sep='\n'):
                        self.paint.handle(line)
                else:
                    raise RuntimeError('Client Disconnect')
            except Exception as e:
                print('client disconnected due to error') 
                # print(e)
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
        self.master = master
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
        else:
            d = DrawSocket(self)
            # TODO Send the broadcast packet
            threading.Thread(target = self.waitForMaster, args=[d] ).start()


    def waitForMaster(self, drawsocket):
        broadcast = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
        broadcast.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
        broadcast.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        while not drawsocket.socketConnected():
            print("pinging for master")
            broadcast.sendto(str.encode('whiteboard'), ('255.255.255.255', 15272))
            sleep(3)
        print("stopping broadcasts")
        
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
        # TODO make like 5 colors to cycle through
        # TODO Set color on slaves
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
                self.root.update()
                calcx = float(event.x) / self.canvas.winfo_width() * 100
                calcy = float(event.y) / self.canvas.winfo_height() * 100
                try:
                    self.sendToSlave('{},{}'.format(calcx, calcy))
                except Exception as e:
                    pass
        elif self.master:
            self.root.update()
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
        print("canvas WxH = {} {}".format(w, h))
        
        # normalized from x 
        nfX = (float(fromX) / 100.0) * w
        # normalized from y 
        nfY = (float(fromY) / 100.0) * h 

        # normalized from x 
        ntX = (float(toX) / 100.0) * w 
        # normalized from y 
        ntY = (float(toY) / 100.0) * h 
            
        print("drawing line line from {},{} to {},{}".format(nfX, nfY, ntX, ntY))
        self.canvas.create_line(nfX, nfY, ntX, ntY,
                               width=self.lineWidth, fill=self.colors[self.color],
                               capstyle=ROUND, smooth=TRUE, splinesteps=36)

    # TODO
    def checkForButtonPress(self, x, y):
        return False

    def handle(self, line):
        if line.rstrip() is '':
            return

        # if i am the master send to the slave also to keep him up to date
        if self.master: 
            self.sendToSlave(line)

        if 'down' in line: 
            print('got down')
            coords = line.split(sep=',')
            if not self.checkForButtonPress(coords[1], coords[2]):
                print("setting prev")
                print(coords)
                self.prev = (coords[1], coords[2])
                print(self.prev)
        elif 'up' in line:
            print('got up')
            coords = line.split(sep=',')
            self.prev = None
        elif 'color' in line:
            print('got color')
            self.setColor(int(line.split(sep=',')[1]))
        elif 'size' in line: 
            print('got size')
            self.setSize(line.split(sep=',')[1])
        elif self.prev is not None:
            coords = line.split(sep=',')
            self.normalizedDrawLine(self.prev[0], self.prev[1], coords[0], coords[1])
            self.prev = (coords[0], coords[1])
        else:
            print('+ unknown message')
            print(line)
            print('- unknown message')
            

    def sendToSlave(self, line): 
        if self.slavesocket: 
            line = line + '\n'
            print("SEND {}".format(line))
            try: 
                self.slavesocket.send(str.encode(line))
            except Exception as e:
                print("slave is dead")
                self.slavesocket = None

    # only single slave supported rn
    # connecting a new slave will kill the other slave :O
    def addSlave(self, ipaddr):
        print("adding slave {}".format(ipaddr)) 
        self.slavesocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.slavesocket.connect((ipaddr, 15273))
        
        # make sure slave gets the write pen type off the bat
        self.sendToSlave("color,{}".format(self.color))
        self.sendToSlave("size,{}".format(self.lineWidth))
        
if __name__ == '__main__':
    print("Setting up tk")
    p = Paint(master=True)
    p.startLoop()
