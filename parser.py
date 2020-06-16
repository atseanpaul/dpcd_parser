import collections

ParseResult = collections.namedtuple('ParseResult',
                                     [
                                       'register',
                                       'start_bit',
                                       'end_bit',
                                       'label',
                                       'value',
                                       'output'
                                     ])
class RangeParser(object):
  name = None
  start = None
  end = None

  def __init__(self, bytes, value_offset):
    self.value = bytes[value_offset:value_offset + self.num_bytes()]
    self.parse_result = {}

  @classmethod
  def can_parse(cls, start):
    # Only support parsing from the beginning of the range
    # TODO: maybe add partial parsing at some point
    if start == cls.start:
      return True
    return False

  def num_bytes(self):
    return type(self).end - type(self).start + 1

  def __field(self, value, start_bit, end_bit):
    start_mask = ((1 << (start_bit)) - 1)
    end_mask = ((1 << (end_bit + 1)) - 1)
    mask = start_mask ^ end_mask
    return (value & mask) >> start_bit

  def add_result(self, label, offset, start_bit, end_bit=None, printfn=lambda x: x):
    if end_bit == None:
      end_bit = start_bit
    if end_bit < start_bit:
      raise ValueError('Inverted start/end bits!')
    value = self.__field(self.value[offset], start_bit, end_bit)
    result = ParseResult(self.name, start_bit, end_bit, label, value, printfn(value))
    self.parse_result[start_bit] = result

  def print(self):
    if not self.parse_result:
      return
    print('{:<10}{:<41}[{}]'.format(hex(type(self).start),
                                   type(self).name,
                              ', '.join(hex(x) for x in self.value)))
    for v in self.parse_result.values():
      print('  [{:<3}{}:{}] {:40}{}'.format(
              v.value,
              v.start_bit,
              v.end_bit,
              v.label,
              v.output))

  def parse(self):
    raise NotImplementedError()

class RangeDPCDRev(RangeParser):
  name = "DPCD_REV"
  start = 0
  end = 0

  def parse(self):
    self.add_result('Major rev', 0, 4, 7)
    self.add_result('Minor rev', 0, 0, 3)

class RangeMaxLinkRate(RangeParser):
  name = 'MAX_LINK_RATE'
  start = 1
  end = 1

  def parse(self):
    self.add_result('Max link rate', 0, 0, 7,
                    lambda x: '{} Gpbs'.format(x * 0.27))

class RangeMaxLaneCount(RangeParser):
  name = 'MAX_LANE_COUNT'
  start = 2
  end = 2

  def parse(self):
    self.add_result('Enhanced frame caps', 0, 7)
    self.add_result('Supports TPS3 pattern', 0, 6)
    self.add_result('Supports post-lt adjust', 0, 5)
    self.add_result('Max lane count', 0, 0, 4)

class RangeMaxDownspread(RangeParser):
  name = 'MAX_DOWNSPREAD'
  start = 3
  end = 3

  def parse(self):
    self.add_result('Supports TPS4 pattern', 0, 7)
    self.add_result('Requires AUX for sync', 0, 6)
    self.add_result('Reserved', 0, 2, 5)
    self.add_result('Supports stream regen bit', 0, 1)
    self.add_result('Max downspread', 0, 0,
                    printfn=lambda x: '<=0.5%' if x else 'None')

class RangeRecvPorts(RangeParser):
  name = 'NORP/DP_PWR_VOLTAGE_CAP'
  start = 4
  end = 4

  def parse(self):
    self.add_result('Capable of 18V', 0, 7)
    self.add_result('Capable of 12V', 0, 6)
    self.add_result('Capable of 5V', 0, 5)
    self.add_result('Reserved', 0, 2, 4)
    self.add_result('CRC 3D supported', 0, 1)
    self.add_result('Number recv ports', 0, 0)

class RangeDownstreamPortPresent(RangeParser):
  name = 'DOWN_STREAM_PORT_PRESENT'
  start = 5
  end = 5

  def downstream_port_type(self, val):
    if val == 0:
      return 'DisplayPort'
    elif val == 1:
      return 'Analog VGA'
    elif val == 2:
      return 'HDMI/DVI/DP++'
    elif val == 3:
      return 'Others'

  def parse(self):
    self.add_result('Reserved', 0, 7)
    self.add_result('Detailed capability available', 0, 4)
    self.add_result('Branch converts format', 0, 3)
    self.add_result('Downstream facing port type', 0, 1, 2,
                    self.downstream_port_type)
    self.add_result('Downstream facing port present', 0, 0)

