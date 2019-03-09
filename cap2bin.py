#!/usr/bin/env python
#
# Heicko command decoder
# (c) 2019 Alexander Graf <agraf@csgraf.de>

import fileinput

class parsecap:
    STATE_GAP = 0
    STATE_ADJUST = 1
    STATE_WAITFORDATA = 2
    STATE_DATA = 3

    def __init__(self):
        self.bintimes=""
        self.times = []
        self.state = self.STATE_GAP
        self.t_avg = 0
        for line in fileinput.input():
            for t in line.split(" "):
                self.times.append(int(t))

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
    
        self.key = r
        return r

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
        print "crc=%02x n=%02x r=%02x" % (self.crc,n,r)
        self.crc = r
        return r

    def print_bintimes(self):
        realbin=""
        #try:
        if True:
            if self.bintimes != "":
                print "enc: %s (%x)" % (self.bintimes, int(self.bintimes, 2))
                for s in map(''.join, zip(*[iter(self.bintimes)]*2)):
                    if s == "01":
                        realbin = realbin + "0"
                    elif s == "10":
                        realbin = realbin + "1"
                    else:
                        print "Weird sequence found: %s" % s
                realbin = realbin + ("0" * 64)
                realbin = realbin[0:(8*8)]
                realstr = ""
                for s in map(''.join, zip(*[iter(realbin)]*8)):
                    realstr = realstr + chr(int(s, 2))
                xor = ord(realstr[4])
                decstr = ""
                for c in realstr:
                    decstr = decstr + chr(ord(c) ^ xor)

                is_invalid=""
                self.key = 0
                for c in decstr[:6]:
                    self.AddKey(ord(c))
                self.AddKey(ord(realstr[6]))
                if self.key != ord(realstr[4]):
                    is_invalid += " key (%x|%x)" % (self.key, ord(realstr[4]))
                else:
                    is_invalid += " key valid"

                self.crc = 0
                for c in decstr[:6]:
                    self.AddCrc(ord(c))
                self.AddCrc(ord(realstr[6]))
                if self.crc != ord(realstr[4]):
                    is_invalid += " crc (%x|%x)" % (self.crc, ord(realstr[4]))
                else:
                    is_invalid += " crc valid"

                print "dec: %s (%x -> %s (key %s roll %02x%s))" % (realbin, int(realbin, 2), decstr.encode("hex"), hex(xor), ord(decstr[2]) ^ ord(decstr[5]) ^ ord(realstr[6]), is_invalid)
        #except:
        #    pass

    def do_gap(self, t):
        if self.bintimes != "":
            self.print_bintimes()
        print "========= New packet ========="
        if t < 1000:
            print "Weird first gap? Only %d long" % t
        self.state = self.STATE_ADJUST
        self.t_avg = 0
        self.bintimes = ""

    def p(self):
        highlow="1"
        for t in self.times:
            #print "state=%d" % self.state
            # First segment should be a huge gap
            if self.state == self.STATE_GAP:
                self.do_gap(t)
            elif self.state == self.STATE_ADJUST:
                if self.t_avg == 0:
                    self.t_avg = t
                if t < self.t_avg * 4:
                    self.t_avg = (self.t_avg + t) / 2
                else:
                    # This is STATE_WAITFORDATA, but we're already there
                    self.state = self.STATE_DATA
                    highlow="1"
            elif self.state == self.STATE_DATA:
                #print "time: %d" % t
                if t < self.t_avg * 1.5:
                    self.bintimes = self.bintimes + highlow
                elif t < self.t_avg * 3:
                    self.bintimes = self.bintimes + (highlow * 2)
                else:
                    # big gap again
                    self.bintimes = self.bintimes + highlow
                    self.bintimes = self.bintimes[2:128]
                    self.do_gap(t)
                if highlow == "1":
                    highlow = "0"
                else:
                    highlow = "1"

        self.print_bintimes() #int(bintimes, 2)

x = parsecap()
x.p()
