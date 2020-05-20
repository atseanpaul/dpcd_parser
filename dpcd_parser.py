#! /usr/bin/env python3
import argparse

def field(val, byte, start_bit, end_bit):
  start_mask = ((1 << (start_bit)) - 1)
  end_mask = ((1 << (end_bit + 1)) - 1)
  mask = start_mask ^ end_mask
  return (val[byte] & mask) >> start_bit

def print_field(label, dpcd, byte, start_bit, end_bit=None, printfn=lambda x: x):
  if end_bit == None:
    end_bit = start_bit
  if end_bit < start_bit:
    raise ValueError('Inverted start/end bits!')
  value = field(dpcd, byte, start_bit, end_bit)
  print('  [{:<3}{}:{}] {:40}{}'.format(byte, start_bit, end_bit, label, printfn(value)))

def print_byte(dpcd, byte):
  print('{:<51}{}'.format(hex(byte), hex(dpcd[byte])))

def downstream_port_type(val):
  if val == 0:
    return 'DisplayPort'
  elif val == 1:
    return 'Analog VGA'
  elif val == 2:
    return 'HDMI/DVI/DP++'
  elif val == 3:
    return 'Others'

def print_port_info(dpcd, port):
  print_byte(dpcd, 8 + (port * 2))
  pfx = 'PORT{}'.format(port)
  print_field('{} Reserved'.format(pfx), dpcd, 8, 6, 7)
  print_field('{} Buffer size per-lane/port'.format(pfx), dpcd, 8, 5, printfn=lambda x: 'Per port' if x else 'Per lane')
  print_field('{} Buffer size units'.format(pfx), dpcd, 8, 4, printfn=lambda x: 'Bytes' if x else 'Pixels')
  print_field('{} HBlank expansion supported'.format(pfx), dpcd, 8, 3)
  print_field('{} usage'.format(pfx), dpcd, 8, 2, printfn=lambda x: 'Secondary stream' if x else 'Primary stream')
  print_field('{} Local EDID present'.format(pfx), dpcd, 8, 1)
  print_field('{} Reserved'.format(pfx), dpcd, 8, 0)
  print('')

  print_byte(dpcd, 9 + (port * 2))
  print_field('{} Buffer Size'.format(pfx), dpcd, 9, 0, 7, lambda x: (x + 1) * 32)
  print('')

def i2c_speed_caps(val):
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

def aux_rd_interval(val):
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

def parse_dpcd(dpcd):
  print_byte(dpcd, 0)
  print_field('Major rev', dpcd, 0, 4, 7)
  print_field('Minor rev', dpcd, 0, 0, 3)
  print('')

  print_byte(dpcd, 1)
  print_field('Max link rate', dpcd, 1, 0, 7, lambda x: '{} Gpbs'.format(x * 0.27))
  print('')

  print_byte(dpcd, 2)
  print_field('Enhanced frame caps', dpcd, 2, 7)
  print_field('Supports TPS3 pattern', dpcd, 2, 6)
  print_field('Supports post-lt adjust', dpcd, 2, 5)
  print_field('Max lane count', dpcd, 2, 0, 4)
  print('')

  print_byte(dpcd, 3)
  print_field('Supports TPS4 pattern', dpcd, 3, 7)
  print_field('Requires AUX for sync', dpcd, 3, 6)
  print_field('Reserved', dpcd, 3, 2, 5)
  print_field('Supports stream regen bit', dpcd, 3, 1)
  print_field('Max downspread', dpcd, 3, 0, printfn=lambda x: '<=0.5%' if x else 'None')
  print('')

  print_byte(dpcd, 4)
  print_field('Capable of 18V', dpcd, 4, 7)
  print_field('Capable of 12V', dpcd, 4, 6)
  print_field('Capable of 5V', dpcd, 4, 5)
  print_field('Reserved', dpcd, 4, 2, 4)
  print_field('CRC 3D supported', dpcd, 4, 1)
  print_field('Number recv ports', dpcd, 4, 0)
  print('')

  print_byte(dpcd, 5)
  print_field('Reserved', dpcd, 5, 5, 7)
  print_field('Detailed capability available', dpcd, 5, 4)
  print_field('Branch converts format', dpcd, 5, 3)
  print_field('Downstream facing port type', dpcd, 5, 1, 2, downstream_port_type)
  print_field('Downstream facing port present', dpcd, 5, 0)
  print('')

  print_byte(dpcd, 6)
  print_field('Reserved', dpcd, 6, 2, 7)
  print_field('Supports 128b/132b encoding', dpcd, 6, 1)
  print_field('Supports 8b/10b encoding', dpcd, 6, 0)
  print('')

  print_byte(dpcd, 7)
  print_field('IEEE unique ID support', dpcd, 7, 7)
  print_field('Sink requires MSA timing', dpcd, 7, 6)
  print_field('Reserved', dpcd, 7, 4, 5)
  print_field('Downstream port count', dpcd, 7, 0, 3)
  print('')

  print_port_info(dpcd, 0)
  print_port_info(dpcd, 1)

  print_byte(dpcd, 0xc)
  print_field('I2C speed support', dpcd, 0xc, 0, 7, i2c_speed_caps)
  print('')

  # TODO: Implement this from eDP spec
  print_byte(dpcd, 0xd)
  print_field('Reserved for eDP', dpcd, 0xd, 0, 7)
  print('')

  print_byte(dpcd, 0xe)
  print_field('Extended receiver caps available', dpcd, 0xe, 7)
  print_field('Training AUX read interval', dpcd, 0xe, 0, 6, aux_rd_interval)
  print('')

def main():
  parser = argparse.ArgumentParser(description='Parse DPCD registers')
  parser.add_argument('--dpcd', help='DPCD values, base16 space separated', required=True)
  args = parser.parse_args()
  dpcd = []
  for b in args.dpcd.split(' '):
    dpcd.append(int(b, 16))
  parse_dpcd(dpcd)

if __name__ == '__main__':
  main()