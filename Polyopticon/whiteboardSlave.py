from whiteboard import Paint
if __name__ == '__main__':
    print("Setting up tk")
    p = Paint(master=False, debug=True)
    p.startLoop()
