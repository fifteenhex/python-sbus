#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Based on:
	Sokrates80/sbus_driver_micropython git hub
	https://os.mbed.com/users/Digixx/code/SBUS-Library_16channel/file/83e415034198/FutabaSBUS/FutabaSBUS.cpp/
	https://os.mbed.com/users/Digixx/notebook/futaba-s-bus-controlled-by-mbed/
	https://www.ordinoscope.net/index.php/Electronique/Protocoles/SBUS
"""

# dsimonet

import array
import serial
import codecs
import time


class SBUSReceiver:
    def __init__(self, _uart_port='/dev/ttyS0'):

        # init serial of raspberry pi
        self.ser = serial.Serial(
            port=_uart_port,
            baudrate=100000,
            parity=serial.PARITY_EVEN,
            stopbits=serial.STOPBITS_TWO,
            bytesize=serial.EIGHTBITS,
            timeout=1,
        )

        # constants
        self.START_BYTE = b'\x0f'
        self.END_BYTE = b'\x00'
        self.SBUS_FRAME_LEN = 25
        self.SBUS_NUM_CHAN = 18
        self.OUT_OF_SYNC_THD = 10
        self.SBUS_NUM_CHANNELS = 18
        self.SBUS_SIGNAL_OK = 0
        self.SBUS_SIGNAL_LOST = 1
        self.SBUS_SIGNAL_FAILSAFE = 2

        # Stack Variables initialization
        self.lastFrameTime = 0
        self.sbusChannels = array.array('H', [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])  # RC Channels
        self.failSafeStatus = self.SBUS_SIGNAL_FAILSAFE
        self.frameCount = 0

    def get_rx_channels(self):
        """
        Used to retrieve the last SBUS channels values reading
        :return:  an array of 18 unsigned short elements containing 16 standard channel values + 2 digitals (ch 17 and 18)
        """

        return self.sbusChannels

    def get_rx_channel(self, num_ch):
        """
        Used to retrieve the last SBUS channel value reading for a specific channel
        :param: num_ch: the channel which to retrieve the value for
        :return:  a short value containing
        """

        return self.sbusChannels[num_ch]

    def get_failsafe_status(self):
        """
        Used to retrieve the last FAILSAFE status
        :return:  a short value containing
        """

        return self.failSafeStatus

    def decode_frame(self, frame):
        self.sbusChannels[0] = (((frame[1]) | (frame[2]) << 8) & 0x07FF)
        self.sbusChannels[1] = (((frame[2]) >> 3 | (frame[3]) << 5) & 0x07FF)
        self.sbusChannels[2] = (((frame[3]) >> 6 | (frame[4]) << 2 | (
            frame[5]) << 10) & 0x07FF)
        self.sbusChannels[3] = (((frame[5]) >> 1 | (frame[6]) << 7) & 0x07FF)
        self.sbusChannels[4] = (((frame[6]) >> 4 | (frame[7]) << 4) & 0x07FF)
        self.sbusChannels[5] = (((frame[7]) >> 7 | (frame[8]) << 1 | (
            frame[9]) << 9) & 0x07FF)
        self.sbusChannels[6] = (((frame[9]) >> 2 | (frame[10]) << 6) & 0x07FF)
        self.sbusChannels[7] = (((frame[10]) >> 5 | (frame[11]) << 3) & 0x07FF)
        self.sbusChannels[8] = (((frame[12]) | (frame[13]) << 8) & 0x07FF)
        self.sbusChannels[9] = (((frame[13]) >> 3 | (frame[14]) << 5) & 0x07FF)
        self.sbusChannels[10] = (((frame[14]) >> 6 | (frame[15]) << 2 | (
            frame[16]) << 10) & 0x07FF)
        self.sbusChannels[11] = (((frame[16]) >> 1 | (frame[17]) << 7) & 0x07FF)
        self.sbusChannels[12] = (((frame[17]) >> 4 | (frame[18]) << 4) & 0x07FF)
        self.sbusChannels[13] = (((frame[18]) >> 7 | (frame[19]) << 1 | (
            frame[20]) << 9) & 0x07FF)
        self.sbusChannels[14] = (((frame[20]) >> 2 | (frame[21]) << 6) & 0x07FF)
        self.sbusChannels[15] = (((frame[21]) >> 5 | (frame[22]) << 3) & 0x07FF)

        # to be tested, No 17 & 18 channel on taranis X8R
        if (frame[23]) & 0x0001:
            self.sbusChannels[16] = 2047
        else:
            self.sbusChannels[16] = 0
        # to be tested, No 17 & 18 channel on taranis X8R
        if ((frame[23]) >> 1) & 0x0001:
            self.sbusChannels[17] = 2047
        else:
            self.sbusChannels[17] = 0

        # Failsafe
        self.failSafeStatus = self.SBUS_SIGNAL_OK
        if (frame[self.SBUS_FRAME_LEN - 2]) & (1 << 2):
            self.failSafeStatus = self.SBUS_SIGNAL_LOST
        if (frame[self.SBUS_FRAME_LEN - 2]) & (1 << 3):
            self.failSafeStatus = self.SBUS_SIGNAL_FAILSAFE

    def update(self):
        """
        we need a least 2 frame size to be sure to find one full frame
        so we take all the buffer (and empty it) and read it by the end to
        catch the last news
        First find ENDBYTE and looking FRAMELEN backward to see if it's STARTBYTE
        """

        while True:
            frame = self.ser.read(1)
            if frame == self.START_BYTE:
                frame += self.ser.read(self.SBUS_FRAME_LEN - 1)
                if len(frame) == self.SBUS_FRAME_LEN:
                    # print(frame.hex())
                    self.decode_frame(frame)
                break


if __name__ == '__main__':

    sbus = SBUSReceiver('/dev/ttyUSB0')

    while True:
        # Call sbus.get_new_data() every about 7 to 10 ms.
        # to be sure to not calling it to much verify your serial.inWaiting() size of your SBUSReceiver instance.
        # if between call your serial is growing to much (> 50) you can call it more often.
        # if it raise you < 50 multiples times in row, you calling it too soon.
        sbus.update()

        # anywhere in your code you can call sbus.get_rx_channels() to get all data or sbus.get_rx_channels()[n] to
        # get value of n channel or get_rx_channel(self, num_ch) to get channel you want.
        print(sbus.get_failsafe_status(), sbus.get_rx_channels(), str(sbus.ser.inWaiting()).zfill(4), (
                time.time() - sbus.lastFrameTime), sbus.frameCount)
