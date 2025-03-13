import serial
import time


connect = serial.Serial("COM5", 115200)
time.sleep(2)

while True:
    val = connect.readline().decode('utf-8')
    print(val)