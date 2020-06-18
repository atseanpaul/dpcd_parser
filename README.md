# dpcd_parser
Parse DPCD register values

Usage:
```
$ ./dpcd_parser.py --help
usage: dpcd_parser.py [-h] [--dpcd DPCD] [--logs]

Parse DPCD registers

optional arguments:
  -h, --help   show this help message and exit
  --dpcd DPCD  DPCD values, base16 space separated
  --logs       Read logs from stdin
```


### Device Info
You can put in the first 15 bytes of the DPCD block directly with the --dpcd argument to get the downstream device information

```
$ ./dpcd_parser.py --dpcd "12 14 c2 01 01 15 01 81 02 01 04 01 0f 00 01"
  0x0       DPCD_REV                                 [0x12]
    [1  4:7] Major rev                               1
    [2  0:3] Minor rev                               2
  0x1       MAX_LINK_RATE                            [0x14]
    [20 0:7] Max link rate                           5.4 Gpbs
  0x2       MAX_LANE_COUNT                           [0xc2]
    [1  7:7] Enhanced frame caps                     1
    [1  6:6] Supports TPS3 pattern                   1
    [0  5:5] Supports post-lt adjust                 0
    [2  0:4] Max lane count                          2
  0x3       MAX_DOWNSPREAD                           [0x1]
    [0  7:7] Supports TPS4 pattern                   0
    [0  6:6] Requires AUX for sync                   0
    [0  2:5] Reserved                                0
    [0  1:1] Supports stream regen bit               0
    [1  0:0] Max downspread                          <=0.5%
  0x4       NORP/DP_PWR_VOLTAGE_CAP                  [0x1]
    [0  7:7] Capable of 18V                          0
    [0  6:6] Capable of 12V                          0
    [0  5:5] Capable of 5V                           0
    [0  2:4] Reserved                                0
    [0  1:1] CRC 3D supported                        0
    [1  0:0] Number recv ports                       1
  0x5       DOWN_STREAM_PORT_PRESENT                 [0x15]
    [0  7:7] Reserved                                0
    [1  4:4] Detailed capability available           1
    [0  3:3] Branch converts format                  0
    [2  1:2] Downstream facing port type             HDMI/DVI/DP++
    [1  0:0] Downstream facing port present          1
  0x6       MAIN_LINK_CHANNEL_CODING                 [0x1]
    [0  2:7] Reserved                                0
    [0  1:1] Supports 128b/132b encoding             0
    [1  0:0] Supports 8b/10b encoding                1
  0x7       DOWN_STREAM_PORT_COUNT                   [0x81]
    [1  7:7] IEEE unique ID support                  1
    [0  6:6] Sink requires MSA timing                0
    [0  4:5] Reserved                                0
    [1  0:3] Downstream port count                   1
  0x8       RECEIVE_PORT0_CAP                        [0x2, 0x1]
    [0  6:7] Reserved                                0
    [0  5:5] Buffer size per-lane/port               Per lane
    [0  4:4] Buffer size units                       Pixels
    [0  3:3] HBlank expansion supported              0
    [0  2:2] usage                                   Primary stream
    [1  1:1] Local EDID present                      1
    [0  0:0] Reserved                                0
    [1  0:7] Buffer Size                             64
  0xa       RECEIVE_PORT1_CAP                        [0x4, 0x1]
    [0  6:7] Reserved                                0
    [0  5:5] Buffer size per-lane/port               Per lane
    [0  4:4] Buffer size units                       Pixels
    [0  3:3] HBlank expansion supported              0
    [1  2:2] usage                                   Secondary stream
    [0  1:1] Local EDID present                      0
    [0  0:0] Reserved                                0
    [1  0:7] Buffer Size                             64
  0xc       I2C Speed Control Capabilities Bit Map   [0xf]
    [15 0:7] I2C speed support                       1 Kbps/5 Kbps/10 Kbps/100 Kbps
  0xd       eDP_CONFIGURATION_CAP                    [0x0]
    [0  0:7] Reserved for eDP                        0
  0xe       TRAINING_AUX_RD_INTERVAL                 [0x1]
    [0  7:7] Extended receiver caps available        0
    [1  0:6] Training AUX read interval              ClockReqDone=100us / ChannelEqDone=4000us
```


### Parse DRM/KMS logs
Use the --logs argument to paste drm/kms debug logs into stdin. The tool will pull out the DPCD operations and parse them, it will ignore all other log messages, so just dump the whole log in. Insert a blank line to terminate stdin read.

