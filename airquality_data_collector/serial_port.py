import serial
import time

# XXX: tidy up or refactor


class SerialPort(object):
    def __init__(self, comport):
        self.device = serial.Serial(
            port=comport,  # COM14
            baudrate=9600,  # 57600, 115200
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1,
            # bytesize=serial.EIGHTBITS
        )

    def open(self, query_idn=False):
        # device.open()
        self.device.isOpen()
        if query_idn:
            self.device.write('*IDN?\r\n')
            out = ''
            time.sleep(0.5)
            while self.device.inWaiting() > 0:
                out += self.device.read(1)
        return 0

    def close(self):
        self.device.close()

    def write(self, cmd):
        self.device.write('%s\r' % cmd)
        out = ''
        time.sleep(0.200)
        while self.device.inWaiting() > 0:
            out += self.device.read(1)
        return 0

    def query(self, cmd):
        self.device.write('%s\r' % cmd)
        out = ''
        time.sleep(0.200)
        while self.device.inWaiting() > 0:
            out += self.device.read(1)
        return out.strip()

    def read(self):
        while True:
            header = self.device.read(2)
            if header == b'\xAA\xC0':
                data = self.device.read(6)
                checksum = self.device.read(1)
                tail = self.device.read(1)
                if tail == b'\xAB':
                    return header + data + checksum + tail

        # return self.device.read(data)
