# TowelRads IR Protocol Implementation
# Written by Tim Leonard (https://github.com/TLeonardUK)
# 
# This code is the reversed engineered infrared protocol used by the TowelRads remotes
# which communicate with the smart timed thermostatic towel radiator elements.
#
# This encodes to/from the wacky "tuya stream" format used by UFO-R11 zigbee IR remote.
#
# Using this you can generate the codes you want to relay to your radiator to automate it.

import tuya
import fastlz
import io
import base64
from bisect import bisect
from struct import pack, unpack
from enum import IntEnum
from pprint import pformat

# Epsilon value for accounting for variance in signal timings (in microseconds)
PHASE_LENGTH_EPSILON = 250

# Each message starts with this header with an up high value followed by a low value
# of these lengts (in microseconds).
HEADER_PHASE_LENGTHS = [10200, 4000]

# How long each high signal persists for (in microseconds)
HI_PHASE_LENGTH = 600

# How long each low signal persists for (in microseconds)
LO_PHASE_LENGTH = 1000

# Gap between each packet that is broadcast (in microseconds). A single message 
# is made up of 9 packets.
PACKET_INTERVAL_TIME = 30000

# How many packets of data are expected in each message.
MESSAGE_PACKET_COUNT = 9

# Expected length of a message transmitted over IR.
MESSAGE_BYTE_LENGTH = 3 * MESSAGE_PACKET_COUNT

# The different modes of operation the towel rail can be run in.
class towelrads_mode(IntEnum):

    # Note eco mode is missing here. This is just implemented 
    # by setting the mode to 1 and the temperature to 50.

    # Supposedly there are "night/asc/open-window/fil-pilote/keylock" modes also
    # available for these towelrads, needs investigation to figure them out.

    # Allows setting temperature in the range of 30-70
    COMFORT             = 1 

    # Fixed temperature of 7 degrees
    FROST_PROTECTION    = 2 

    # Run based on the programmed schedules.
    SCHEDULED           = 3

    # TODO No idea what this one is, never seen, might just be an unused value?
    UNKNOWN_4           = 4 

    # Boosts the temperature to max for 2 hours before falling back to old mode.
    BOOST_2HOUR         = 5

    # No heating enabled.
    OFF                 = 6

# A complete message sent from the remote controller to thw towelrads radiator.
# This message is made up of 7 individual 3 byte packets broadcast in a pulse distance
# encoding with some proprietary pulse timings.
class towelrads_message:

    def __repr__(self):
        from pprint import pformat
        return "<" + type(self).__name__ + "> " + pformat(vars(self), indent=4, width=1)

    # --------------------------------------------------------------------------------------------
    # Packet 1
    # --------------------------------------------------------------------------------------------

    # These values are the accumulated time since the remote was turned on, presumably
    # used for syncronising the time on the towel rad. As its cumulative you can get hours > 24.
    # This will overflow roughly once every 10 days.
    time_hour = 0
    time_minute = 0
    time_second = 0

    # --------------------------------------------------------------------------------------------    
    # Packet 2
    # --------------------------------------------------------------------------------------------

    # The mode the radiator should now run in.
    mode = towelrads_mode.COMFORT

    # The temperature in degrees celsius to heat the towel rail to. 
    #
    # WARNING: I have no idea if there are range safeties for this value, be careful you set it
    #          in the safe range the element was designed for.
    #
    temperature = 50

    # Unknown, appears to always be 0.
    unknown_0 = 0
    
    # --------------------------------------------------------------------------------------------
    # Packet 3 - 9
    # --------------------------------------------------------------------------------------------
    
    # Each of the following packets contain 24 bits, each bit represents an hour during the day.
    # If the bit is set, that hour will run in comfort mode, if its not set it will run in night mode.
    # Bits are inverse, counting down from 23:00 to 00:00

    schedule_monday = 0
    schedule_tuesday = 0
    schedule_wednesday = 0
    schedule_thursday = 0
    schedule_friday = 0
    schedule_saturday = 0
    schedule_sunday = 0

# Compares two floating point values and returns true if the difference is less than the epsilon
def equal_with_epsilon(value, target, epsilon = PHASE_LENGTH_EPSILON):
    return abs(value - target) <= epsilon

# Converts 3x 8 bit numbers into a 24bit number
def decode_schedule(a, b, c):
    return (c << 16) | (b << 8) | a
    