```
$ ./dpcd_parser.py --logs
[  2 258946.147062] [intel_dp_detect] [CONNECTOR:90:DP-2]
[  2 258946.147063] [intel_power_well_get] enabling power well 2
[  2 258946.147473] [drm_dp_dpcd_read] DPDDC-C: 0x00000 AUX -> (ret= 15) 12 14 e4 01 a1 01 01 81 00 00 04 00 3f 00 01
[  2 258946.147474] [intel_dp_read_dpcd] DPCD: 12 14 e4 01 a1 01 01 81 00 00 04 00 3f 00 01
[  2 258946.147749] [drm_dp_dpcd_read] DPDDC-C: 0x00200 AUX -> (ret=  1) 01
[  2 258946.148140] [drm_dp_dpcd_read] DPDDC-C: 0x00080 AUX -> (ret= 16) 0d 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
[  2 258946.148500] [drm_dp_dpcd_read] DPDDC-C: 0x00500 AUX -> (ret= 12) 00 80 e1 44 70 34 33 32 30 00 07 81
[  2 258946.148501] [drm_dp_read_desc] DP branch: OUI 00-80-e1 dev-ID Dp4320 HW-rev 0.0 SW-rev 7.129 quirks 0x0000
[  2 258946.148775] [drm_dp_dpcd_read] DPDDC-C: 0x00021 AUX -> (ret=  1) 01
[  2 258946.148776] [intel_dp_detect] Sink is MST capable
[  2 258946.149299] [drm_dp_dpcd_write] DPDDC-C: 0x00111 AUX <- (ret=  1) 07
[  2 258946.149437] [drm_dp_dpcd_write] DPDDC-C: 0x002c0 AUX <- (ret=  1) 01
[  2 258946.149591] [drm_dp_dpcd_write] DPDDC-C: 0x001c0 AUX <- (ret=  3) 00 00 3f
[  2 258946.149865] [drm_dp_dpcd_read] DPDDC-C: 0x002c0 AUX -> (ret=  1) 00
[  2 258946.170307] [drm_dp_dpcd_read] DPDDC-C: 0x002c0 AUX -> (ret=  1) 01
[  2 258946.170309] [intel_power_well_put] disabling power well 2
[  2 258946.170317] [drm_helper_hpd_irq_event] [CONNECTOR:90:DP-2] status updated from disconnected to disconnected


[258946.147473] AUX read [0x0:0xe] on DPDDC-C
  0x0       DPCD_REV                                 [0x12]
    [1  4:7] Major rev                               1
    [2  0:3] Minor rev                               2
  0x1       MAX_LINK_RATE                            [0x14]
    [20 0:7] Max link rate                           5.4 Gpbs
  0x2       MAX_LANE_COUNT                           [0xe4]
    [1  7:7] Enhanced frame caps                     1
    [1  6:6] Supports TPS3 pattern                   1
    [1  5:5] Supports post-lt adjust                 1
    [4  0:4] Max lane count                          4
  0x3       MAX_DOWNSPREAD                           [0x1]
    [0  7:7] Supports TPS4 pattern                   0
    [0  6:6] Requires AUX for sync                   0
    [0  2:5] Reserved                                0
    [0  1:1] Supports stream regen bit               0
    [1  0:0] Max downspread                          <=0.5%
  0x4       NORP/DP_PWR_VOLTAGE_CAP                  [0xa1]
    [1  7:7] Capable of 18V                          1
    [0  6:6] Capable of 12V                          0
    [1  5:5] Capable of 5V                           1
    [0  2:4] Reserved                                0
    [0  1:1] CRC 3D supported                        0
    [1  0:0] Number recv ports                       1
  0x5       DOWN_STREAM_PORT_PRESENT                 [0x1]
    [0  7:7] Reserved                                0
    [0  4:4] Detailed capability available           0
    [0  3:3] Branch converts format                  0
    [0  1:2] Downstream facing port type             DisplayPort
    [1  0:0] Downstream facing port present          1
  0x6       MAIN_LINK_CHANNEL_CODING                 [0x1]
    [0  2:7] Reserved                                0
    [0  1:1] Supports 128b/132b encoding             0
    [1  0:0] Supports 8b/10b encoding                1
  0x7       DOWN_STREAM_PORT_COUNT                   [0x81]
    [1  7:7] IEEE unique ID support                  1
    [0  6:6] Sink requires MSA timing                0
    [0  4:5] Reserved                                0
    [1  0:3] Downstream port count                   1
  0x8       RECEIVE_PORT0_CAP                        [0x0, 0x0]
    [0  6:7] Reserved                                0
    [0  5:5] Buffer size per-lane/port               Per lane
    [0  4:4] Buffer size units                       Pixels
    [0  3:3] HBlank expansion supported              0
    [0  2:2] usage                                   Primary stream
    [0  1:1] Local EDID present                      0
    [0  0:0] Reserved                                0
    [0  0:7] Buffer Size                             32
  0xa       RECEIVE_PORT1_CAP                        [0x4, 0x0]
    [0  6:7] Reserved                                0
    [0  5:5] Buffer size per-lane/port               Per lane
    [0  4:4] Buffer size units                       Pixels
    [0  3:3] HBlank expansion supported              0
    [1  2:2] usage                                   Secondary stream
    [0  1:1] Local EDID present                      0
    [0  0:0] Reserved                                0
    [0  0:7] Buffer Size                             32
  0xc       I2C Speed Control Capabilities Bit Map   [0x3f]
    [63 0:7] I2C speed support                       1 Kbps/5 Kbps/10 Kbps/100 Kbps/400 Kbps/1 Mbps
  0xd       eDP_CONFIGURATION_CAP                    [0x0]
    [0  0:7] Reserved for eDP                        0
  0xe       TRAINING_AUX_RD_INTERVAL                 [0x1]
    [0  7:7] Extended receiver caps available        0
    [1  0:6] Training AUX read interval              ClockReqDone=100us / ChannelEqDone=4000us

[258946.147749] AUX read [0x200:0x200] on DPDDC-C
  0x200     SINK_COUNT                               [0x1]
    [0  7:7] SINK_COUNT_bit7                         0
    [0  6:6] CP_READY                                0
    [1  0:5] SINK_COUNT                              1

[258946.148140] AUX read [0x80:0x8f] on DPDDC-C
  0x80      Downstream Facing Port 0 Capabilities    [0xd, 0x0, 0x0, 0x0]
    [0  4:7] NON_EDID_DFPX_ATTRIBUTE                 
    [1  3:3] DFPX_HPD                                HPD Aware
    [5  0:2] DFPX_TYPE                               DP++
    [0  0:7] Maximum TMDS Char Clock Rate            0.0 MHz
    [0  2:7] Reserved                                0
    [0  0:1] Maximum Bits/component                  8bpc
    [0  2:7] Reserved                                0
    [0  1:7] UNDEFINED                               0
    [0  0:0] FRAME_SEQ_TO_FRAME_PACK                 0
  0x84      Downstream Facing Port 1 Capabilities    [0x0, 0x0, 0x0, 0x0]
    [0  4:7] NON_EDID_DFPX_ATTRIBUTE                 
    [0  3:3] DFPX_HPD                                HPD Unaware
    [0  0:2] DFPX_TYPE                               DisplayPort
    [0  0:7] Reserved                                0
    [0  0:7] Reserved                                0
    [0  0:7] Reserved                                0
  0x88      Downstream Facing Port 2 Capabilities    [0x0, 0x0, 0x0, 0x0]
    [0  4:7] NON_EDID_DFPX_ATTRIBUTE                 
    [0  3:3] DFPX_HPD                                HPD Unaware
    [0  0:2] DFPX_TYPE                               DisplayPort
    [0  0:7] Reserved                                0
    [0  0:7] Reserved                                0
    [0  0:7] Reserved                                0
  0x8c      Downstream Facing Port 3 Capabilities    [0x0, 0x0, 0x0, 0x0]
    [0  4:7] NON_EDID_DFPX_ATTRIBUTE                 
    [0  3:3] DFPX_HPD                                HPD Unaware
    [0  0:2] DFPX_TYPE                               DisplayPort
    [0  0:7] Reserved                                0
    [0  0:7] Reserved                                0
    [0  0:7] Reserved                                0

[258946.148500] AUX read [0x500:0x50b] on DPDDC-C
  0x500     Branch IEEE_OUI                          [0x0, 0x80, 0xe1]
             Value                                   0-80-e1
  0x503     Branch Device Identification String      [0x44, 0x70, 0x34, 0x33, 0x32, 0x30]
             Value                                   "Dp4320"
  0x509     Branch Hardware Revision                 [0x0]
    [0  0:3] Minor Revision                          0
    [0  4:7] Major Revision                          0
  0x50a     Branch Firmware Major Revision           [0x7]
    [7  0:7] Revision                                7
  0x50b     Branch Firmware Minor Revision           [0x81]
    [1290:7] Revision                                129

[258946.148775] AUX read [0x21:0x21] on DPDDC-C
  0x21      MSTM_CAP                                 [0x1]
    [0  2:7] Reserved                                0
    [0  1:1] SINGLE_STREAM_SIDEBAND_MSG_SUPPORT      0
    [1  0:0] MST_CAP                                 1

[258946.149299] AUX write [0x111:0x111] on DPDDC-C

-- Unparsed values
0x111     UNKNOWN                                  [0x7]

[258946.149437] AUX write [0x2c0:0x2c0] on DPDDC-C

-- Unparsed values
0x2c0     UNKNOWN                                  [0x1]

[258946.149591] AUX write [0x1c0:0x1c2] on DPDDC-C

-- Unparsed values
0x1c0     UNKNOWN                                  [0x0]
0x1c1     UNKNOWN                                  [0x0]
0x1c2     UNKNOWN                                  [0x3f]

[258946.149865] AUX read [0x2c0:0x2c0] on DPDDC-C

-- Unparsed values
0x2c0     UNKNOWN                                  [0x0]

[258946.170307] AUX read [0x2c0:0x2c0] on DPDDC-C

-- Unparsed values
0x2c0     UNKNOWN                                  [0x1]
```
