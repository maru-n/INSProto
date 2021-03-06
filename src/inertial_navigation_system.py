#!/usr/bin/env python

from abc import ABCMeta, abstractmethod
import serial
import struct
import time
import numpy as np


class INS(object):
    __metaclass__ = ABCMeta

    def __init__(self):
        super(INS, self).__init__()

    def __del__(self):
        self.stop()

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def get_time(self):
        pass

    @abstractmethod
    def get_quaternion(self):
        pass

    @abstractmethod
    def get_all_sensor_data(self):
        pass

    @abstractmethod
    def get_velocity(self):
        pass

    @abstractmethod
    def get_position(self):
        pass


class AndroidINS(INS):
    def __init__(self, serial_device_name, serial_baudrate=115200, serial_timeout=0.1):
        super(AndroidINS, self).__init__()
        self.__serial_device_name = serial_device_name
        self._serial_baudrate = serial_baudrate
        self._serial_timeout = serial_timeout

    def start(self):
        self.__serial = serial.Serial(self.__serial_device_name,
                                      self._serial_baudrate,
                                      timeout=self._serial_timeout)

    def stop(self):
        try:
            self.__serial.close()
        except:
            pass

    def get_time(self):
        return time.time()

    def get_quaternion(self):
        # Dummy data!!
        return (0., 0., 0., 0.)

    def get_all_sensor_data(self):
        self.__serial.write([1])
        data_num = 12*3
        bytes = self.__serial.read(data_num)
        if len(bytes) == data_num:
            return struct.unpack('>fffffffff', bytes)
        else:
            self.__serial.flush()
            Exception("No data received.")

    def get_velocity(self):
        # Dummpy data!!
        return (0., 0., 0.)

    def get_position(self):
        # Dummpy data!!
        return (0., 0., 0.)


from vectornav import *

