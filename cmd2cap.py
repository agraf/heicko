#!/usr/bin/env python
#
# Heicko command generator
# (c) 2019 Alexander Graf <agraf@csgraf.de>

import argparse
import binascii
import struct
import fcntl

import fileinput 
import os

class gencap:
    CMD_DOWN = 0x21
    CMD_DOT  = 0x41
    CMD_UP   = 0x81

    def __init__(self, cmd, blindid, ctrlrid, rollingcode = 0, delay = 0):
        self.cmd = cmd
        self.blindid = blindid
        self.ctrlrid = ctrlrid
        self.rollingcode = rollingcode
        self.delay = delay
        self.key = 0

        #/* All elements are big endian */
        #struct blind_cmd_pkg {
        #    uint16_t blind_bitmap; /* (1 << 0..15) */
        #    uint8_t  cmd;
        #    uint8_t  ctrlr_id;     /* Controller ID */
        #    uint8_t  zero;         /* Must be zero? */
        #    uint8_t  blind_nr;     /* 0..15 (CHxx - 1) */
        #    uint8_t  rolling_code; /* blind_nr ^ cmd ^ rolling_code */
        #    uint8_t  key;          /* encryption key for [:5] */
        #};
        self.cmdstruct = struct.Struct(">HBBBB")
        self.calc_cmdpkg()
        self.calc_bits()
        self.calc_bits_me()
        self.calc_times()

    crc8_table = [
            0x00, 0x07, 0x0e, 0x09, 0x1c, 0x1b, 0x12, 0x15,
            0x38, 0x3f, 0x36, 0x31, 0x24, 0x23, 0x2a, 0x2d,
            0x70, 0x77, 0x7e, 0x79, 0x6c, 0x6b, 0x62, 0x65,
            0x48, 0x4f, 0x46, 0x41, 0x54, 0x53, 0x5a, 0x5d,
            0xe0, 0xe7, 0xee, 0xe9, 0xfc, 0xfb, 0xf2, 0xf5,
            0xd8, 0xdf, 0xd6, 0xd1, 0xc4, 0xc3, 0xca, 0xcd,
            0x90, 0x97, 0x9e, 0x99, 0x8c, 0x8b, 0x82, 0x85,
            0xa8, 0xaf, 0xa6, 0xa1, 0xb4, 0xb3, 0xba, 0xbd,
            0xc7, 0xc0, 0xc9, 0xce, 0xdb, 0xdc, 0xd5, 0xd2,
            0xff, 0xf8, 0xf1, 0xf6, 0xe3, 0xe4, 0xed, 0xea,
            0xb7, 0xb0, 0xb9, 0xbe, 0xab, 0xac, 0xa5, 0xa2,
            0x8f, 0x88, 0x81, 0x86, 0x93, 0x94, 0x9d, 0x9a,
            0x27, 0x20, 0x29, 0x2e, 0x3b, 0x3c, 0x35, 0x32,
            0x1f, 0x18, 0x11, 0x16, 0x03, 0x04, 0x0d, 0x0a,
            0x57, 0x50, 0x59, 0x5e, 0x4b, 0x4c, 0x45, 0x42,
            0x6f, 0x68, 0x61, 0x66, 0x73, 0x74, 0x7d, 0x7a,
            0x89, 0x8e, 0x87, 0x80, 0x95, 0x92, 0x9b, 0x9c,
            0xb1, 0xb6, 0xbf, 0xb8, 0xad, 0xaa, 0xa3, 0xa4,
            0xf9, 0xfe, 0xf7, 0xf0, 0xe5, 0xe2, 0xeb, 0xec,
            0xc1, 0xc6, 0xcf, 0xc8, 0xdd, 0xda, 0xd3, 0xd4,
            0x69, 0x6e, 0x67, 0x60, 0x75, 0x72, 0x7b, 0x7c,
            0x51, 0x56, 0x5f, 0x58, 0x4d, 0x4a, 0x43, 0x44,
            0x19, 0x1e, 0x17, 0x10, 0x05, 0x02, 0x0b, 0x0c,
            0x21, 0x26, 0x2f, 0x28, 0x3d, 0x3a, 0x33, 0x34,
            0x4e, 0x49, 0x40, 0x47, 0x52, 0x55, 0x5c, 0x5b,
            0x76, 0x71, 0x78, 0x7f, 0x6a, 0x6d, 0x64, 0x63,
            0x3e, 0x39, 0x30, 0x37, 0x22, 0x25, 0x2c, 0x2b,
            0x06, 0x01, 0x08, 0x0f, 0x1a, 0x1d, 0x14, 0x13,
            0xae, 0xa9, 0xa0, 0xa7, 0xb2, 0xb5, 0xbc, 0xbb,
            0x96, 0x91, 0x98, 0x9f, 0x8a, 0x8d, 0x84, 0x83,
            0xde, 0xd9, 0xd0, 0xd7, 0xc2, 0xc5, 0xcc, 0xcb,
            0xe6, 0xe1, 0xe8, 0xef, 0xfa, 0xfd, 0xf4, 0xf3]

    def AddCrc(self, n):
        r = self.crc8_table[self.crc ^ n]
        #print "crc=%02x n=%02x r=%02x" % (self.crc,n,r)
        self.crc = r
        return r

    def leftRotate(self, n): 
        return ((n << 1)|((n >> 7) & 0x1)) & 0xff
    
    def AddKey(self, n):
        r = self.key
    
        for bit in (0x80, 0x40, 0x20, 0x10, 0x8, 0x4, 0x2, 0x1):
            if r & 0x80:
                r = self.leftRotate(r) ^ 0x7
            else:
                r = self.leftRotate(r)
    
            if not n & bit:
                r ^= 0x7
    
        #print "key=%02x n=%02x r=%02x" % (self.key,n,r)
        self.key = r
        return r

    def calc_cmdpkg(self):
        self.cmdpkg = self.cmdstruct.pack(1 << self.blindid, self.cmd, self.ctrlrid, 0, self.blindid)

        #print "raw cmd: %s" % binascii.hexlify(self.cmdpkg)

        # Obfuscated rolling code
        rollingcode = self.rollingcode ^ self.blindid ^ self.cmd

        # Generate encryption key
        self.crc = 0
        for c in self.cmdpkg:
            self.AddCrc(ord(c))
        self.AddCrc(rollingcode)
        self.key = self.crc

        # Encrypt it
        newpkg = ""
        for c in self.cmdpkg:
            newpkg += chr(ord(c) ^ self.key)
        self.cmdpkg = newpkg + chr(rollingcode) + chr(self.key)

    def calc_bits(self):
        self.bits = ''.join(format(ord(x), '08b') for x in self.cmdpkg)

    def calc_bits_me(self):
        # Prologue
        self.bits_me = "10" * (0x28 + 0x16 + 1)
        self.bits_me += "0" * 0xa

        # Start Bit Sequence
        self.bits_me += "10"

        # Actual data
        for c in self.bits:
            if c == "0":
                self.bits_me += "01"
            elif c == "1":
                self.bits_me += "10"
            else:
                raise Exception("Invalid bit number sequence")

        # Epilogue
        self.bits_me += "0" * 0x44

        # Ensure we submit the epilogue
        self.bits_me += "1"

    def calc_times(self):
        self.times = []
        old_bit = "0"
        cur_time = 0
        for new_bit in self.bits_me:
            if new_bit == old_bit:
                cur_time += self.delay
            else:
                if cur_time:
                    self.times.append(cur_time)
                cur_time = self.delay
                old_bit = new_bit

    def p(self):
        #print "cmd: %s" % binascii.hexlify(self.cmdpkg)
        #print "bits: %s" % self.bits
        #print "bits (Manchester Encoded): %s" % self.bits_me
        #print "times: ",
        for x in self.times:
            print x,