class RangeMainLinkChannelCoding(RangeParser):
  name = 'MAIN_LINK_CHANNEL_CODING'
  start = 6
  end = 6

  def parse(self):
    self.add_result('Reserved', 0, 2, 7)
    self.add_result('Supports 128b/132b encoding', 0, 1)
    self.add_result('Supports 8b/10b encoding', 0, 0)

class RangeDownStreamPortCount(RangeParser):
  name = 'DOWN_STREAM_PORT_COUNT'
  start = 7
  end = 7

  def parse(self):
    self.add_result('IEEE unique ID support', 0, 7)
    self.add_result('Sink requires MSA timing', 0, 6)
    self.add_result('Reserved', 0, 4, 5)
    self.add_result('Downstream port count', 0, 0, 3)

class RangeReceivePortCap(object):
  @staticmethod
  def parse(parser):
    parser.add_result('Reserved', 0, 6, 7)
    parser.add_result('Buffer size per-lane/port', 0, 5,
                      printfn=lambda x: 'Per port' if x else 'Per lane')
    parser.add_result('Buffer size units', 0, 4,
                      printfn=lambda x: 'Bytes' if x else 'Pixels')
    parser.add_result('HBlank expansion supported', 0, 3)
    parser.add_result('usage', 0, 2, printfn=lambda x: 'Secondary stream' if x else 'Primary stream')
    parser.add_result('Local EDID present', 0, 1)
    parser.add_result('Reserved', 0, 0)
    parser.add_result('Buffer Size', 1, 0, 7, lambda x: (x + 1) * 32)

class RangeReceivePortCap0(RangeParser):
  name = 'RECEIVE_PORT0_CAP'
  start = 8
  end = 9

  def parse(self):
    RangeReceivePortCap.parse(self)

class RangeReceivePortCap1(RangeParser):
  name = 'RECEIVE_PORT1_CAP'
  start = 0xA
  end = 0xB

  def parse(self):
    RangeReceivePortCap.parse(self)

class RangeI2CSpeedCap(RangeParser):
  name = 'I2C Speed Control Capabilities Bit Map'
  start = 0xC
  end = 0xC

  def i2c_speed_caps(self, val):
    if val == 0:
      return 'No physical i2c bus'
    speeds = []
    if val & 1:
      speeds.append('1 Kbps')
    if val & 2:
      speeds.append('5 Kbps')
    if val & 4:
      speeds.append('10 Kbps')
    if val & 8:
      speeds.append('100 Kbps')
    if val & 0x10:
      speeds.append('400 Kbps')
    if val & 0x20:
      speeds.append('1 Mbps')
    if val & 0x40 or val & 0x80:
      speeds.append('RESERVED')
    return '/'.join(speeds)

  def parse(self):
    self.add_result('I2C speed support', 0, 0, 7, self.i2c_speed_caps)

class RangeEDPConfigCap(RangeParser):
  name = 'eDP_CONFIGURATION_CAP'
  start = 0xD
  end = 0xD

  def parse(self):
    # TODO: Implement this from eDP spec
    self.add_result('Reserved for eDP', 0, 0, 7)

class RangeTrainingAuxInterval(RangeParser):
  name = 'TRAINING_AUX_RD_INTERVAL'
  start = 0xE
  end = 0xE

  def aux_rd_interval(self, val):
    fn = lambda x: 'ClockReqDone=100us / ChannelEqDone={}us'.format(x)
    if val == 0:
      return fn(400)
    elif val == 1:
      return fn(4000)
    elif val == 2:
      return fn(8000)
    elif val == 3:
      return fn(12000)
    elif val == 4:
      return fn(16000)

  def parse(self):
    self.add_result('Extended receiver caps available', 0, 7)
    self.add_result('Training AUX read interval', 0, 0, 6, self.aux_rd_interval)


class Parser(object):
  def __init__(self):
    self.registry = []
    for c in RangeParser.__subclasses__():
      self.registry.append(c)
    self.result = []
    self.unparsed = {}

  def parse(self, bytes, offset):
    i = 0
    while i < len(bytes):
      addr = i + offset
      parsed_bytes = 0
      for r in self.registry:
        if not r.can_parse(addr):
          continue

        parser = r(bytes, i)
        parser.parse()
        parsed_bytes = parser.num_bytes()
        self.result.append(parser)
        break

      if not parsed_bytes:
        self.unparsed[addr] = bytes[i]
        i += 1
      else:
        i += parsed_bytes

  def print(self):
    for r in self.result:
      r.print()
    for a,v in self.unparsed.items():
      print('{:<10}{:<41}[{}]'.format(hex(a),
                                     'UNKNOWN',
                                     hex(v)))
