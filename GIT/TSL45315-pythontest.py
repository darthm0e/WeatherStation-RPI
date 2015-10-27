import smbus
from time import sleep

# select the correct i2c bus for this revision of Raspberry Pi
revision = ([l[12:-1] for l in open('/proc/cpuinfo','r').readlines() if l[:8]=="Revision"]+['0000'])[0]
bus = smbus.SMBus(1 if int(revision, 16) >= 4 else 0)

class TSL45315:
    VAL_COMMAND = 0x80
    REG_CONTROL = 0x00 | VAL_COMMAND
    REG_CONFIG  = 0x01 | VAL_COMMAND
    REG_DATA_LOW    = 0x04 | VAL_COMMAND

    VAL_PWON    = 0x03
    VAL_PWOFF   = 0x00
    VAL_INVALID = -1

    VAL_TIME_400_MS = 0x00
    VAL_TIME_200_MS = 0x01
    VAL_TIME_100_MS = 0x02


    MASK_TCNTRL     = 0x03

    address = None

    def __init__(self, address = 0x29):
        self.address = address
        self.disableMeasurement()
        self.setTime(400)
        self.enableMeasurement()

    def enableMeasurement(self):
        bus.write_byte_data(self.address, self.REG_CONTROL, self.VAL_PWON)

    def disableMeasurement(self):
        bus.write_byte_data(self.address, self.REG_CONTROL, self.VAL_PWOFF)

    def setTime(self, time):
        if not time in [100, 200, 400]:
            raise ValueError("Time %d out of range [%d,%d,%d]" % (time, 100, 200, 400))
        if time == 400:
            bits_time = self.VAL_TIME_400_MS
            self.time_multiplier = 1
        elif time == 200:
            bits_time = self.VAL_TIME_200_MS
            self.time_multiplier = 2
        elif time == 100:
            bits_time = self.VAL_TIME_100_MS
            self.time_multiplier = 4
        new_byte_time = bits_time & self.MASK_TCNTRL

        current_byte_config = bus.read_byte_data(self.address, self.REG_CONFIG)
        new_byte_config = (current_byte_config & ~self.MASK_TCNTRL) | new_byte_time
        bus.write_byte_data(self.address, self.REG_CONFIG, new_byte_config)

    def getTime(self):
        current_byte_config =  bus.read_byte_data(self.address, self.REG_CONFIG)
        bits_time = (current_byte_config & self.MASK_TCNTRL)
        if bits_time == self.VAL_TIME_400_MS:
            t = 400
        elif bits_time == self.VAL_TIME_200_MS:
            t = 200
        elif bits_time == self.VAL_TIME_100_MS:
            t = 100
        else:
            t = self.VAL_INVALID # indicates undefined
        return t

    def getLux(self):
        data_bytes = bus.read_i2c_block_data(self.address, self.REG_DATA_LOW, 2)
        return self.time_multiplier * (data_bytes[1] << 8 | data_bytes[0])


if __name__ == "__main__":
    # if run directly we'll just create an instance of the class and output
    # the current readings
    tsl45315 = TSL45315()

    lux = tsl45315.getLux()
    print "TSL45315 on address 0x%x:" % (tsl45315.address)
    print "   light = %dlux" % ( lux )