parser = argparse.ArgumentParser()
parser.add_argument("-c", "--cmd", help='Command (down/dot/up)', required=True)
parser.add_argument("-b", "--blind", help='Blind ID', required=True)
parser.add_argument("-C", "--ctrlrid", help='Controller ID', default='0x2b')
parser.add_argument("-r", "--rollingcode", help='Rolling Code (default=0)', default='-1')
parser.add_argument("-d", "--delay", help='Delay between bits in ms (default=400)', default=400, type=int)
args = parser.parse_args()

cmd = 0
if args.cmd == "down":
    cmd = gencap.CMD_DOWN
elif args.cmd == "dot":
    cmd = gencap.CMD_DOT
elif args.cmd == "up":
    cmd = gencap.CMD_UP
else:
    raise Exception("Please specify a valid command (down/dot/up)")

try:
    blindid = int(args.blind, 0)
except:
    raise Exception("Please specify a valid Blind ID (must be a number, not %s)" % args.blind)

try:
    ctrlrid = int(args.ctrlrid, 0)
except:
    raise Exception("Please specify a valid Controller ID (must be a number)")

if args.rollingcode == "-1":
    p = os.path.dirname(os.path.abspath(__file__)) + '/roll'
    with open(p, 'rw+') as f:
        fcntl.lockf(f, fcntl.LOCK_EX)
        rollingcode = int(f.read(), 0)
        f.seek(0, 0)
        f.truncate()
        f.write(hex((rollingcode + 1) & 0xff))
        fcntl.lockf(f, fcntl.LOCK_UN)
else:
    try:
        rollingcode = int(args.rollingcode, 0)
    except:
        raise Exception("Please specify a valid Rolling Code (must be a number, not %s)" % args.blind)

g = gencap(cmd, blindid, ctrlrid, rollingcode=rollingcode, delay=args.delay)
g.p()
