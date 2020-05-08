from socket import *
import struct
import mss
from PIL import Image
import pyautogui

nameSever = 'testServer'
flagConnect = False
connClient = None
addrClient = None
rfb_protocol = 'RFB 003.008\n'
clientEncode = None
clientPixelFormat = None

# Packet Length
ENCODE_LENGTH = 4
PIXEL_LENGTH = 20
FRAMEREQ_LENGTH = 10
KEYEVENT_LENGTH = 8
POINTEREVENT_LENGTH = 6


def getHost():
    s = socket(AF_INET, SOCK_STREAM)
    s.connect(('www.google.com', 80))
    addr = s.getsockname()[0]
    s.close()
    return addr


def setMessageType(type):
    buf = b''
    with mss.mss() as sct:
        pix = sct.grab(sct.monitors[1])
    img = Image.frombytes('RGB', pix.size, pix.bgra, 'raw', 'BGRX')

    if type == 0:
        print('Set pixel format')
        buf += connClient.recv(PIXEL_LENGTH - 1)
    if type == 2:
        print('Set encode format')
        buf += connClient.recv(ENCODE_LENGTH - 1)
    if type == 3:
        print('Set FrameUpdate format')
        buf += connClient.recv(FRAMEREQ_LENGTH - 1)
        recHand, rectData = frameBufferUpdate(img, 0, 0)
        connClient.send(recHand)
        connClient.send(rectData)
    if type == 4:
        print('Set keyEvent format')
        buf += connClient.recv(KEYEVENT_LENGTH - 1)
        print(buf)
        pyautogui.typewrite(buf[6:7].decode('utf-8'))
    if type == 5:
        print('Set pointEvent format')
        buf += connClient.recv(POINTEREVENT_LENGTH - 1)
        print(buf)
        xC = int.from_bytes(buf[1:3], "big")
        yC = int.from_bytes(buf[4:5], "big")

        if not int.from_bytes(buf[0:1], "big") == 0:
            if int.from_bytes(buf[0:1], "big") == 1:
                pyautogui.click(button='left')
            if int.from_bytes(buf[0:1], "big") == 4:
                pyautogui.click(button='right')
        print(int.from_bytes(buf[0:1], "big"))
        print(xC)
        print(yC)
        pyautogui.moveTo(xC, yC)
    return buf


def frameBufferUpdate(img, xCord, yCord):
    # rectangle  header
    buf = struct.pack('!B', 0)
    buf += struct.pack('x')
    buf += struct.pack('!H', 1)
    buf += struct.pack('H', xCord)
    buf += struct.pack('!H', yCord)
    buf += struct.pack('!H', img.size[0])
    buf += struct.pack('!H', img.size[1])
    buf += struct.pack('!i', 0)

    # rectangle pixel data
    bufData = img.tobytes('raw', 'RGBX')
    return buf, bufData


def main():
    print('Server is started')
    global flagConnect, connClient, addrClient
    s = socket(AF_INET, SOCK_STREAM)
    s.bind((getHost(), 5900))
    s.listen()
    protoVersion = rfb_protocol.encode('UTF-8')
    print(len(nameSever))

    # Server works
    while True:
        if not flagConnect:
            connClient, addrClient = s.accept()
            print('Connected new Client %s', addrClient)
            connClient.send(protoVersion)
            data = connClient.recv(len(protoVersion))
            if data == protoVersion:
                print("Protocols are detected")
            print(data)

            # Security handShake
            buf = struct.pack("!B", 1)
            buf += struct.pack("!B", 1)
            connClient.send(buf)
            print(buf)
            initClient = connClient.recv(1)
            print(initClient)

            buf = struct.pack("!I", 0)
            print(buf)
            connClient.send(buf)
            initClient = connClient.recv(1)
            print(initClient)

            # Server init

            buf = struct.pack('!H', 1920)  # ширина
            buf += struct.pack('!H', 1080)  # высота
            #
            buf += struct.pack('!B', 32)  # Бит в пикселе
            buf += struct.pack('!B', 24)  # глубина
            buf += struct.pack('!B', 0)  # big-endian-flag
            buf += struct.pack('!B', 1)  # true-colour-flag
            buf += struct.pack('!H', 255)  # red-max
            buf += struct.pack('!H', 255)  # green-max
            buf += struct.pack('!H', 255)  # blue-max
            buf += struct.pack('!B', 16)  # red-shift 11
            buf += struct.pack('!B', 5)  # green-shift 0
            buf += struct.pack('!B', 0)  # blue-shift 5
            buf += struct.pack('x')  # padding
            buf += struct.pack('x')  # padding
            buf += struct.pack('x')  # padding
            #
            buf += struct.pack('!I', len(nameSever))
            connClient.send(buf)

            ns = nameSever.encode('UTF-8')
            connClient.send(ns)

            flagConnect = True
        else:
            # Определяем тип сообщения setEncode, pixelEvent, keyEvent или messageBufferEvent
            buf = b''
            buf += connClient.recv(1)  # Get message type
            buf += setMessageType(buf[0])


if __name__ == '__main__':
    main()


