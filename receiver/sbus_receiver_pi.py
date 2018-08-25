"""
derivated from # from Sokrates80/sbus_driver_micropython

"""


import array
import serial
import binascii
import codecs
import time

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
			timeout = 0,

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
		self.isReady = True
		self.lastFrameTime = 0
		self.sbusBuff = bytearray(1)  # single byte used for sync
		self.sbusFrame = bytearray(25)  # single SBUS Frame
		self.sbusChannels = array.array('H', [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])  # RC Channels
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


	def get_new_data(self):
		"""
		we need a least 2 frame size to be sure to find one full frame
		so we take all the fuffer (and empty it) and read it by the end to
		catch the last news
		First find ENDBYTE and looking FRAMELEN backward to see if it's STARTBYTE
		"""

		#does we have enougth data in the buffer and no thread is currently trying in background?
		if self.ser.inWaiting() >= self.SBUS_FRAME_LEN*2 and self.isReady:
			self.isReady = False	
			#so taking all of them
			tempFrame = self.ser.read(self.ser.inWaiting()) 
<<<<<<< HEAD
			print "---tmpFrame len", len(tempFrame), "/", self.SBUS_FRAME_LEN
			# for each char of the buffer frame we looking for the end byte
			for end in range(0, self.SBUS_FRAME_LEN):
				#looking for end byte, remember we working backwards
				print len(tempFrame)-1-end,
				if tempFrame[len(tempFrame)-1-end] == self.END_BYTE :
					#looking for start from last hit point minus FRAMELEN
					print len(tempFrame)-end-self.SBUS_FRAME_LEN
=======
			# for each char of the buffer frame we looking for the end byte
			for end in range(0, self.SBUS_FRAME_LEN):
				#looking for end byte, remember we working backwards
				if tempFrame[len(tempFrame)-1-end] == self.END_BYTE :
					#looking for start from last hit point minus FRAMELEN
>>>>>>> threading
					if tempFrame[len(tempFrame)-end-self.SBUS_FRAME_LEN] == self.START_BYTE :
						# if it is the right char, frame look good :')
						# remember data arrive in 8E2 packet so it was already parity verified

						# so the frame have to be remap only if it different (cpu time is precious)
						lastUpdate = tempFrame[len(tempFrame)-end-self.SBUS_FRAME_LEN:len(tempFrame)-1-end]
						if not self.sbusFrame == lastUpdate:
							self.sbusFrame = lastUpdate
							self.decode_frame()

						self.lastFrameTime = time.time() # keep trace of the last update
						self.isReady = True
						break



# excuted if this doc is not imported
# for testing purpose only
if __name__ == '__main__':

	

	sbus = SBUSReceiver('/dev/ttyS0')

	while True:
		time.sleep(0.08)
		sbus.get_new_data()
		#print sbus.get_failsafe_status(), sbus.get_rx_channels(), str(sbus.ser.inWaiting()).zfill(4) , (time.time()-sbus.lastFrameTime)