# Decompresses a base64 / fastlz wrapped set of ir timings.
def decompress_ir_code(input):
    return tuya.decode_ir(input)
#	payload = base64.decodebytes(input.encode('ascii'))
#
#	payload = pack('<I', len(payload) * 100) + payload
#	payload = fastlz.decompress(payload)
 #   
#	signal = []
#	while payload:
#		assert len(payload) >= 2, f'garbage in decompressed payload: {payload.hex()}'
#		signal.append(unpack('<H', payload[:2])[0])
#		payload = payload[2:]
#
#	return signal

# Compresses a base64 / fastlz wrapped set of ir timings, which can be used directly with the UFO-R11
def compress_ir_code(input):
    return tuya.encode_ir(input, 0)
#	payload = b''.join(pack('<H', t) for t in signal)
#	out = fastlz.compress(payload, compression_level)
#	return base64.encodebytes(payload).decode('ascii').replace('\n', '')

# Converts a 24bit number into 3x 8 bit numbers
def encode_schedule(input):
    return [ 
        input & 0xFF,
        (input >> 8) & 0xFF,
        (input >> 16) & 0xFF
    ]

# Converts a message to the IR signal that needs to be emitted through a UFO-R11 IR blaster.
def encode_towelrads(message):

    binary = ""

    # Convert the message to a list of packets which are a list of bytes.
    packets = []
    packets.append([
        message.time_hour,
        message.time_minute,
        message.time_second
    ])
    packets.append([
        message.mode,
        message.temperature,
        message.unknown_0
    ])
    packets.append(encode_schedule(message.schedule_monday))
    packets.append(encode_schedule(message.schedule_tuesday))
    packets.append(encode_schedule(message.schedule_wednesday))
    packets.append(encode_schedule(message.schedule_thursday))
    packets.append(encode_schedule(message.schedule_friday))
    packets.append(encode_schedule(message.schedule_saturday))
    packets.append(encode_schedule(message.schedule_sunday))

    # Output each packet into signal timings.
    signal = []
    for packet in packets:

        # Packet headers
        signal.append(HEADER_PHASE_LENGTHS[0])
        signal.append(HEADER_PHASE_LENGTHS[1])

        # Output packet bits.
        for byte in packet:
            for bit in range(7, -1, -1):
                bit_mask = (1 << bit)
                bit_set = (byte & bit_mask) != 0
                binary += ("1" if bit_set else "0")
                signal.append(HI_PHASE_LENGTH)
                signal.append((LO_PHASE_LENGTH * 2) if bit_set else LO_PHASE_LENGTH)

        # Gap between packets
        signal.append(PACKET_INTERVAL_TIME)

    print(binary)

    return signal

