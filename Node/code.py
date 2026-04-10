# Pi Imports
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

# --- NODE INFO ---
mutedMic = False
mutedAmp = False
Node_Number = 1

# --- WIFI CONSTANTS ---
WIFI_SSID = "PLACEHOLDER" # Wifi Name
WIFI_PASSWORD = "PLACEHOLDER" # Wifi Password
HUB_IP = "PLACEHOLDER" # IP of the HUB, but TailScale
PORT = 5005

# --- NETWORKING ---
try:
    wifi.radio.connect(WIFI_SSID, WIFI_PASSWORD) # Connects to wifi
    pool = socketpool.SocketPool(wifi.radio) # Sets the networking pool
    sock = pool.socket(pool.AF_INET, pool.SOCK_DGRAM) # Sets socket
    sock.setblocking(False) # To not freeze when nothing is received
    sock.bind(("0.0.0.0", PORT)) # Sets listening ip

    if DEBUG:
        print("[DEBUG] Socket bind successful")

    Wifi = "Connected Successfully"
except Exception as e:
    Wifi = None
    if DEBUG: print("[DEBUG] Wifi or Socket Error: ", e)

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
    if DEBUG:
        print("[DEBUG] Mic Setup Failed: ", e)

# --- Amp Setup ---
try:
    # Pins: BCLK = GP20, LRC = GP21, DIN = GP22
    amp = audiobusio.I2SOut(board.GP20, board.GP21, board.GP22)
except Exception as e:
    if DEBUG:
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
        if DEBUG:
            print("[DEBUG] No Audio Received")
        pass

def recordAudio():
    try:
        mic.record(sending_buffer)
    except Exception as ex:
        if DEBUG:
            print("[DEBUG] recording failed: ", ex)


# --- LOOP ---
while True:
    # Button control
    event = buttons.events.get()
    if event and event.pressed:
        if event.key_number == 0:
            mutedMic = not mutedMic
            if not mic:
                mutedMic = True
        if event.key_number == 1:
            mutedAmp = not mutedAmp

    if DEBUG:
        print(f"[DEBUG] Key: {event.key_number}")
        print(f"[DEBUG] Mic Status: {"Muted" if not mutedMic else "Active"}")
        print(f"[DEBUG] Amp Status: {"Muted" if not mutedAmp else "Active"}")

    # Receive Audio
    if amp:
        if not mutedAmp:
            getAudio()

    # Record Audio
    if mic and not mutedMic:
        recordAudio()

        # Sends recording to Hub
        if wifi:
            sock.sendto(sending_buffer, (HUB_IP, PORT))

    if not wifi and not mic and not amp:
        continue
