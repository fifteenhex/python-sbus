#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Based on:
	Sokrates80/sbus_driver_micropython git hub
	https://os.mbed.com/users/Digixx/code/SBUS-Library_16channel/file/83e415034198/FutabaSBUS/FutabaSBUS.cpp/
	https://os.mbed.com/users/Digixx/notebook/futaba-s-bus-controlled-by-mbed/
	https://www.ordinoscope.net/index.php/Electronique/Protocoles/SBUS
"""

import asyncio
import array
import serial
import serial_asyncio
import time


class SBUSReceiver:
    class SBUSFramer(asyncio.Protocol):

        START_BYTE = 0x0f
        END_BYTE = 0x00
        SBUS_FRAME_LEN = 25

        def __init__(self):
            super().__init__()
            self._in_frame = False
            self._frame = bytearray()
            self.transport = None
            self.frames = asyncio.Queue()

        def connection_made(self, transport):
            self.transport = transport
            print('port opened', transport)

        def data_received(self, data):
            for b in data:
                if self._in_frame:
                    self._frame.append(b)
                    if len(self._frame) == SBUSReceiver.SBUSFramer.SBUS_FRAME_LEN:
                        print(self._frame.hex())
                        decoded_frame = SBUSReceiver.SBUSFrame(self._frame)
                        self.frames.put(decoded_frame)
                        self._in_frame = False
                else:
                    if b == SBUSReceiver.SBUSFramer.START_BYTE:
                        self._in_frame = True
                        self._frame.clear()
                        self._frame.append(b)

        def connection_lost(self, exc):
            print('port closed')
            asyncio.get_event_loop().stop()

    class SBUSFrame:
        OUT_OF_SYNC_THD = 10
        SBUS_NUM_CHANNELS = 18
        SBUS_SIGNAL_OK = 0
        SBUS_SIGNAL_LOST = 1
        SBUS_SIGNAL_FAILSAFE = 2

        def __init__(self, frame):
            self.sbusChannels = [None] * SBUSReceiver.SBUSFrame.SBUS_NUM_CHANNELS

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
            self.failSafeStatus = SBUSReceiver.SBUSFrame.SBUS_SIGNAL_OK
            if (frame[SBUSReceiver.SBUSFramer.SBUS_FRAME_LEN - 2]) & (1 << 2):
                self.failSafeStatus = SBUSReceiver.SBUSFrame.SBUS_SIGNAL_LOST
            if (frame[SBUSReceiver.SBUSFramer.SBUS_FRAME_LEN - 2]) & (1 << 3):
                self.failSafeStatus = SBUSReceiver.SBUSFrame.SBUS_SIGNAL_FAILSAFE

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

    def __init__(self, _uart_port='/dev/ttyUSB0'):
        serial_coro = serial_asyncio.create_serial_connection(asyncio.get_running_loop(),
                                                              SBUSReceiver.SBUSFramer,
                                                              _uart_port,
                                                              baudrate=100000,
                                                              parity=serial.PARITY_EVEN,
                                                              stopbits=serial.STOPBITS_TWO,
                                                              bytesize=serial.EIGHTBITS)
        # self._framer = protocol
        self.serial_task = asyncio.create_task(serial_coro)

    async def get_frame(self):
        # return self._framer.frames.get()
        pass


async def main():
    sbus = SBUSReceiver('/dev/ttyUSB0')
    frame = await sbus.get_frame()
    # sbus.update()

    # anywhere in your code you can call sbus.get_rx_channels() to get all data or sbus.get_rx_channels()[n] to
    # get value of n channel or get_rx_channel(self, num_ch) to get channel you want.
    # print(sbus.get_failsafe_status(), sbus.get_rx_channels(), str(sbus.ser.inWaiting()).zfill(4), (
    #        time.time() - sbus.lastFrameTime), sbus.frameCount)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.run_forever()
    loop.close()
