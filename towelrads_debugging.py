



# This is some very bastardized NEC encoding, the timings are very off from what they should be.

# 32.768 timer

               
# 10114, 3986, 609, 990, 609, 990, 609, 990, 609, 990, 609, 990, 609, 1985, 609, 990, 609, 990, 609, 990, 609, 990, 609, 990, 609, 1985, 609, 1985, 609, 990, 609, 1985, 609, 1985, 609, 990, 609, 990, 609, 990, 609, 990, 609, 990, 609, 990, 609, 990, 609, 1985, 609

# Header
# 10100, 4000

# Alternating 609/990
# each pulse is 1,600 total

# This seems to just be NEC with the timings slightly different?

def decode_message(ir, as_binary):
    output = []
    real_timings = []
    signal_high = True
    ignore_next = False
    submessages_found = 0

    bit_value = 0
    bit_index = 0

    for index in range(0, len(ir)):
        duration_us = ir[index]
        real_timings.append(duration_us)

        if (ignore_next):
            ignore_next = False
            continue

        # See if we have found the header.
        if (index < len(ir) - 1 and equal_with_epsilon(duration_us, HEADER_PHASE_LENGTHS[0]) and equal_with_epsilon(ir[index + 1], HEADER_PHASE_LENGTHS[1])):
            ignore_next = True
            continue

        # Else decode as on/off signals
        else:
            if (not signal_high):
                signal_bit = 0

                # Single down = 0
                if (equal_with_epsilon(duration_us, LO_PHASE_LENGTH)): 
                    #print(str(duration_us)+" = 0")
                    signal_bit = 0
                # Double down = 1 
                elif (equal_with_epsilon(duration_us, LO_PHASE_LENGTH * 2)): 
                    #print(str(duration_us)+" = 1")
                    signal_bit = 1
                # Gap before repeat
                elif (equal_with_epsilon(duration_us, PACKET_INTERVAL_TIME, HI_PHASE_LENGTH)): 
                    # If we have a large gap, assume its the gap between messages?
                    submessages_found += 1
                    if (submessages_found > 8):
                        real_timings = real_timings[:-1]
                        break
                    else:
                        signal_high = True
                        ignore_next = False

                        bit_value = 0
                        bit_index = 0
                        output.append("_")
                        real_timings.append("_")
                        continue
                else:
                    print("Unknown low signal timing, potentially corrupt: " + str(duration_us))
                    return [[], []]
            
                bit_value <<= 1
                bit_value |= signal_bit
                bit_index += 1
                if (as_binary):
                    output.append(signal_bit)
                elif (bit_index >= 8):
                    output.append(bit_value)
                    bit_value = 0
                    bit_index = 0
            else:
                if (not equal_with_epsilon(duration_us, HI_PHASE_LENGTH)): 
                    print("Unknown high signal timing, potentially corrupt: " + str(duration_us))
                    return [[], []]

            signal_high = not signal_high
            
    return [ real_timings, output ]

