import socket
import sys
import threading

# --- IDENTIFICATION ---
HUB_NUMBER = 1
HUB_NAME = "PLACEHOLDER"

# --- NETWORK CONFIG ---
LOCAL_PORT = 5005
OTHER_HUB_IP = "PLACEHOLDER"
OTHER_HUB_PORT = 5005

# --- NODE LIST ---
nodeIP = {
    # PLACEHOLDER
    # 1.1.1.1,
    # 1.1.1.2,
    # etc
}

# --- SOCKET SETUP ---
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", LOCAL_PORT))

def handleTraffic ():
    while True:
        try:
            data, addr = sock.recvfrom(2048)
            ip = addr[0]

            if ip == OTHER_HUB_IP:
                for node in nodeIP:
                    sock.sendto(data, (node, LOCAL_PORT))

            else:
                nodeIP[ip] = True

                sock.sendto(data, (OTHER_HUB_IP, OTHER_HUB_PORT))

        except Exception as e:
            print("Error: ", e)

threading.Thread(target=handleTraffic, daemon=True).start()

try:
    while True:
        pass
except KeyboardInterrupt:
    print("Shutting down HUB")
    sock.close()
    sys.exit()