# Converts an IR signal recieved from a UFO-R11 IR blaster to a towelrads message.
def decode_towelrads(input):
    signal_values = []
    signal_high = True
    ignore_next = False
    packets_found = 0

    bit_value = 0
    bit_index = 0

    #binary = "";

    # The signal input is made up of durations between each phase change. So the even values are
    # always high-phase and odd values are low-phase.
    #
    # The data bits are encoded within this using phase-distance-encoding, where the length of each low phase
    # determines if a 1 or 0 bit is being transmitted.

    for index in range(0, len(input)):
        duration_us = input[index]

        if (ignore_next):
            ignore_next = False
            continue

        # See if we have found the header, if so skip it.
        if (index < len(input) - 1 and equal_with_epsilon(duration_us, HEADER_PHASE_LENGTHS[0]) and equal_with_epsilon(input[index + 1], HEADER_PHASE_LENGTHS[1])):
            ignore_next = True
            continue

        # Else decode as on/off signals
        else:
            if (not signal_high):
                signal_bit = 0

                # Single low interval is equal to a 0 bit
                if (equal_with_epsilon(duration_us, LO_PHASE_LENGTH)): 
                    signal_bit = 0
                # Double low interval is equal to a 1 bit
                elif (equal_with_epsilon(duration_us, LO_PHASE_LENGTH * 2)): 
                    signal_bit = 1
                # Gap before next packet
                elif (equal_with_epsilon(duration_us, PACKET_INTERVAL_TIME, HI_PHASE_LENGTH)): 
                    packets_found += 1
                    if (packets_found >= MESSAGE_PACKET_COUNT): # We only expect 9 packets in total, we can drop any others.
                        break
                    else:
                        signal_high = True
                        ignore_next = False

                        bit_value = 0
                        bit_index = 0
                        continue
                else:
                    raise "Unknown low signal timing, potentially corrupt: " + str(duration_us)
            
                # Append signal bit to the current byte and push into the signal output
                # if we have read a full byte.
                #binary += ("1" if signal_bit else "0")

                bit_value <<= 1
                bit_value |= signal_bit
                bit_index += 1
                if (bit_index >= 8):
                    signal_values.append(bit_value)
                    bit_value = 0
                    bit_index = 0
            else:
                if (not equal_with_epsilon(duration_us, HI_PHASE_LENGTH)): 
                    raise "Unknown high signal timing, potentially corrupt: " + str(duration_us)

            signal_high = not signal_high
            
    # Ensure we have the expected message size.
    if (len(signal_values) != MESSAGE_BYTE_LENGTH):
        raise "Message signal was unexpected size, expected " + str(MESSAGE_BYTE_LENGTH) + " but got " + str(len(signal_values))

    # Decode the decimal values into a message structure.
    message = towelrads_message()
    message.time_hour           = signal_values[0]
    message.time_minute         = signal_values[1]
    message.time_second         = signal_values[2]

    message.mode                = signal_values[3]
    message.temperature         = signal_values[4]
    message.unknown_0           = signal_values[5]
    
    message.schedule_monday     = decode_schedule(signal_values[6], signal_values[7], signal_values[8])
    message.schedule_tuesday    = decode_schedule(signal_values[9], signal_values[10], signal_values[11])
    message.schedule_wednesday  = decode_schedule(signal_values[12], signal_values[13], signal_values[14])
    message.schedule_thursday   = decode_schedule(signal_values[15], signal_values[16], signal_values[17])
    message.schedule_friday     = decode_schedule(signal_values[18], signal_values[19], signal_values[20])
    message.schedule_saturday   = decode_schedule(signal_values[21], signal_values[22], signal_values[23])
    message.schedule_sunday     = decode_schedule(signal_values[24], signal_values[25], signal_values[26])

    #print(binary)

    return message




# Test a signal round trip


signal = "B2covQ9dAvgD4A0DA+gHXQLgAxvgHw/gAydACwFZduAVZ0BjQCdAB0ADwAvAB0AT4BkDAasC4BtnAfgD4DkD4P1n4Pdn4l5vAgNdAg=="
signal2 = "Bzoouw9mAuAHgAMB6wOAA8APwAfAF0AHQBNAB8AD4AcPQBdAE8ADQA8Bc3aAZ0AL4AcD4AMnwBtAE0ALwAdAC+AbA+ATZ+AbP+AfI+D9Z+D9Z+BYZwIDZgI="
signal3 = "B58nkA9hAuAD4DEDA8MHYQLgAz/AD+ADBwE6deAZZ8AvQEvAC8AHQBPgGwPgG2fgG0fgFyPg/Wfg/WfgWGcCA2EC"
#print(signal)

#decoded_timings = decompress_ir_code(signal)    
#print(decoded_timings)

#decoded_message = decode_towelrads(decoded_timings)
#print(decoded_message)

#encoded_timings = encode_towelrads(decoded_message)
#print(encoded_timings)

#encoded_signal  = tuya.encode_ir(encoded_timings)    
#print(encoded_signal)

#print("===========================")

on_message = towelrads_message()
on_message.mode = int(towelrads_mode.COMFORT)
on_message.temperature = 70
print(encode_towelrads(on_message))
print(tuya.encode_ir(encode_towelrads(on_message)))

off_message = towelrads_message()
off_message.mode = int(towelrads_mode.OFF)
off_message.temperature = 70
print(encode_towelrads(off_message))
print(tuya.encode_ir(encode_towelrads(off_message)))

#print("===================")
#print(signal)
#print(tuya.decode_ir(signal))
#print(tuya.encode_ir(tuya.decode_ir(signal)))
#print(tuya.decode_ir(tuya.encode_ir(tuya.decode_ir(signal))))
#print("===================")
#print(signal2)
#print(tuya.decode_ir(signal2))
#print(tuya.encode_ir(tuya.decode_ir(signal2)))
#print(tuya.decode_ir(tuya.encode_ir(tuya.decode_ir(signal2))))
#print("===================")
#print(signal3)
#print(tuya.decode_ir(signal3))
#print(tuya.encode_ir(tuya.decode_ir(signal3)))
#print(tuya.decode_ir(tuya.encode_ir(tuya.decode_ir(signal3))))