ir_signals = [
    # On
    #["On", "CyEotA9nAtcHZwLmA+AFA0ATwAPgBxtAD8AbQAdAD0ADwAvgAwcF1wexAkV2gGdAI+APAwPXB2cCwBvAC8AHwBfgFwfgG2fgF0PgGR/gHc8B5gPgNwPgX2cBZwLhxTfgX8/gXmcCA2cC"],
    #["On", "B3wnmA9fAt8D4AkDA8MHXwLgDxfAG8AH4AMnQBPAA8AXAWx14BFnwCNAM+AHC+ADE8Ab4BMH4Btn4BM/4B8b4F1nAMrgQGdBR+ATA+Bdz+D9Z+AoZwIDXwI="],
    ["On", "C0YowQ9lAuAHZQLsA+AFA0ATwAPAG+ADD0ALQBfAB0ALQANAD0ADwAsF7AOyAnZ2gGcB7APgEQPAM0AjwAvAB0AT4BkD4B1nAewD4DkDAXZ24BnP4P1n4ANn4V+f4F9nA2UCdnbiWgcCA2UC"],
    ["On", "Czgoxw9lAuEHZQLtA+AFA0ATwAPAG+ADD+ADC8AfQAdAF+ADB0ALAYR2gGdAC+APA8A3QB/AC8AHQBPgGwPgG2fgG0fgFyPgXWcAreBeZ+Bfz+D9Z+AoZwIDZQI="],
    ["On", "C08ovw9nAtwHZwLsA+AFA0ATwAPAG+ADD8ALQAfAH+AHB0AbBdwHpAJ/doBn4Acf4AMPA9wHZwLAD8ALwAfAF+AVB+AdZwHsA+A3A+BfZwFnAuEbN0An4DUD4P3P4JDPAgNnAg=="],
    ["On (Reboot)", "B1QoyA9jAvID4C0DA+cHYwLgAztAD0ADwBPACwGRduAVZ8An4Ac34AcXwB/gDwfgF2fgDzfgJxfgxWcApeDGz+HGnwIDYwI="],
    ["On (Reboot Fast)", "B6IowQ9qAu8D4EkDAeIHgANAWwFxduARZ+ADJ0ArQANAE+ADB0AL4BsD4BNn4Bs/4B8j4P1n4P1n4FhnAgNqAg=="],
    ["On (Reboot Fast Second)", "B3EowQ9mAu8D4DEDA/kHZgLgAz/AD8AHQBsBgXbgGWfgAy/AC8AHQEPgGQMBoQLgG2cB7wPgNwPg/Wfg/WfgWmcCA6EC"],

    ["On A", "Cz8oyQ9bAusHWwL5A+ABA+AHD+AHG0Af4AMD4AMfwAvgAx8Bm3aAZ8Ab4AsHQC/AF0AL4AMDwBfgFwfgG2fgF0PgGx/g/Wfgr2cEnQL5A1vgPAPiXAcCA1sC"],
    ["On B", "B0QotA9nAt8HgAMD6gNnAkALwAfAC0AP4AcD4BsbwCMBbHaAZ+AHQ+ADD8ArwAfgAxtAC+APF0AbwAPgG2fAK+AzB+D9Z+D9Z+BYZwIDtgI="],

    # Off
    #["Off", "B4Inkg9hAt4D4AkDA8EHYQLgDxfAG0AHQAPgCyfAE0AfAXF14BVnQCPAL0AHwA/AB0AT4BsD4BNn4Bs/4B8j4KdnQUfgEwPgp8/hF6fgxM8CA74C"],
    ["Off", "C0UovA9kAuAHZALuA+AFA0ATwAPAG+ADD0ALQBfAB8AL4AMPQBNAAwGCdoBnQAvgBwNAL0AD4AMXwA/AB+ADG+ATC+ATZ+ATN+AlGwGtAuDFZwBk4F7P4F9n4V+f4F7PAgNkAg=="],
    ["Off", "C0QovQ9mAt0HZgLtA+AFA0ATwAPAG+ADD+ADC+ADH0AL4AMbQAsBinaAZ0Ab4AcDQB9AA+ADF8APwAfgAxvgEwvgE2fgEzfgJxvg/Wfg92cApeJdBwIDZgI="],
    ["Off", "C0wovQ9mAt4HZgLuA+AFA0ATwAPAG+ADD8ALQAfAH0AHwA/AB0ATAYl2gGdAC+AHA0AnQAPgAxfAD8AH4AMb4BML4BNn4BM34Ccb4P1n4CdnAKXh/TfhJzcCA2YC"],
    ["Off (Reboot)", "B2kovA9mAu0D4C0DA+IHZgLgBzvAE0AHQANAHwF/duARZ0AjQANAJ8ADwA/AB8AX4BcH4BNn4Bc74CEfAagC4P1n4CdnAGbhxjfgXs8CA2YC"],
    ["Off (Reboot Fast)", "B4ooxw9oAu8D4EEDA+AHaALAT4ALA7ACbHbgEWdAI0ADAe8D4AEDwA/AB+ADG+ATC+ATZ+ATN+AnG+BdZ+EVNwHvA+BBA+Bdz+D9Z+AoZwIDaAI="],
    ["Off (Reboot Fast Sec)", "B5covg9nAu8D4DEDA+gHZwLgFT8DpgJ4duARZ0A/QAMB7wPgAQPAD8AH4AMb4BEL4BVnAe8D4D8D4MdnAWcC4ROfQB/gPQPhXzcBZwLgxM8CA6YC"],

    ["Off A", "Bz4otw9hAtkHgAMD7wNhAkALwAfAC0AP4AsD4AsfQBNAA0AvQAdAAwFjdoBnQBPgBwNAH0ADwBfgAwvAE0AH4A8XQBvAA+ATZ8Aj4DsH4F1nAKDgXmfgx8/hxjcCA2EC"],
    ["Off B", "C0couw9mAtwHZgLvA+ABA+AHD+AHG0AfwAPgAxvAC8AbwAcBiXaAZ8Af4AMHwCPgCxPgCxvgAyfgBQsBtALgE2cB7wPgQQPg/Wfg/WfgWGcCA2YC"],

    # Up Temp
    ["Up to 45", "CzkoxQ9fAuEHXwL0A+ABA+AHD+ADG0ALwB9AB0ADQBPgAwNAE+ADAwGSdoBn4AMj4AcLQC/AE8ALQAdAA0AXwAdAC+ANAwGcAuAbZwH0A+A3A+BfZwFfAuD9z+Anz+FfN+BeZwIDXwI="],
    ["Up to 50", "C1oouQ9nAuMHZwLsA+ABA+AHD+ADG0ALQB9AA0AL4BkDA6sCgnaAZwHsA+ARA+ADT0ALQAPAL+ADC8AT4AsH4Btn4As34CUT4B3PAewD4DcD4F9nAWcC4V034Mdn4V6fAgOrAg=="],
    ["Up to 55", "B1MouQ9jAvAHIAMAA+ACA+AHD+ADG0ALQB9AA0AL4AsDwBtAByADAYd2oGfgCyvAEyAnAPDgAwvAD0AHwAPAH+AMBwGiAuAcZwAD4AJn4C4L4F1n4P3P4CnP4V834F5nAgNjAg=="],
    ["Up to 60", "C1MowQ9eAuEHXgL3A+ABA+AHD+ADG0ALQB9AA8ALQAdAA8ATQAvgAQMDmwKRdoBnAfcD4BED4AM7QAvgAwPgEzfgAxvgG2fgAy/gLwvg/Wfg92fiHdcB9wPgNgMCA14C"],
    ["Up to 65", "C1EovA9nAuIHZwLtA+ABA+AHD+ADG0ALQB9AA0AL4AMDwBPgAwdACwGGdoBn4AMr4AcLQCdAE8AHQAvgAwPgDxfgAyPgG2fgAy/gLQsBtgLgxWcAZ+Bez+D9Z+AoZwIDtgI="],
    ["Up to 70", "C1coxw9ZAvEHWQL8A+ABA+AHD+ADG0ALQB9AA0AL4AMDQBNAA0ATQAfAAwGPdoBnQBfgDwNAK0AbwAdAC0ADQA9AA0AL4BcD4Btn4BdD4Bsf4MVnAJ/gxs/hxp8CA1kC"],

    # Down Temp
    ["Down to 65", "C1gowg9mAuQHZgLuA+ABA+AHD8Ab4AcX4AcPwCfgAwcF5AeuAop2gGfgAxfgBwsD5AdmAkATwAdAC+ADA+APF+ABI+AdZwHuA+A3A+DHZwFmAuEbn0An4DcD4P1n4CZnAgOuAg=="],
    ["Down to 60", "C0sovA9bAuoHWwL6A+ABA+AHD8Ab4AcX4AcP4AMnQBuAAwObApN2gGfAH+ALBwPqB1sCwBdAC+ADA8AX4BcH4Btn4BdD4Bsf4F1n4R03AfoD4DkD4F3P4P1n4ChnAgNbAg=="],
    ["Down to 55", "C1Uovg9ZAuwHWQL8A+ABA+AHD8Ab4AcX4B8PAYZ2gGfAR+ALB+ADS0ALQANAJ0AHwANAD+ATA+AbZ+ATP+AfG+BdZwCh4MZn4V834MZnAgOhAg=="],
    ["Down to 50", "C1goww9mAtwHZgLuA+ABA+AHD8Ab4AcX4A8PQBdAA4A3A7ECf3aAZwHuA+ARA+ABL4AL4AcPQBfgFwPgG2fgF0PgGR/gHc8B7gPgNwPgX2cBZgLh/TfhjjcCA2YC"],
    ["Down to 45", "C1Eoxw9nAt4HZwLuA+ABA+AHD8Ab4AcX4AsPQBNAA+ADMwGMdoBnwBPgCwfgBzNAI0ATQAPAC0AH4BEDAa0C4BtnAe4D4DkD4P1n4P1n4FhnAgNnAg=="],
    ["Down to 40", "C2Eotg9lAucHZQLuA+ABA+AHD8Ab4AcXQA9AA8AfwAfAE8AHAYZ2gGfAH+ALB8ArQBvAC8AHQBPgGQMBpgLgG2cB7gPgNwPgX2cBZQLgxc/hXzfgX2fhXp8CA2UC"],

    # Modes
    ["Mode Frost", "C0soxA9iAt8HYgLyA+ABA+AHD8AbwBfgAwfAC0AjwAtAB0ADwBMBhXaAZ0AP4AsDwCvAG8APwAfAF+AVBwGtAuAXZwHyA+A9A+D9Z+CPZ+LGBwIDYgI="],
    ["Mode Frost", "B1oouA9ZAv0D4DEDA/sHWQLAP+ADC+ADEwGFduAVZ+AHN8APwAfAS+AVBwGcAuAXZwH9A+A9A+D9Z+D9Z+BYZwIDWQI="],
    ["Mode Schedule", "C0coyQ9pAtsHaQLrA+ABA+AHD8AbwBdAB0ADwBfgAwdAF0AD4AMTAYl2gGfgAxPgAwtAL0ADwBPAC8AHwBfgFwfgF2fgFz/gHx/g/Wfg/WfgWGcCA2kC"],
    ["Mode Comfort", "C1IoyQ9oAuYHaALsA+ABA+AHD8AbwBdAB0ADwBfAB8ATQAdAA8AXAYJ2gGfAD+ALB+ADL8ALwAfgCy/gCxPgG2fgCzfgJxPg/Wfg/WfgWGcCA2gC"],

    ["Eco On", "C1wotg9mAuAHZgLtA+ABA+AHD8AbwBdAB0ADQBfAB0ALwAPAE0AHQAMBgHaAZ8Af4AsHQCfAF0ALQAPgAw/AC+ATB+AbZ+ATP+AfG+BdZwCq4MZn4f034Sg3AgOqAg=="],
    ["Eco Off", "C1MoyQ9lAtwHZQLwA+ABA+AHD8AbwBdAB0ADQBfAB+ALC4AbA6YCf3aAZwHwA+ARA4ArAWUCQANAC0ADQAtAA+ADC0AP4A0D4B1nAfAD4DkD4BvP4P1n4P1n4DRnAgNlAg=="],

    ["Eco On (Reboot)", "B1govw9mAu4D4CkDA+YHZgJAN8AHQAtAA8APQAdAA0ATAZB24BlnwCtAL0ALQANAC0AD4AMLQA/gDwPgG2fgDzvgIxfgxWcApuDGz+HGnwIDZgI="],
    ["Eco Off (Reboot)", "B1Mozg9VAvsD4BEDAy4EVQLgCx8D8QdVAkAXwAfAC8APwAcF+wOvAoF24Bln4AEvgAvAD0B/wAtAG+ARA+AdZwP7A1UCQFNAB+AvA+Abz+AjY+ALK0AT4ANnQA/gC6/gDxfAK+AXH0An4ANnQA/gTwPgF2fgGasErwL7A1XgGAPgE2fgC2PgCxPgGWcBrwLgD2fgC0/gCxMD+wNVAuAPFwv7A1UC+wNVAvsDVQI="],

    ["2h Boost On", "B2MovQ9rAusD4EEDA+EHawJAT0AHQANACwF2duARZ8AjwAdAL8ALwAdAE+AbAwF2duARZ+AbP+AfIwF2duD9Z+D9Z+BWZwIDawI="],
    ["2h Boost Off", "B10ovQ9pAu0D4D0DAd4H4AEDQFNAD0AHAYd24BlnwCtAL8ALwAdAE+AbA+AbZ+AbR+AXI+DFZwCw4F7P4F9n4cafAgNpAg=="],

    # Times
    ["00:00", "Bz8oxg9fAvID4EUDAeAHgAPAVwFoduARZ+AHK0AzQBPgAwdAC+AbA+ATZ+AbP+AdIwGnAuD9Z+AnZwBf4V434MZnAgNfAg=="],
    ["01:00", "B5Motg9sAusD4BEDA+EHbALgEx/gCxvgAzNACwFaduARZ0AfQAPgA0fAD8AH4AMb4BML4BNn4BM34Ccb4P1n4P1n4FhnAgNsAg=="],
    ["02:00", "B5kotw9uAuoD4A0DA9EHbgLgDxvgExfAN8AHAVt24BFnQCNAA+ADT8APwAfgAxvgEwvgE2fgEzfgJxvg/Wfg/WfgWGcCA24C"],
    ["03:00", "B6Qovg9iAu4D4AcDAIpgEwHdB4ADgA+AEwHuA+AZAwHdB4ArAd0HQAMDigJeduAPZ0AfgANAC8ADQBMD7gOKAoAHQAvgGwMBigKAZwGKAkALAe4D4Bsz4CsjAYoCgGfgKzvgHzMBigJAA+CJZwGKAoADQMfgAwtAD8ADQBdAC8AHwAsBigLgDc8DigLuA0Aj4AMDQBNAA+ADE+AXC0AvgAPgCWcBigKAA+AHQ+APF+AHJ+ADD8AzAYoC4AlnwCcBigKAA8APwAfgExfAI+AGBwIDigI="],
    ["04:00", "B4IouQ9pAu4DgAMD2wdpAuALC8AT4B8HwEfABwFfduAFZ+ADR0AjQAPgBxNAD+AHF0AT4BEDAbcC4BNnAe4D4EED4F1n4P3P4CnP4V834F5nAgO3Ag=="],
    ["05:00", "B6QotQ9oAu8D4AkDA9wHaAJAF8AHQAvgHwNAM0ADwC8BanbgFWfgAytAM8APwAdAE+AbA+ATZ+AbP+AfI+BdZwC14F5n4MfP4cY3AgNoAg=="],
    ["06:00", "B5sotg9rAuwD4AkDAdYHgAPgCxvgFxNAO0AjQAcF1gewAmR24BdnAbACQC/AAwPWB2sCQAvAB0AL4BkDAbAC4BNnAewD4EED4MVn4ds3BLAC7ANr4EgD4lwHAgOwAg=="],
    #["07:00", ""],
    #["08:00", ""],
    #["09:00", ""],
    #["10:00", ""],
    #["11:00", ""],
    ["12:00", "B4UouA9pAu0D4AUDAdoHgAPgBxfgGw9AO+AHJwFjduANZ0AnQC9AA0ALwAPAD8AHwBfgFQcBuALgE2cB7QPgQQPgxWfhXzfgx2fiXgcCA2kC"],
    ["13:00", "B5Qouw9nAvAD4AUDAd0HgANAF0ALQAfgIwNAM0ADgDMDsgJgduANZwPwA2cCQCdAA0ALwAPAD8AHwBfgFQfgFWcB8APgQQPgE8/gQWfgX8/gX2cBZwLhXTfgj2cEsgLwA2fgKQMCA2cC"],

    ["22:00", "B50ovA9uAukD4AEDA+EHbgJAD0AHQANAC+AjA0AzQAPgAzMBYnbgCWfAH0ArQAPAD0AHwA/AB0AT4BsD4BNn4Bs/4B8j4P1n4P1n4FhnAgNuAg=="],
    ["23:00", "DVQotQ9sAtkHbALoA2wCQAdAA+ADC8APQBPgFwPgDysBX3aAZ+ALP0AzQAPgAxvAD8AH4AMb4BML4BNn4BM34Ccb4P1n4P1n4FhnAgNsAg=="],

    ["Schedule", "B2kowg9ZAvoD4B0DA/IHWQLgEyvAH+AHBwFiduAVZ0AvQAPAW+ADC0ATQA9AA0AL4BMD4Bdn4A87QFvgIwPgL2fgD3/gBxeAiwGhAuA3ZwHyB+AdA+AjZ+AfU+ALJ+AjZ+EHE8AP4AtX4AUT4Tk3wGtABwHyB+APA+AVZwHyB4ADQENAA8AP4AMHQBfAA+ADF+AECwIHWQI="],

]

