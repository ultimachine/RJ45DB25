#!/usr/bin/python3

import time
import serial
import signal
import os
import sys
import subprocess
from termcolor import colored
import psycopg2
import datetime

testjig = "RJ45-DB25"

print("RJ45-DB25 Test Server")
directory = os.path.split(os.path.realpath(__file__))[0]
version = subprocess.check_output(['git', '--git-dir='+directory+'/.git', 'rev-parse', 'HEAD']).strip().decode()
print("Git version - " + str(version))

print("Connecting to database...")
# Open our file outside of git repo which has database location, password, etc
dbfile = open(directory+'/postgres_info.txt', 'r')
postgresInfo = dbfile.read()
dbfile.close()
while True:
    try:
        testStorage = psycopg2.connect(postgresInfo)
        break
    except Exception as e:
        print(e)
        print("Could not connect! Type [Enter] to try again-> ")
        input()
        continue
        #sys.exit(0)

cursor = testStorage.cursor()


def signal_handler(signal, frame):
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)


while True:
    serialNumber = ""
    print("Enter RJ45-DB25 serial number : ")
    serialNumber = input()

    try:
        sNum = int(serialNumber)
        if( sNum not in range(45250001,45259000) ):
            print(colored("Invalid Entry. (Use 45250001-45259000).",'magenta'))
            continue
    except:
            print("Invalid Entry. (Use 45250001-45259000).")
            continue

    print("Press [Enter] to start test")
    input()

    fo = open("RJ45_DB25_log.txt", "a")
    fo.write(serialNumber + '\n')

    print("starting test...")

    ser = serial.Serial()
    ser.port = '/dev/ttyACM0'
    ser.baudrate = 115200
    ser.timeout = 0
    try: ser.open()
    except Exception as e: print(e)
    ser.flushOutput()
    ser.flushInput()

    ser.write(b'?\n')
    time.sleep(0.2)
    print(colored(ser.read(500).decode('utf-8'),'cyan'))

    full_output = ""
    test_result = "Failed"
    # test takes approx. 7 seconds. update output every 0.5 seconds.
    for count in range(4*2):
        #print colored("time: " + str(count * 0.5),'red')
        time.sleep(0.5)
        output = ser.read(500).strip().decode('utf-8')
        #print colored("output_length: " + str(len(output)),'red')
        if len(output):
          print(colored(output,'cyan'))
          full_output = full_output + output

    if("Passed" in full_output):
      test_result = "Passed"

    ser.flushOutput()
    ser.flushInput()
    ser.close()
    
    print("Test Result: " + test_result)

    print("Writing results to database...")
    testStorage = psycopg2.connect(postgresInfo)
    cursor = testStorage.cursor()
    cursor.execute("""INSERT INTO testdata(serial, timestamp, testresults, testversion, testjig) VALUES (%s, %s, %s, %s, %s)""", (serialNumber, 'now', test_result, version, testjig, ))
    testStorage.commit()
    cursor.close()


