from datetime import datetime
from tracemalloc import start
from pythonosc import dispatcher
from pythonosc import osc_server
from pyfirmata import Arduino, util
from playsound import playsound
from pynput.keyboard import Key, Controller
import time
from pyfirmata import Arduino, util

ip = "172.20.10.11"
port = 5981

activate_pageturn = True
activate_sustain = True
toggle_Sustain = False
startTime = 0
startSustainResetTime = time.time()
timeDiffThreshold = 0.3
accValueThreshold = 0.07
sustainResetTimeThreshold = 0.2
minAccX = 100

# Connect to Arduino Uno board on specified port.
board = Arduino("/dev/cu.usbmodem2101")
keyboard = Controller()

        
#switch sustain to off for 200ms and then on again    
def sustain_handle():
        board.digital[13].write(0)
        time.sleep(0.2)
        board.digital[13].write(1)

#callback when acceleromter values are sent
def eeg_handler_acc(address: str,*args):
    global activate_pageturn, activate_sustain, startTime, startSustainResetTime, minAccX
    if(startTime == 0):
        startTime = time.time()

    dateTimeObj = datetime.now()
    printStr = dateTimeObj.strftime("%Y-%m-%d %H:%M:%S.%f")
    acc = []
    for arg in args:
        acc.append(float(arg))

    #Turn pages based on head rotation of left and right
    if (acc[1] < 0.05 and acc[1] > -0.05 ):
        activate_pageturn = True
    if (acc[1] > 0.2 and activate_pageturn):
       activate_pageturn = False
       keyboard.press(Key.right)
       keyboard.release(Key.right)

    
    elif (acc[1] < -0.2 and activate_pageturn):
        activate_pageturn = False
        keyboard.press(Key.left)
        keyboard.release(Key.left)
        print("left key pressed")

    #find minAccX value in the past 300ms
    if (time.time() - startTime < timeDiffThreshold):
        if(acc[0] < minAccX):
            minAccX = acc[0]
    #handle sustain when the user headbangs in front
    if(time.time() - startTime >= timeDiffThreshold):
        if (acc[0]-minAccX > accValueThreshold and activate_sustain):  
            sustain_handle()
            activate_sustain = False
            startSustainResetTime = time.time()
        minAccX = 100
        startTime = time.time()

    if ((not activate_sustain) and (time.time() - startSustainResetTime > sustainResetTimeThreshold)):
        activate_sustain = True


#handle sustain when user blinks
def eeg_handler_blink(address: str,*args):
    print("blinked")
    sustain_handle()

#start server to listen for muse band signals over wifi    
if __name__ == "__main__":
    dispatcher = dispatcher.Dispatcher()
    dispatcher.map("/muse/acc", eeg_handler_acc)
    dispatcher.map("/muse/elements/blink", eeg_handler_blink)
    server = osc_server.ThreadingOSCUDPServer((ip, port), dispatcher)
    server.serve_forever()