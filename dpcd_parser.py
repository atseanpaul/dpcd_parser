#! /usr/bin/env python3
import argparse
import collections
import re
import sys

import parser

DrmLog = collections.namedtuple('DrmLog',
                                [
                                  'operation',
                                  'port',
                                  'offset',
                                  'type',
                                  'retcode',
                                  'bytes',
                                  'timestamp'
                                ])

def log_bytes_to_list(log_bytes):
  ret = []
  for b in log_bytes.split(' '):
    ret.append(int(b, 16))
  return ret

def log_reader():
  logs = []
  patt_timestamp = r'(?:\[\s*(?:[0-9]+\s+)?([0-9]+\.[0-9]+)\])'
  patt_function = r'\[(?:drm:)?drm_dp_dpcd_(read|write)\]'
  patt_port = r'([\S]+):'
  patt_addr = r'0x([0-9A-Fa-f]+)'
  patt_type = r'([\S]+)'
  patt_dir = r'[-><]{2}'
  patt_ret = r'\(ret=\s+([0-9-]+)\)'
  patt_data = r'((?:[0-9a-fA-F]{2}\s?)+)'
  patt_whitespace = r'\s+'
  pattern = r'{ts}{ws}{fn}{ws}{pt}{ws}{ad}{ws}{tp}{ws}{dr}{ws}{rt}{ws}{dt}'.format(
    ts=patt_timestamp, fn=patt_function, pt=patt_port, ad=patt_addr, tp=patt_type,
    dr=patt_dir,rt=patt_ret,dt=patt_data,ws=patt_whitespace
  )
  regex = re.compile(pattern)
  for line in sys.stdin:
    if line == '\n':
      break
    line = line.rstrip()
    m = regex.findall(line)
    if m:
      logs.append(DrmLog(operation=m[0][1],
                   port=m[0][2],
                   offset=int(m[0][3], 16),
                   type=m[0][4],
                   retcode=int(m[0][5]),
                   bytes=log_bytes_to_list(m[0][6]),
                   timestamp=m[0][0]))
  return logs

def main():
  arg_parser = argparse.ArgumentParser(description='Parse DPCD registers')
  arg_parser.add_argument('--dpcd', help='DPCD values, base16 space separated', default=None)
  arg_parser.add_argument('--logs', help='Read logs from stdin', action='store_true', default=False)
  args = arg_parser.parse_args()

  if args.dpcd:
    p = parser.Parser()
    dpcd = log_bytes_to_list(args.dpcd)
    p.parse(dpcd, 0)
    p.print()

  if args.logs:
    data = log_reader()
    for d in data:
      p = parser.Parser()
      p.parse(d.bytes, d.offset)
      print('')
      print('[{}] {} {} [{}:{}] on {}'.format(d.timestamp, d.type, d.operation, hex(d.offset), hex(d.offset + len(d.bytes) - 1), d.port))
      p.print()


if __name__ == '__main__':
  main()
