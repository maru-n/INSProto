#!/usr/bin/env python

from sys import stdout
from data_receiver import DataReceiver
from optparse import OptionParser
import glob
from sys import platform
import serial


def get_available_serial_devices():
    if platform.startswith('win'):
        ports = ['COM' + str(i + 1) for i in range(256)]
    elif platform.startswith('linux') or platform.startswith('cygwin'):
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result


def select_serial_device():
    devices = get_available_serial_devices()
    while True:
        for i in range(len(devices)):
            print('%2d: %s' % (i, devices[i]))
        key_input = input('please select device: ')
        try:
            di = int(key_input)
            if di < len(devices):
                break
        except:
            pass
    return devices[di]

if __name__ == '__main__':
    parser = OptionParser()
    (opts, args) = parser.parse_args()

    data_receiver = DataReceiver()
    if len(args) < 1:
        serial_device = select_serial_device()
    else:
        serial_device = args[0]

    data_receiver.set_serial_settings(serial_device)

    while True:
        try:
            ax, ay, az, gx, gy, gz, mx, my, mz = data_receiver.fetch_all_data()
            msg = ''
            msg += 'accel(x:% 9.5f y:% 9.5f z:% 9.5f)  ' % (ax, ay, az)
            msg += 'gyro(x:% 9.5f y:% 9.5f z:% 9.5f)  ' % (gx, gy, gz)
            msg += 'mag(x:% 10.5f y:% 10.5f z:% 10.5f)' % (mx, my, mz)
        except Exception as e:
            msg = "no data available."
        finally:
            stdout.write('\r\033[K' + msg)
            stdout.flush()