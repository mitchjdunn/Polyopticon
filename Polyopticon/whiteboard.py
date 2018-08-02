from tkinter import *
import threading
import socket 
from tkinter.colorchooser import askcolor

class Paint(object):
    DEFAULT_COLOR = 'white'
    

    def __init__(self):
        # Setup server socket
        self.port = 15273
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.serverSocket.bind(('0.0.0.0', self.port))

        # Setup the Tk interface
        self.root = Tk()

        self.canvas = Canvas(self.root, bg='black')# , width=600, height=600)
        self.canvas.pack(fill=BOTH, expand=YES, padx = 5, pady = 5)

        self.penButton = Button(self.root, text='pen', command=self.usePen)
        self.penButton.configure(width = 10, height = 6, bd=0) 
        self.canvas.create_window(10, 10, anchor=NW, window=self.penButton)

        self.colorButton = Button(self.root, text='color', command=self.chooseColor)
        self.colorButton.configure(width = 10, height = 6, bd = 0) 
        self.canvas.create_window(10, 90, anchor=NW, window=self.colorButton)

        self.eraserButton = Button(self.root, text='eraser', command=self.useEraser)
        self.eraserButton.configure(width = 10, bd = 0, height = 6)
        self.canvas.create_window(10, 170, anchor=NW, window=self.eraserButton)

        self.sizes = [1, 3, 5, 8, 10, 20]
        self.currentSize = 0
        self.sizeButton = Button(self.root, text='Size (1)', command=self.changeSize)
        self.sizeButton.configure(width = 10, bd = 0, height = 6)
        self.canvas.create_window(10, 250, anchor=NW, window=self.sizeButton)

        # listen for clients in another thread
        threading.Thread(target = self.listen).start()
        # self.listen()

        self.setup()
        self.root.mainloop()

    def changeSize(self):
        self.currentSize = (self.currentSize + 1) % len(self.sizes)
        self.sizeButton.configure(text="Size (%d)"%self.sizes[self.currentSize])

    def setup(self):
        self.oldX = None
        self.oldY = None
        self.lineWidth = self.sizes[self.currentSize]
        self.color = self.DEFAULT_COLOR
        self.eraserOn = False
        self.activateButton = self.penButton
        self.canvas.bind('<B1-Motion>', self.paint)
        self.canvas.bind('<ButtonRelease-1>', self.reset)

    def usePen(self):
        self.activateButton(self.penButton)

    def chooseColor(self):
        self.eraserOn = False
        self.color = askcolor(color=self.color)[1]

    def useEraser(self):
        self.activateButton(self.eraser_button, eraser_mode=True)

    def activateButton(self, some_button, eraser_mode=False):
        self.activateButton.config(relief=RAISED)
        some_button.config(relief=SUNKEN)
        self.activateButton = some_button
        self.eraserOn = eraser_mode

    def paint(self, event):
        self.lineWidth = self.sizes[self.currentSize]
        paintColor = 'black' if self.eraserOn else self.color
        if self.oldX and self.oldY:
            self.canvas.create_line(self.oldX, self.oldY, event.x, event.y,
                               width=self.lineWidth, fill=paintColor,
                               capstyle=ROUND, smooth=TRUE, splinesteps=36)
        self.oldX = event.x
        self.oldY = event.y

    def reset(self, event):
        self.oldX, self.oldY = None, None

    # Accepts new sockets from server socket
    def listen(self):
        self.sock.listen(5)
        while True:
            client, address = self.sock.accept()
            client.settimeout(60)
            threading.Thread(target = self.listenToClient,args = (client,address)).start()

    # Recv data from client and translate that to lines in the Tk app
    def listenToClient(self, client, address):
        size = 1024
        while True:
            try:
                data = client.recv(size)
                if data:
                    # Set the response to echo back the recieved data 
                    response = data
                    client.send(response)
                else:
                    raise error('Client disconnected')
            except:
                client.close()
                return False


if __name__ == '__main__':
    Paint()

