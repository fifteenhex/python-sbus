"""
derivated from # from Sokrates80/sbus_driver_micropython

"""


import array
import serial
import time
import binascii
import codecs

class SBUSReceiver():
	def __init__(self, _uart_port):
		#self.sbus = serial.Serial(uart_port, 105000)
		#self.sbus.init(100000, bits=8, parity=0, stop=2, timeout_char=3, read_buf_len=250)

		self.ser = serial.Serial(
			port=_uart_port,#port='/dev/serial0',
			baudrate = 100000,
			parity=serial.PARITY_EVEN,
			stopbits=serial.STOPBITS_TWO,
			bytesize=serial.EIGHTBITS,
			timeout = 3,
		)

		# constants
		self.START_BYTE = b'\x0f' # 15 in ascii
		self.END_BYTE = b'\x00' # Nul in ascii
		self.SBUS_FRAME_LEN = 25
		self.SBUS_NUM_CHAN = 18
		self.OUT_OF_SYNC_THD = 10
		self.SBUS_NUM_CHANNELS = 18
		self.SBUS_SIGNAL_OK = 0
		self.SBUS_SIGNAL_LOST = 1
		self.SBUS_SIGNAL_FAILSAFE = 2

		# Stack Variables initialization
		self.lastFrameTime = 0
		self.validSbusFrame = 0
		self.lostSbusFrame = 0
		self.frameIndex = 0
		self.resyncEvent = 0
		self.outOfSyncCounter = 0
		self.sbusBuff = bytearray(1)  # single byte used for sync
		self.sbusFrame = bytearray(25)  # single SBUS Frame
		self.sbusChannels = array.array('H', [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])  # RC Channels
		self.isSync = False
		self.startByteFound = False
		self.failSafeStatus = self.SBUS_SIGNAL_FAILSAFE


	def toInt(self, _from):
		return int(codecs.encode(_from, 'hex'), 16)


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

	def get_rx_report(self):
		"""
		Used to retrieve some stats about the frames decoding
		:return:  a dictionary containg three information ('Valid Frames','Lost Frames', 'Resync Events')
		"""

		rep = {}
		rep['Valid Frames'] = self.validSbusFrame
		rep['Lost Frames'] = self.lostSbusFrame
		rep['Resync Events'] = self.resyncEvent

		return rep

	def decode_frame(self):

		# TODO: DoubleCheck if it has to be removed
		for i in range(0, self.SBUS_NUM_CHANNELS - 2):
			self.sbusChannels[i] = 0

		# counters initialization
		byte_in_sbus = 1
		bit_in_sbus = 0
		ch = 0
		bit_in_channel = 0

		for i in range(0, 175):  # TODO Generalization

			if self.toInt(self.sbusFrame[byte_in_sbus]) & (1 << bit_in_sbus): 
				self.sbusChannels[ch] |= (1 << bit_in_channel)

			bit_in_sbus += 1
			bit_in_channel += 1

			if bit_in_sbus == 8:
				bit_in_sbus = 0
				byte_in_sbus += 1

			if bit_in_channel == 11:
				bit_in_channel = 0
				ch += 1


		# Decode Digitals Channels

		# Digital Channel 1
		if self.toInt(self.sbusFrame[self.SBUS_FRAME_LEN - 2]) & (1 << 0):
			self.sbusChannels[self.SBUS_NUM_CHAN - 2] = 1
		else:
			self.sbusChannels[self.SBUS_NUM_CHAN - 2] = 0

		# Digital Channel 2
		if self.toInt(self.sbusFrame[self.SBUS_FRAME_LEN - 2] ) & (1 << 1):
			self.sbusChannels[self.SBUS_NUM_CHAN - 1] = 1
		else:
			self.sbusChannels[self.SBUS_NUM_CHAN - 1] = 0

		# Failsafe
		self.failSafeStatus = self.SBUS_SIGNAL_OK
		if self.toInt(self.sbusFrame[self.SBUS_FRAME_LEN - 2]) & (1 << 2):
			self.failSafeStatus = self.SBUS_SIGNAL_LOST
		if self.toInt(self.sbusFrame[self.SBUS_FRAME_LEN - 2]) & (1 << 3):
			self.failSafeStatus = self.SBUS_SIGNAL_FAILSAFE


	def get_sync(self):

		if self.ser.inWaiting() > 0:
			if self.startByteFound:
				if self.frameIndex == (self.SBUS_FRAME_LEN - 1):
					self.sbusBuff = self.ser.read()  # end of frame byte
					if self.sbusBuff[0] == self.END_BYTE:  
						self.startByteFound = False
						self.isSync = True
						self.frameIndex = 0
				else:

					self.sbusBuff = self.ser.read()  # keep reading 1 byte until the end of frame
					self.frameIndex += 1
			else:
				self.frameIndex = 0
				self.sbusBuff = self.ser.read()  # read 1 byte
				if self.sbusBuff[0] == self.START_BYTE:  # looking for start byte
					self.startByteFound = True
					self.frameIndex += 1

	def get_new_data(self):
		"""
		This function must be called periodically according to the specific SBUS implementation in order to update
		the channels values.
		For FrSky the period is 300us.
		"""

		if self.isSync:
			if self.ser.inWaiting() >= self.SBUS_FRAME_LEN:
				self.sbusFrame = self.ser.read(self.SBUS_FRAME_LEN)  # read the whole frame
				if (self.sbusFrame[0] == self.START_BYTE and self.sbusFrame[self.SBUS_FRAME_LEN - 1] == self.END_BYTE):  # TODO: Change to use constant var value
					self.validSbusFrame += 1
					self.outOfSyncCounter = 0
					self.decode_frame()

					self.lastFrameTime = time.time() # keep trace of the last update
					self.ser.reset_input_buffer() #have to flush buffer cause X8R @ 1M baud will overflow it too quick
					self.ser.isSync = False #and have to resync
				else:
					self.lostSbusFrame += 1
					self.outOfSyncCounter += 1

				if self.outOfSyncCounter > self.OUT_OF_SYNC_THD:
					self.isSync = False
					self.resyncEvent += 1
			
		else:
			self.get_sync()





# excuted if this doc is not imported
# for testing purpose only
if __name__ == '__main__':

	sbus = SBUSReceiver('/dev/ttyS0')

	timer1 = 0

	while True:
		sbus.get_new_data()
		if time.time() - timer1 > 0.005:
			a = sbus.get_rx_channels()
			if a[0] >= 512 :
				print sbus.get_rx_channels(), sbus.ser.inWaiting(), (time.time()-sbus.lastFrameTime)
			timer1 = time.time()