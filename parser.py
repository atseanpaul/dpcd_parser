import collections

class ParserBase(object):
  pass

class MultiByteParser(ParserBase):
  Result = collections.namedtuple('Result',
                                  [
                                    'register',
                                    'value',
                                    'output'
                                  ])
  name = None
  start = None
  end = None

  def __init__(self, bytes, value_offset):
    self.value = bytes[value_offset:value_offset + self.num_bytes()]
    self.output = None

  @classmethod
  def need_followon(cls, start, bytes):
    return False

  @classmethod
  def can_parse(cls, start, bytes):
    # TODO: add partial parsing support
    if start >= cls.start and start <= cls.end:
      return True
    return False

  def num_bytes(self):
    return type(self).end - type(self).start + 1

  def add_result(self, printfn=lambda x: x):
    self.output = printfn(self.value)

    value = 0
    for i,v in enumerate(self.value):
      value += v << (i * 8)
    return value

  def print(self):
    print('  {:<10}{:<41}[{}]'.format(hex(type(self).start),
                                   type(self).name,
                              ', '.join(hex(x) for x in self.value)))
    print('  {:<11}{:<40}{}'.format('', 'Value', self.output))

  def parse(self):
    raise NotImplementedError()


class RangeParser(ParserBase):
  Result = collections.namedtuple('Result',
                                  [
                                    'register',
                                    'start_bit',
                                    'end_bit',
                                    'label',
                                    'value',
                                    'output'
                                    ])

  name = None
  start = None
  end = None

  def __init__(self, bytes, value_offset):
    self.value = bytes[value_offset:value_offset + self.num_bytes()]
    self.parse_result = []

  @classmethod
  def need_followon(cls, start, bytes):
    return False

  @classmethod
  def can_parse(cls, start, bytes):
    # Only support parsing from the beginning of the range
    # TODO: maybe add partial parsing at some point
    if start == cls.start:
      return True
    return False

  def num_bytes(self):
    return type(self).end - type(self).start + 1

  def field(self, value, start_bit, end_bit):
    start_mask = ((1 << (start_bit)) - 1)
    end_mask = ((1 << (end_bit + 1)) - 1)
    mask = start_mask ^ end_mask
    return (value & mask) >> start_bit

  def add_result(self, label, offset, start_bit, end_bit=None, printfn=lambda x: x):
    if end_bit == None:
      end_bit = start_bit
    if end_bit < start_bit:
      raise ValueError('Inverted start/end bits!')
    if offset >= len(self.value):
      raise ValueError(f'Invalid offset {offset} len={len(self.value)}!')
    value = self.field(self.value[offset], start_bit, end_bit)
    result = RangeParser.Result(self.name, start_bit, end_bit, label, value, printfn(value))
    self.parse_result.append(result)

    return value

  def add_multi_result(self, label, offset, start_bit, end_bit, printfn=lambda x: x):
    if start_bit == end_bit:
      raise ValueError(f'Invalid range {start_bit}->{end_bit}!')
    elif abs(start_bit - end_bit) > (len(self.value) * 8):
      raise ValueError(f'Invalid range {start_bit} - {end_bit} > len={len(self.value)}!')

    if start_bit < end_bit:
      offset_end = offset + int(end_bit / 8)
      s_value = self.value[offset:(offset_end + 1)]
      s_start_bit = start_bit
      s_end_bit = end_bit
    else:
      offset_end = offset + int(start_bit / 8)
      s_value = self.value[offset:(offset_end + 1)]
      s_value.reverse()
      s_start_bit = end_bit
      s_end_bit = start_bit

    total = 0
    for i,v in enumerate(s_value):
      total += v << (i * 8)

    value = self.field(total, s_start_bit, s_end_bit)

    result = RangeParser.Result(self.name, start_bit, end_bit, label, value, printfn(value))
    self.parse_result.append(result)

    return value

  def print(self):
    print('  {:<10}{:<41}[{}]'.format(hex(type(self).start),
                                   type(self).name,
                              ', '.join(hex(x) for x in self.value)))
    for v in self.parse_result:
      print('    [{:<8} {}:{}] {:40}{}'.format(
              hex(v.value),
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

class RangeReceivePortCap(RangeParser):
  def parse(self):
    self.add_result('Reserved', 0, 6, 7)
    self.add_result('Buffer size per-lane/port', 0, 5,
                      printfn=lambda x: 'Per port' if x else 'Per lane')
    self.add_result('Buffer size units', 0, 4,
                      printfn=lambda x: 'Bytes' if x else 'Pixels')
    self.add_result('HBlank expansion supported', 0, 3)
    self.add_result('usage', 0, 2, printfn=lambda x: 'Secondary stream' if x else 'Primary stream')
    self.add_result('Local EDID present', 0, 1)
    self.add_result('Reserved', 0, 0)
    self.add_result('Buffer Size', 1, 0, 7, lambda x: (x + 1) * 32)

class RangeReceivePortCap0(RangeReceivePortCap):
  name = 'RECEIVE_PORT0_CAP'
  start = 8
  end = 9

class RangeReceivePortCap1(RangeReceivePortCap):
  name = 'RECEIVE_PORT1_CAP'
  start = 0xA
  end = 0xB

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

class RangeMSTMCaps(RangeParser):
  name = 'MSTM_CAP'
  start = 0x21
  end = 0x21

  def parse(self):
    self.add_result('Reserved', 0, 2, 7)
    self.add_result('SINGLE_STREAM_SIDEBAND_MSG_SUPPORT', 0, 1)
    self.add_result('MST_CAP', 0, 0)

class RangeDetailedCapInfo(RangeParser):
  def dfpx_attribute(self, val):
    ret = []
    if val & 1:
      ret.append('480i@60')
    if val & 2:
      ret.append('480i@50')
    if val & 3:
      ret.append('1080i@60')
    if val & 4:
      ret.append('1080i@50')
    if val & 5:
      ret.append('720p@60')
    if val & 6:
      ret.append('720p@50')
    return ','.join(ret)

  def dfpx_type(self, val):
    if val == 0:
      return 'DisplayPort'
    elif val == 1:
      return 'Analog VGA'
    elif val == 2:
      return 'DVI'
    elif val == 3:
      return 'HDMI'
    elif val == 4:
      return 'Other (No DisplayID/EDID support)'
    elif val == 5:
      return 'DP++'
    elif val == 6:
      return 'Wireless'
    elif val == 7:
      return 'Reserved'

  def max_bits_per_component(self, val):
    ret = ['8bpc']
    if val & 1:
      ret.append('10bpc')
    if val & 2:
      ret.append('12bpc')
    if val & 3:
      ret.append('16bpc')
    return '/'.join(ret)

  def parse(self):
    self.add_result('NON_EDID_DFPX_ATTRIBUTE', 0, 4, 7, self.dfpx_attribute)
    self.add_result('DFPX_HPD', 0, 3, 3, lambda x: 'HPD Aware' if x else 'HPD Unaware')
    self.add_result('DFPX_TYPE', 0, 0, 2, self.dfpx_type)
    # Detailed cap info for downstream ports isn't always available
    if len(self.value) <= 1:
      return

    # DP
    type = self.field(self.value[0], 0, 2)
    if type == 0:
      self.add_result('Reserved', 1, 0, 7)
      self.add_result('Reserved', 2, 0, 7)
      self.add_result('Reserved', 3, 0, 7)
    # VGA
    elif type == 1:
      self.add_result('Maximum Pixel Rate', 1, 0, 7, lambda x: '{} MP/s'.format(x * 8))
      self.add_result('Reserved', 2, 2, 7)
      self.add_result('Maximum Bits/component', 2, 0, 1, self.max_bits_per_component)
      self.add_result('Reserved', 3, 0, 7)
    # DVI
    elif type == 2:
      self.add_result('Maximum TMDS Char Clock Rate', 1, 0, 7, lambda x: '{} MHz'.format(x * 2.5))
      self.add_result('Reserved', 2, 2, 7)
      self.add_result('Maximum Bits/component', 2, 0, 1, self.max_bits_per_component)
      self.add_result('Reserved', 3, 3, 7)
      self.add_result('High Color Depth', 3, 2)
      self.add_result('Dual Link', 3, 1)
      self.add_result('Reserved', 3, 0)
    # HDMI
    elif type == 3:
      self.add_result('Maximum TMDS Char Clock Rate', 1, 0, 7, lambda x: '{} MHz'.format(x * 2.5))
      self.add_result('Reserved', 2, 2, 7)
      self.add_result('Maximum Bits/component', 2, 0, 1, self.max_bits_per_component)
      self.add_result('Reserved', 3, 5, 7)
      self.add_result('CONVERSION_FROM_YCBCR444_TO_YCBCR420_SUPPORT', 3, 4)
      self.add_result('CONVERSION_FROM_YCBCR444_TO_YCBCR422_SUPPORT', 3, 3)
      self.add_result('YCBCR420_PASS_THROUGH_SUPPORT', 3, 2)
      self.add_result('YCBCR422_PASS_THROUGH_SUPPORT', 3, 1)
      self.add_result('FRAME_SEQ_TO_FRAME_PACK', 3, 0)
    # Other
    elif type == 4:
      self.add_result('UNDEFINED', 1, 0, 7)
      self.add_result('UNDEFINED', 2, 0, 7)
      self.add_result('UNDEFINED', 3, 0, 7)
    # DP++
    elif type == 5:
      self.add_result('Maximum TMDS Char Clock Rate', 1, 0, 7, lambda x: '{} MHz'.format(x * 2.5))
      self.add_result('Reserved', 2, 2, 7)
      self.add_result('Maximum Bits/component', 2, 0, 1, self.max_bits_per_component)
      self.add_result('Reserved', 3, 2, 7)
      self.add_result('UNDEFINED', 3, 1, 7)
      self.add_result('FRAME_SEQ_TO_FRAME_PACK', 3, 0)
    # Wireless
    elif type == 6:
      self.add_result('Reserved', 1, 4, 7)
      self.add_result('WIRELESS_TECHNOLOGY', 1, 0, 3, lambda x: 'WiGig' if x == 0 else 'Reserved')
      self.add_result('Reserved', 2, 4, 7)
      self.add_result('WDE_TX_CONCURRENCY_CAP', 2, 2, 3)
      self.add_result('NUMBER_OF_WDE_TX_ON_DEVICE', 2, 0, 1)
      self.add_result('Reserved', 3, 0, 7)

class RangeDetailedCapInfoDFP0(RangeDetailedCapInfo):
  name = 'Downstream Facing Port 0 Capabilities'
  start = 0x80
  end = 0x83

class RangeDetailedCapInfoDFP1(RangeDetailedCapInfo):
  name = 'Downstream Facing Port 1 Capabilities'
  start = 0x84
  end = 0x87

class RangeDetailedCapInfoDFP2(RangeDetailedCapInfo):
  name = 'Downstream Facing Port 2 Capabilities'
  start = 0x88
  end = 0x8B

class RangeDetailedCapInfoDFP3(RangeDetailedCapInfo):
  name = 'Downstream Facing Port 3 Capabilities'
  start = 0x8C
  end = 0x8F

class RangePanelReplayCap(RangeParser):
  name = 'PANEL_REPLAY_CAPABILITY_SUPPORTED'
  start = 0xB0
  end = 0xB1

  def parse(self):
    self.add_result('Reserved', 0, 2, 7)
    self.add_result('Selective Update Support', 0, 1)
    self.add_result('Replay Support', 0, 0)
    self.add_result('Reserved', 1, 6, 7)
    self.add_result('Selective Update Granularity', 1, 5,
                    lambda x: 'Required' if x else 'Not Required')
    self.add_result('Reserved', 1, 0, 4)

class RangeSinkCountParser(RangeParser):
  def parse(self):
    self.add_result('SINK_COUNT_bit7', 0, 7)
    self.add_result('CP_READY', 0, 6)
    self.add_result('SINK_COUNT', 0, 0, 5)

class RangeSinkCount(RangeSinkCountParser):
  name = 'SINK_COUNT'
  start = 0x200
  end = 0x200

class RangeDeviceServiceIRQParser(RangeParser):
  def parse(self):
    self.add_result('Reserved', 0, 7)
    self.add_result('SINK_SPECIFIC_IRQ', 0, 6)
    self.add_result('UP_REQ_MSG_RDY', 0, 5)
    self.add_result('DOWN_REP_MSG_RDY', 0, 4)
    self.add_result('MCCS_IRQ', 0, 3)
    self.add_result('CP_IRQ', 0, 2)
    self.add_result('AUTOMATED_TEST_REQUEST', 0, 1)
    self.add_result('REMOTE_CONTROL_COMMAND_PENDING', 0, 0)

class RangeDeviceServiceIRQ(RangeDeviceServiceIRQParser):
  name = 'DEVICE_SERVICE_IRQ_VECTOR'
  start = 0x201
  end = 0x201

class RangeLaneStatus(RangeParser):
  def __init__(self, bytes, value_offset, lane_offset):
    super().__init__(bytes, value_offset)
    self.pfx = ('LANE{}'.format(lane_offset), 'LANE{}'.format(lane_offset))

  def parse(self):
    self.add_result('Reserved', 0, 7)
    self.add_result('{}_SYMBOL_LOCKED'.format(self.pfx[1]), 0, 6)
    self.add_result('{}_CHANNEL_EQ'.format(self.pfx[1]), 0, 5)
    self.add_result('{}_CR_DONE'.format(self.pfx[1]), 0, 4)
    self.add_result('Reserved', 0, 3)
    self.add_result('{}_SYMBOL_LOCKED'.format(self.pfx[0]), 0, 2)
    self.add_result('{}_CHANNEL_EQ'.format(self.pfx[0]), 0, 1)
    self.add_result('{}_CR_DONE'.format(self.pfx[0]), 0, 0)

class RangeLane01Status(RangeLaneStatus):
  name = 'LANE0_1_STATUS'
  start = 0x202
  end = 0x202

  def __init__(self, bytes, value_offset):
    super().__init__(bytes, value_offset, 0)

class RangeLane23Status(RangeLaneStatus):
  name = 'LANE2_3_STATUS'
  start = 0x203
  end = 0x203

  def __init__(self, bytes, value_offset):
    super().__init__(bytes, value_offset, 2)

class RangeLaneAlignStatusUpdatedParser(RangeParser):
  def parse(self):
    self.add_result('LINK_STATUS_UPDATED', 0, 7)
    self.add_result('DOWNSTREAM_PORT_STATUS_CHANGED', 0, 6)
    self.add_result('Reserved', 0, 2, 5)
    self.add_result('POST_LT_ADJ_REQ_IN_PROGRESS', 0, 1)
    self.add_result('INTERLANE_ALIGN_DONE', 0, 0)

class RangeLaneAlignStatusUpdated(RangeLaneAlignStatusUpdatedParser):
  name = 'LANE_ALIGN_STATUS_UPDATED'
  start = 0x204
  end = 0x204

class RangeSinkStatusParser(RangeParser):
  def parse(self):
    self.add_result('Reserved', 0, 3, 7)
    self.add_result('STREAM_REGENERATION_STATUS', 0, 2)
    self.add_result('RECEIVE_PORT_1_STATUS', 0, 1, printfn=lambda x: '{} sync'.format('IN' if x else 'OUT'))
    self.add_result('RECEIVE_PORT_0_STATUS', 0, 0, printfn=lambda x: '{} sync'.format('IN' if x else 'OUT'))

class RangeSinkStatus(RangeSinkStatusParser):
  name = 'SINK_STATUS'
  start = 0x205
  end = 0x205

class MultiByteIEEEOUI(MultiByteParser):
  def parse(self):
    self.add_result(lambda x: '{}-{}-{}'.format(
                    hex(x[0])[2:],
                    hex(x[1])[2:],
                    hex(x[2])[2:]))

class MultiByteSinkIEEEOUI(MultiByteIEEEOUI):
  name = 'Sink IEEE_OUI'
  start = 0x400
  end = 0x402

class MultiByteDeviceId(MultiByteParser):
  def parse(self):
    self.add_result(lambda x: '"{}"'.format(bytes(x).decode('utf-8')))

class MultiByteSinkDeviceId(MultiByteDeviceId):
  name = 'Sink Device Identification String'
  start = 0x403
  end = 0x408

class RangeHardwareRevision(RangeParser):
  def parse(self):
    self.add_result('Minor Revision', 0, 0, 3)
    self.add_result('Major Revision', 0, 4, 7)

class RangeSinkHardwareRevision(RangeHardwareRevision):
  name = 'Sink Hardware Revision'
  start = 0x409
  end = 0x409

class RangeFirmwareMajorRevision(RangeParser):
  def parse(self):
    self.add_result('Revision', 0, 0, 7)

class RangeSinkFirmwareMajorRevision(RangeFirmwareMajorRevision):
  name = 'Sink Firmware Major Revision'
  start = 0x40A
  end = 0x40A

class RangeFirmwareMinorRevision(RangeParser):
  def parse(self):
    self.add_result('Revision', 0, 0, 7)

class RangeSinkFirmwareMinorRevision(RangeFirmwareMinorRevision):
  name = 'Sink Firmware Minor Revision'
  start = 0x40B
  end = 0x40B

class MultiByteReserved40C(MultiByteParser):
  name = 'RESERVED'
  start = 0x40C
  end = 0x4FF

  def parse(self):
    self.add_result()

class MultiByteBranchIEEEOUI(MultiByteIEEEOUI):
  name = 'Branch IEEE_OUI'
  start = 0x500
  end = 0x502

class MultiByteBranchDeviceId(MultiByteDeviceId):
  name = 'Branch Device Identification String'
  start = 0x503
  end = 0x508

class RangeBranchHardwareRevision(RangeHardwareRevision):
  name = 'Branch Hardware Revision'
  start = 0x509
  end = 0x509

class RangeBranchFirmwareMajorRevision(RangeFirmwareMajorRevision):
  name = 'Branch Firmware Major Revision'
  start = 0x50A
  end = 0x50A

class RangeBranchFirmwareMinorRevision(RangeFirmwareMinorRevision):
  name = 'Branch Firmware Minor Revision'
  start = 0x50B
  end = 0x50B

class MultiByteDownRequest(MultiByteParser):
  name = 'DOWN_REQ'
  start = 0x1000
  end = 0x11FF

  def parse(self):
    self.add_result()

class MultiByteUpReply(MultiByteParser):
  name = 'UP_REP'
  start = 0x1200
  end = 0x13FF

  def parse(self):
    self.add_result()

class RangeDownReplyParser(RangeParser):
  name = 'DOWN_REP'
  start = 0x1400
  end = 0x15FF

  @classmethod
  def can_parse(cls, start, bytes):
    if start < cls.start or start > cls.end or (start % 16) != 0:
      return False

    print(f'start={hex(start)} bytes={bytes}')
    lct = (bytes[0] >> 4) & 0x0F;
    print(f'lct={lct} idx={1 + int(lct / 2) + 2} len={len(bytes)}')
    request_id = bytes[1 + int(lct / 2) + 2]
    print(f'request_id={hex(request_id)}')
    return request_id == cls.request_id

  def parse_sideband_header(self):
    num_links = self.add_result('Link Count Total', 0, 4, 7)
    self.add_result('Link Count Remaining', 0, 0, 3)
    for i in range(0, num_links - 1):
      start_bit = 0 if (i % 2) == 0 else 4
      self.add_result(f'link[{i}]: Relative Address', 1 + i, start_bit, start_bit + 3)
    cur = 1 + int(num_links / 2)
    if num_links > 1 and (num_links % 2) != 0:
      self.add_result(f'zeros', cur, 4, 7)
      cur += 1
    self.add_result('Broadcast Message', cur, 7, 7)
    self.add_result('Path Message', cur, 6, 6)
    self.add_result('Body Length', cur, 0, 5)
    cur += 1
    self.add_result('Start of Message Transmission', cur, 7, 7)
    self.add_result('End of Message Transmission', cur, 6, 6)
    self.add_result('Zero', cur, 5, 5)
    self.add_result('Message Sequence Number', cur, 4, 4)
    self.add_result('Header CRC', cur, 0, 3)
    return cur + 1

class RangeDownRepMessageTransactionVersion(RangeDownReplyParser):
  request_id = 0x00

  def parse(self):
    cur = self.parse_sideband_header()
    self.add_result('Request ID', cur, 0, 7, printfn=lambda x: 'GET_MESSAGE_TRANSACTION_VERSION')
    self.add_result('Transaction Version Number', cur + 1, 0, 7)

class RangeDownRepLinkAddress(RangeDownReplyParser):
  request_id = 0x01

  @classmethod
  def need_followon(cls, start, bytes):
    ret = start == cls.start #TODO: Need to count number of device type 5's
    print(f'{"NEED" if ret else "no need"} followon: {hex(start)} {hex(cls.start)} {bytes}')
    return ret

  def parse(self):
    cur = self.parse_sideband_header()
    self.add_result('Request ID', cur, 0, 7, printfn=lambda x: 'LINK_ADDRESS')
    self.add_multi_result('Global Unique Id', cur + 1, 0, 127)
    self.print()
    print(' '.join('{:02x}'.format(x) for x in self.value))
    ports = self.add_result('Ports', cur + 17, 0, 3)
    print(f'PORTS={hex(ports)} cur={cur + 17} val={hex(self.value[cur + 17])}/{self.value[cur + 17]}')

    cur += 18
    print(f'PORTS={hex(ports)} cur={cur} val={hex(self.value[cur])}/{self.value[cur]}')
    for i in range(0, ports):
      is_input = self.add_result(f'p[{i}]: Is Input', cur, 0, 0, printfn=lambda x: 'Yes' if x else 'No')
      dev_type = self.add_result(f'p[{i}]: Peer Device Type', cur, 1, 3)
      self.add_result(f'p[{i}]: Port Number', cur, 4, 7)

      self.add_result(f'p[{i}]: Messaging Capability Status', cur + 1, 0, 0)
      self.add_result(f'p[{i}]: DP Device Plug Status', cur + 1, 1, 1)
      
      if dev_type == 5:
        print(f'DEV_TYPE={dev_type}')
        self.add_multi_result(f'p[{i}]: Current Capabilities', cur + 1, 2, 130)
        cur += 16

      if not is_input:
        self.add_result(f'p[{i}]: Legacy Plug Status', cur + 1, 2, 2)
        self.add_result(f'p[{i}]: Zeros', cur + 1, 3, 7)
        self.add_result(f'p[{i}]: DPCD Revision', cur + 2, 0, 7)
        self.add_multi_result('p[{i}]: Global Unique Id', cur + 3, 0, 127)
        self.add_multi_result('p[{i}]: Num SDP Streams', cur + 19, 0, 3)
        self.add_multi_result('p[{i}]: Num SDP Stream Sinks', cur + 19, 4, 7)
        cur += 20
      else:
        self.add_multi_result('p[{i}]: Zeros', cur + 1, 2, 7)
        cur += 1

class RangeDownRepEnumPathResources(RangeDownReplyParser):
  request_id = 0x00

  def parse(self):
    self.add_result('Request ID', 0, 0, 7, printfn=lambda x: 'GET_MESSAGE_TRANSACTION_VERSION')
    self.add_result('Message Txn Version Number', 1, 0, 7)

class RangeDownRepEnumPathResources(RangeDownReplyParser):
  request_id = 0x10

  def parse(self):
    self.add_result('Request ID', 0, 0, 7, printfn=lambda x: 'ENUM_PATH_RESOURCES')
    self.add_result('Port', 1, 0, 3)
    self.add_multi_result('BW Number Available[multi]', 2, 15, 0)
    self.add_multi_result('Payload BW Number[multi]', 4, 15, 0)

class RangeDownRepAllocatePayload(RangeDownReplyParser):
  request_id = 0x11

  def parse(self):
    self.add_result('Request ID', 0, 0, 7, printfn=lambda x: 'ALLOCATE_PAYLOAD')
    self.add_result('Port Number', 1, 0, 3)
    self.add_result('Zeros', 1, 4, 7)
    self.add_result('Virtual Channel PBN', 2, 0, 7)
    self.add_result('Allocated PBN', 3, 0, 15)

class RangeDownRepQueryPayload(RangeDownReplyParser):
  request_id = 0x12

  def parse(self):
    self.add_result('Request ID', 0, 0, 7, printfn=lambda x: 'QUERY_PAYLOAD')
    self.add_result('Port Number', 1, 0, 3)
    self.add_result('Zeros', 1, 4, 7)
    self.add_multi_result('Allocated PBN', 2, 0, 16)

class RangeDownRepRemoteDPCDRead(RangeDownReplyParser):
  request_id = 0x20

  def parse(self):
    self.add_result('Request ID', 0, 0, 7, printfn=lambda x: 'REMOTE_DPCD_READ')
    self.add_result('Zeros', 1, 0, 3)
    self.add_result('Port Number', 1, 4, 7)
    num_bytes = self.add_result('Number of Bytes', 2, 0, 7)
    for i in range(0, min(num_bytes, len(self.value) - 3)):
      self.add_result(f'data[{i}]', 3 + i, 0, 7)

'''
class MultiByteDownReply(RangeParser):
  name = 'DOWN_REP'
  start = 0x1400
  end = 0x15FF

  @staticmethod
  def printfn_reqid(value):
    if value == 0x00:
      return 'GET_MESSAGE_TRANSACTION_VERSION'
    elif value == 0x01:
      return 'LINK_ADDRESS'
    elif value == 0x02:
      return 'CONNECTION_STATUS_NOTIFY'
    elif value == 0x10:
      return 'ENUM_PATH_RESOURCES'
    elif value == 0x11:
      return 'ALLOCATE_PAYLOAD'
    elif value == 0x12:
      return 'QUERY_PAYLOAD'
    elif value == 0x13:
      return 'RESOURCE_STATUS_NOTIFY'
    elif value == 0x14:
      return 'CLEAR_PAYLOAD_ID_TABLE'
    elif value == 0x20:
      return 'REMOTE_DPCD_READ'
    elif value == 0x21:
      return 'REMOTE_DPCD_WRITE'
    elif value == 0x22:
      return 'REMOTE_I2C_READ'
    elif value == 0x23:
      return 'REMOTE_I2C_WRITE'
    elif value == 0x24:
      return 'POWER_UP_PHY'
    elif value == 0x25:
      return 'POWER_DOWN_PHY'
    elif value == 0x30:
      return 'SINK_EVENT_NOTIFY'
    elif value == 0x38:
      return 'QUERY_STREAM_ENCRYPTION_STATUS'
    else:
      return 'NOT FOUND'

  def parse(self):
    self.add_result('Request ID', 0, 0, 7, printfn=MultiByteDownReply.printfn_reqid)
    self.add_result('Request ID', 0, 0, 7, printfn=MultiByteDownReply.printfn_reqid)
'''

class MultiByteUpRequest(MultiByteParser):
  name = 'UP_REQ'
  start = 0x1600
  end = 0x17FF

  def parse(self):
    self.add_result()

class RangeSinkCountESI(RangeSinkCountParser):
  name = 'SINK_COUNT_ESI'
  start = 0x2002
  end = 0x2002

class RangeDeviceServiceIRQESI0(RangeDeviceServiceIRQParser):
  name = 'DEVICE_SERVICE_IRQ_VECTOR_ESI0'
  start = 0x2003
  end = 0x2003

class RangeDeviceServiceIRQESI1(RangeParser):
  name = 'DEVICE_SERVICE_IRQ_VECTOR_ESI1'
  start = 0x2004
  end = 0x2004

  def parse(self):
    self.add_result('Reserved', 0, 5, 7)
    self.add_result('DSC_ERROR_STATUS', 0, 4)
    self.add_result('PANEL_REPLAY_ERROR_STATUS', 0, 3)
    self.add_result('CEC_IRQ', 0, 2)
    self.add_result('LOCK_ACQUISITION_REQUEST', 0, 1)
    self.add_result('RX_GTC_MSTR_REQ_STATUS_CHANGE', 0, 0)

class RangeLinkServiceIRQESI0(RangeParser):
  name = 'LINK_SERVICE_IRQ_VECTOR_ESI0'
  start = 0x2005
  end = 0x2005

  def parse(self):
    self.add_result('Reserved', 0, 5, 7)
    self.add_result('CONNECTED_OFF_ENTRY_REQUESTED', 0, 4)
    self.add_result('HDMI_LINK_STATUS_CHANGED', 0, 3)
    self.add_result('STREAM_STATUS_CHANGED', 0, 2)
    self.add_result('LINK_STATUS_CHANGED', 0, 1)
    self.add_result('RX_CAP_CHANGED', 0, 0)

class RangeEDPPSR(RangeParser):
  name = 'eDP PSR Registers (TODO)'
  start = 0x2006
  end = 0x200B

  # TODO
  def parse(self):
    self.add_result('Reserved', 0, 0, 7)
    self.add_result('Reserved', 1, 0, 7)
    self.add_result('Reserved', 2, 0, 7)
    self.add_result('Reserved', 3, 0, 7)
    self.add_result('Reserved', 4, 0, 7)

class RangeLane01StatusESI(RangeLaneStatus):
  name = 'LANE0_1_STATUS_ESI'
  start = 0x200C
  end = 0x200C

  def __init__(self, bytes, value_offset):
    super().__init__(bytes, value_offset, 0)

class RangeLane23StatusESI(RangeLaneStatus):
  name = 'LANE2_3_STATUS_ESI'
  start = 0x200D
  end = 0x200D

  def __init__(self, bytes, value_offset):
    super().__init__(bytes, value_offset, 2)

class RangeLaneAlignStatusUpdatedESI(RangeLaneAlignStatusUpdatedParser):
  name = 'LANE_ALIGN_STATUS_UPDATED_ESI'
  start = 0x200E
  end = 0x200E

class RangeSinkStatusESI(RangeSinkStatusParser):
  name = 'SINK_STATUS_ESI'
  start = 0x200F
  end = 0x200F

class RangeCECTunnelingCap(RangeParser):
  name = 'CEC_TUNNELING_CAPABILITY'
  start = 0x3000
  end = 0x3000

  def parse(self):
    self.add_result('CEC_TUNNELING_CAPABLE', 0, 0)
    self.add_result('CEC_SNOOPING_CAPABLE', 0, 1)
    self.add_result('CEC_MULTIPLE_LA_CAPABLE', 0, 2)
    self.add_result('Reserved', 0, 3, 7)

class MultiByteKsvParser(MultiByteParser):
  def bit_weight(self, x):
    weight = 0
    for i in x:
      weight += bin(i).count('1')
    return '{} 1s, {} 0s'.format(weight, 40 - weight)

  def parse(self):
    self.add_result(self.bit_weight)

class MultiByteBksv(MultiByteKsvParser):
  name = 'Bksv'
  start = 0x68000
  end = 0x68004

class MultiByteR0Prime(MultiByteParser):
  name = 'R0`'
  start = 0x68005
  end = 0x68006

  def parse(self):
    self.add_result()

class MultiByteAksv(MultiByteKsvParser):
  name = 'Aksv'
  start = 0x68007
  end = 0x6800B

class MultiByteAn(MultiByteParser):
  name = 'An'
  start = 0x6800C
  end = 0x68013

  def parse(self):
    self.add_result()

class MultiByteVPrimeH0(MultiByteParser):
  name = 'V`H0'
  start = 0x68014
  end = 0x68017

  def parse(self):
    self.add_result()

class MultiByteVPrimeH1(MultiByteParser):
  name = 'V`H1'
  start = 0x68018
  end = 0x6801B

  def parse(self):
    self.add_result()

class MultiByteVPrimeH2(MultiByteParser):
  name = 'V`H2'
  start = 0x6801C
  end = 0x6801F

  def parse(self):
    self.add_result()

class MultiByteVPrimeH3(MultiByteParser):
  name = 'V`H3'
  start = 0x68020
  end = 0x68023

  def parse(self):
    self.add_result()

class MultiByteVPrimeH4(MultiByteParser):
  name = 'V`H4'
  start = 0x68024
  end = 0x68027

  def parse(self):
    self.add_result()

class RangeBcaps(RangeParser):
  name = 'Bcaps'
  start = 0x68028
  end = 0x68028

  def parse(self):
    self.add_result('Reserved', 0, 2, 7)
    self.add_result('REPEATER', 0, 1)
    self.add_result('HDCP_CAPABLE', 0, 0)

class RangeBstatus(RangeParser):
  name = 'Bstatus'
  start = 0x68029
  end = 0x68029

  def parse(self):
    self.add_result('Reserved', 0, 4, 7)
    self.add_result('REAUTHENTICATION_REQUEST', 0, 3)
    self.add_result('LINK_INTEGRITY_FAILURE', 0, 2)
    self.add_result('R0`_AVAILABLE', 0, 1)
    self.add_result('READY', 0, 0)

class RangeBinfo(RangeParser):
  name = 'Binfo'
  start = 0x6802A
  end = 0x6802B

  def parse(self):
    self.add_result('MAX_DEVS_EXCEEDED', 0, 7)
    self.add_result('DEVICE_COUNT', 0, 0, 6)
    self.add_result('Reserved', 1, 4, 7)
    self.add_result('MAX_CASCADE_EXCEEDED', 1, 3)
    self.add_result('DEPTH', 1, 0, 2)

class MultiByteKsvFifo(MultiByteParser):
  name = 'KSV FIFO'
  start = 0x6802C
  end = 0x6803A

  def parse(self):
    self.add_result()

class RangeAinfo(RangeParser):
  name = 'Ainfo'
  start = 0x6803B
  end = 0x6803B

  def parse(self):
    self.add_result('Reserved', 0, 1, 7)
    self.add_result('REAUTHENTICATION_ENABLE_IRQ_HPD', 0, 0)

class RangeCPReserved(RangeParser):
  name = 'RESERVED'
  start = 0x6803C
  end = 0x6803C

  def parse(self):
    self.add_result('Reserved', 0, 0, 7)

class Parser(object):
  def __init__(self):
    self.registry = self.build_registry(ParserBase)
    self.result = []
    self.unparsed = {}

  def build_registry(self, cls):
    ret = []
    for c in cls.__subclasses__():
      ret += self.build_registry(c)
    # BADCODE: assume if a class is subclassed, it is not a parser
    if not ret:
      ret.append(cls)
    return ret

  def get_parser(self, bytes, offset):
    for r in self.registry:
      if not r.can_parse(offset, bytes):
        continue
      return r
    return None

  def followon_range(self, bytes, offset):
    p = self.get_parser(bytes, offset)
    if not p or not p.need_followon(offset, bytes):
      return None
    return (p.start, p.end)

  def parse(self, bytes, offset):
    i = 0
    while i < len(bytes):
      addr = i + offset
      parsed_bytes = 0
      for r in self.registry:
        if not r.can_parse(addr, bytes[i:]):
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

    if not self.unparsed:
      return

    print('')
    print('-- Unparsed values')
    for a,v in self.unparsed.items():
      print('{:<10}{:<41}[{}]'.format(hex(a),
                                     'UNKNOWN',
                                     hex(v)))