class VN100INS(INS):
    def __init__(self, serial_device_name):
        super(VN100INS, self).__init__()
        self.vn100 = Vn100()
        self.__serial_device_name = serial_device_name
        self.reset_data()
        self.__logging = False

    def start(self, logging=False):
        if logging:
            self.start_logging()
        self.__setup_vn100()

    def __setup_vn100(self):
        err_code = vn100_connect(self.vn100, self.__serial_device_name, 921600)
        if err_code != VNERR_NO_ERROR:
            raise Exception('Failed to connect to vn100. (Error code:%d)' % err_code)
        err_code = vn100_setAsynchronousDataOutputType(self.vn100, VNASYNC_OFF, True)
        if err_code != VNERR_NO_ERROR:
            raise Exception('Failed to disabe asynchronous ascii output. (Error code:%d)' % err_code)
        err_code = vn100_setBinaryOutputConfiguration(
            self.vn100,
            1,
            BINARY_ASYNC_MODE_SERIAL_2,
            4,
            BG1_TIME_STARTUP|BG1_DELTA_THETA|BG1_QTN,
            BG3_ACCEL|BG3_GYRO|BG3_MAG,
            BG5_NONE,
            #BG5_LINEAR_ACCEL_NED,
            True)
        if err_code != VNERR_NO_ERROR:
            raise Exception('Failed to set binary output configuration. (Error code:%d)' % err_code)
        err_code = vn100_registerAsyncDataReceivedListener(self.vn100, self.__data_listener)
        if err_code != VNERR_NO_ERROR:
            raise Exception('Failed to register asynchronous data receiver. (Error code:%d)' % err_code)

    def stop(self):
        err_code = vn100_unregisterAsyncDataReceivedListener(self.vn100, self.__data_listener);
        # if err_code != VNERR_NO_ERROR:
        #     raise Exception('Error code: %d' % err_code)
        err_code = vn100_disconnect(self.vn100);
        # if err_code != VNERR_NO_ERROR:
        #     raise Exception('Error code: %d' % err_code)

    def reset_data(self):
        self.__time = 0.
        self.__time_offset = None
        self.__quaternion = np.zeros(4)
        self.__acceleration = np.zeros(3)
        self.__angular_rate = np.zeros(3)
        self.__magnetic = np.zeros(3)
        self.__dv = np.zeros(3)
        self.__vel = np.zeros(3)
        self.__pos = np.zeros(3)

    def get_time(self):
        return self.__time

    def get_quaternion(self):
        return self.__quaternion

    def get_all_sensor_data(self):
        return (self.__acceleration, self.__angular_rate, self.__magnetic)

    def get_navigation_state(self):
        return (self.__dv, self.__vel, self.__pos)

    def get_delta_velocity(self):
        return self.__dv

    def get_velocity(self):
        return self.__vel

    def get_position(self):
        return self.__pos

    def __init_log(self):
        self.__time_log = []
        self.__quaternion_log = []
        self.__acceleration_log = []
        self.__angular_rate_log = []
        self.__magnetic_log = []
        self.__dv_log = []
        self.__vel_log = []
        self.__pos_log = []

    def start_logging(self):
        if not self.__logging:
            self.__init_log()
        self.__logging = True

    def stop_logging(self):
        self.__logging = False

    def is_logging(self):
        return self.__logging

    def save_logfile(self, filename):
        if self.__logging:
            Exception('Couldn\'t save log during logging. Stop logging before save it.')
        np.savez(filename,
                 time = np.array(self.__time_log),
                 qtn = np.array(self.__quaternion_log),
                 acl = np.array(self.__acceleration_log),
                 ang = np.array(self.__angular_rate_log),
                 mag = np.array(self.__magnetic_log),
                 dv = np.array(self.__dv_log),
                 vel = np.array(self.__vel_log),
                 pos = np.array(self.__pos_log)
                 )


    def __data_listener(self, sender, data):
        self.__update(data)


    def __update(self, data):
        if self.__time_offset is None:
            self.__time_offset = data.timeStartup * 1e-9
        pre_time = self.__time
        self.__time = data.timeStartup * 1e-9 - self.__time_offset
        dt = self.__time - pre_time
        #dt = data.deltaTime
        if self.__time < pre_time:
            print("error: " + str(pre_time))

        self.__quaternion[0], self.__quaternion[1], self.__quaternion[2], self.__quaternion[3] = data.quaternion.x, data.quaternion.y, data.quaternion.z, data.quaternion.w
        self.__acceleration[0], self.__acceleration[1], self.__acceleration[2] = data.acceleration.c0, data.acceleration.c1, data.acceleration.c2
        self.__angular_rate[0], self.__angular_rate[1], self.__angular_rate[2] = data.angularRate.c0, data.angularRate.c1, data.angularRate.c2
        self.__magnetic[0], self.__magnetic[1], self.__magnetic[2] = data.magnetic.c0, data.magnetic.c1, data.magnetic.c2
        self.__dv[0], self.__dv[1], self.__dv[2] = data.deltaVelocity.c0, data.deltaVelocity.c1, data.deltaVelocity.c2
        #self.__dv[0], self.__dv[1], self.__dv[2] = data.linearAccelNed.c0*dt, data.linearAccelNed.c1*dt, data.linearAccelNed.c2*dt

        pre_vel = list(self.__vel)
        if self.__detect_zero_velocity():
            self.__vel[0] = 0.
            self.__vel[1] = 0.
            self.__vel[2] = 0.
        else:
            self.__vel[0] += self.__dv[0]
            self.__vel[1] += self.__dv[1]
            self.__vel[2] += self.__dv[2]

        self.__pos[0] += (self.__vel[0] + pre_vel[0]) * dt * 0.5
        self.__pos[1] += (self.__vel[1] + pre_vel[1]) * dt * 0.5
        self.__pos[2] += (self.__vel[2] + pre_vel[2]) * dt * 0.5

        if self.__logging:
            self.__time_log.append(self.__time)
            self.__quaternion_log.append(list(self.__quaternion))
            self.__acceleration_log.append(list(self.__acceleration))
            self.__angular_rate_log.append(list(self.__angular_rate))
            self.__magnetic_log.append(list(self.__magnetic))
            self.__dv_log.append(list(self.__dv))
            self.__vel_log.append(list(self.__vel))
            self.__pos_log.append(list(self.__pos))


    ZVD_ANGULAR_RATE_X_MIN = -0.0012
    ZVD_ANGULAR_RATE_X_MAX =  0.0012
    ZVD_ANGULAR_RATE_Y_MIN = -0.0012
    ZVD_ANGULAR_RATE_Y_MAX =  0.0012
    ZVD_ANGULAR_RATE_Z_MIN = -0.0016
    ZVD_ANGULAR_RATE_Z_MAX =  0.0016
    ZVD_COUNT = 1

    def __detect_zero_velocity(self):
        try:
            self.__zvd_cnt
        except Exception as e:
            self.__zvd_cnt = 0

        if VN100INS.ZVD_ANGULAR_RATE_X_MIN < self.__angular_rate[0] and \
           VN100INS.ZVD_ANGULAR_RATE_X_MAX > self.__angular_rate[0] and \
           VN100INS.ZVD_ANGULAR_RATE_Y_MIN < self.__angular_rate[1] and \
           VN100INS.ZVD_ANGULAR_RATE_Y_MAX > self.__angular_rate[1] and \
           VN100INS.ZVD_ANGULAR_RATE_Z_MIN < self.__angular_rate[2] and \
           VN100INS.ZVD_ANGULAR_RATE_Z_MAX > self.__angular_rate[2]:
            self.__zvd_cnt += 1
        else:
            self.__zvd_cnt = 0

        if self.__zvd_cnt >= VN100INS.ZVD_COUNT:
            return True
        else:
            return False
