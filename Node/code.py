# Pi Imports
import time

import board
import audiobusio
import keypad

# Network Imports
import wifi
import socketpool

# Other Imports
import array

# --- DEGUB MODE ---
DEBUG = True
DEBUG_PRINT = 0

# --- NODE INFO ---
mutedMic = False
mutedAmp = False
Node_Number = 1

# --- WIFI CONSTANTS ---
WIFI_SSID = "PLACEHOLDER" # Wifi Name
WIFI_PASSWORD = "PLACEHOLDER" # Wifi Password
HUB_IP = "PLACEHOLDER" # IP of the Hub, but TailScale
PORT = 5005

# --- NETWORKING ---
try:
    wifi.radio.connect(WIFI_SSID, WIFI_PASSWORD) # Connects to Wi-Fi
    pool = socketpool.SocketPool(wifi.radio) # Sets the networking pool
    sock = pool.socket(pool.AF_INET, pool.SOCK_DGRAM) # Sets socket
    sock.setblocking(False) # To not freeze when nothing is received
    sock.bind(("0.0.0.0", PORT)) # Sets listening ip

    if DEBUG and DEBUG_PRINT == 0:
        print("[DEBUG] Socket bind successful")

    wifiConnected = "Connected Successfully"
except Exception as e:
    wifiConnected = None
    if DEBUG and DEBUG_PRINT == 0:
        print("[DEBUG] Wifi or Socket Error: ", e)

# --- BUTTONS SETUP ---
buttons = keypad.Keys((board.GP2, board.GP3), value_when_pressed=False, pull=True)

# --- DEVICES SETUP ---
mic = None
amp = None

# --- Mic Setup ---
try:
    # Pins: SCK = GP26, WS = GP27, SD = 28
    mic = audiobusio.I2SIn(board.GP26, board.GP27, board.GP28)
except Exception as e:
    if DEBUG and DEBUG_PRINT == 0:
        print("[DEBUG] Mic Setup Failed: ", e)

# --- Amp Setup ---
try:
    # Pins: BCLK = GP20, LRC = GP21, DIN = GP22
    amp = audiobusio.I2SOut(board.GP20, board.GP21, board.GP22)
except Exception as e:
    if DEBUG and DEBUG_PRINT == 0:
        print("[DEBUG] Amp Setup Failed: ", e)

# 512 bit sound arrays
sending_buffer = array.array('h', [0] * 512)
receiving_buffer = array.array('h', [0] * 512)

# --- FUNCTIONS ---
def getAudio():
    try:
        size, addr = sock.recvfrom_into(receiving_buffer)
        if size > 0:
            audioSample = audiobusio.RawSample(receiving_buffer)
            amp.play(audioSample)
    except OSError:
        if DEBUG and DEBUG_PRINT == 0:
            print("[DEBUG] No Audio Received")
        pass

def recordAudio():
    try:
        mic.record(sending_buffer)
    except Exception as ex:
        if DEBUG and DEBUG_PRINT == 0:
            print("[DEBUG] recording failed: ", ex)


# --- LOOP ---
while True:
    # Stops if nothing is connected
    if not wifiConnected and not mic and not amp:
        continue

    # Button control
    event = buttons.events.get()
    if event and event.pressed:
        if DEBUG and DEBUG_PRINT == 0:
            print(f"[DEBUG] Key: {event.key_number if event.key_number else "None"}")

        if event.key_number == 0:
            mutedMic = not mutedMic
            if not mic:
                mutedMic = True

            if DEBUG and DEBUG_PRINT == 0:
                print(f"[DEBUG] Mic Status: {"Muted" if mutedMic else "Active"}")

        if event.key_number == 1:
            mutedAmp = not mutedAmp
            if not amp:
                mutedAmp = True

            if DEBUG and DEBUG_PRINT == 0:
                print(f"[DEBUG] Amp Status: {"Muted" if mutedAmp else "Active"}")

    # Receive Audio
    if amp:
        if not mutedAmp:
            getAudio()

    # Record Audio
    if mic and not mutedMic:
        recordAudio()

        # Sends recording to Hub
        if wifiConnected:
            sock.sendto(sending_buffer, (HUB_IP, PORT))

    # Slows down the prints so that print statements don't flood
    if DEBUG:
        DEBUG_PRINT += 1
        if DEBUG_PRINT >= 100:
            DEBUG_PRINT = 0
