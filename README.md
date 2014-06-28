HK-T6Av2
========

Serial protocol desciption between computer and HK-T6Av2 RC remote

# HK-T6Av2 Protocol
The serial port of the transmitter is set at 115200 baud. I've seen 4
messages so far. Pot-state message, parameter request, parameter dump,
and parameter set.

## Pot-state message
18 Bytes, TX->PC
* Byte [0,1]: Header, always [0x55, 0xFC]
* Byte [2-15]: Payload, Potmeter values.
  * [2] MSB [3] LSB CH1
  * [4] MSB [5] LSB CH2
  * [6] MSB [7] LSB CH3
  * [8] MSB [9] LSB CH4
  * [10] MSB [11] LSB CH5
  * [12] MSB [13] LSB CH6
  * [14] MSB [15] __LSB CH4 but between 0 and 1000?__
* Byte [16,17]: Checksum. All bytes of payload added up, MSB first.

## Parameter Request
3 Bytes, PC->TX
* Byte [0,1]: Header, always [0x55, 0xFA]
* Byte [2]: UNKNOWN, always [0x00]

## Parameter Dump
68 Bytes, TX->PC
* Byte [0,1]: Header, always [0x55, 0xFD]
* Byte [2-66]: payload, see Parameter section.
* Byte [67,68]: Checksum. All bytes of payload added up, MSB first.

## Parameter Set
68 Bytes, PC->TX
* Byte [0,1]: Header. Always [0x55, 0xFF]
* Byte [2-66]: payload. See Parameter section.
* Byte [67,68]: Checksum. All bytes of payload added up, MSB first.

## Parameters
65 Bytes, payload
* Byte [0] upper nibble: TX Model.
  * Resp. Model1-4
* Byte [0] lower nibble: Craft Type.
  *Resp. Acro, heli120, heli90, heli140
* Byte [1]: Reverse. Bitmask.
  * CH8 first, CH1 last. 0 off, 1 on.
* Byte [2-7]: DR values [0-127]
  * [2] CH1, DR off value
  * [3] CH1, DR on value
  * [4] CH2, DR off value
  * [5] CH2, DR on value
  * [6] CH4, DR off value
  * [7] CH4, DR on value
* Byte [8-10]: Swash AFR in percent
  * [8] CH1
  * [9] CH2
  * [10] CH6
* Byte [11-22]: End points for potmeters, [0-127]
  * [11] Left [12] Right CH1
  * [13] Left [14] Right CH2
  * [15] Left [16] Right CH3
  * [17] Left [18] Right CH4
  * [19] Left [20] Right CH5
  * [21] Left [22] Right CH6
* Byte [23-32]: Throttle curve [0-127]
  * [23] Normal [24] ID EP0
  * [25] Normal [26] ID EP1
  * [27] Normal [28] ID EP2
  * [29] Normal [30] ID EP3
  * [31] Normal [32] ID EP4
* Byte [33-42]: Pitch curve [0-127]
  * [33] Normal [34] ID EP0
  * [35] Normal [36] ID EP1
  * [37] Normal [38] ID EP2
  * [39] Normal [40] ID EP3
  * [41] Normal [42] ID EP4
* Byte [43-48]: Subtrim, signed, two's complement
  * [43] CH1
  * [44] CH2
  * [45] CH3
  * [46] CH4
  * [47] CH5
  * [48] CH6
* Byte [49-52]: Mix1 setting
  * [49] upper nibble, source select, resp. CH1-CH6,VRA,VRB
  * [49] lower nibble, destination select, resp. CH1-CH6
  * [50] Uprate in percent
  * [51] Downrate in percent
  * [52] Switch, reps. SWA, SWB, ON, OFF
* Byte [53-56]: Mix2 setting
* Byte [57-60]: Mix3 setting
* Byte [61-64]: Switch Functions
  * [61] Switch A, Resp. NULL, DR, Thrcut, Nor/ID
  * [62] Switch B, Resp. NULL, DR, Thrcut, Nor/ID
  * [63] VRA, resp. NULL, Pith Adjust
  * [64] VRB, resp. NULL, Pith Adjust