for value in ir_signals:
    operation = value[0]
    signal = value[1]

#    print("==== " + operation + " ====");
#    print("Encoded: " + signal)
    timings = tuya.decode_ir(signal)    
    binary_decoded = decode_message(timings, True)
    decimal_decoded = decode_message(timings, False)
#    print("Timings: ");
#    print(decoded[0])
#    print("Decoded: ")
#    print(decoded[1])

    print(str(operation).ljust(30, " ") + " " + "".join(str(x) for x in binary_decoded[1]) + " " + str(decimal_decoded[1]))
#    print(timings)

# command
# first 8 bits = remote id? destination id? (one controller is 4, one is 214, one is 135/136??) Seems to start at 0 after battery reset, counter?
# next 8 bits = some kind of message id?

# 7 packets
#    first message:
#       byte[0] = hour (accumulating)
#       byte[1] = minute
#       byte[2] = second
#    second message:
#       byte[0] = operation
#                   1 = comfort
#                   2 = frost
#                   3 = schedule
#                   4 = 
#                   5 = 2h boost
#                   6 = off
#                   7 = 
#                   8 =
#                   9 =
#       byte[1] = temperature
#       byte[2] = 0?
#    remaining 5 messages:
#      3 bytes all zero
#      possibly schedule data?
#

2
12
25
10


# start =
# end = 


# 00:00 = Bz8oxg9fAvID4EUDAeAHgAPAVwFoduARZ+AHK0AzQBPgAwdAC+AbA+ATZ+AbP+AdIwGnAuD9Z+AnZwBf4V434MZnAgNfAg==
# 23:00 = DVQotQ9sAtkHbALoA2wCQAdAA+ADC8APQBPgFwPgDysBX3aAZ+ALP0AzQAPgAxvAD8AH4AMb4BML4BNn4BM34Ccb4P1n4P1n4FhnAgNsAg==


#00:00 = 0
#23:00 = 11993120
#12:00 = 786448
#01:00 = 65545
#02:00 = 131082
#03:00 = 196619
#04:00 = 2359306
#05:00 = 327692
#06:00 = 393227
#07:00 = 
#08:00 = 
#09:00 = 

# 144hz
#12:00 = should be around 6,220,800