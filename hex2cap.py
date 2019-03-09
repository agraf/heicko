#!/usr/bin/env python
#
# Simple hex to time conversion helper script
# (c) 2019 Alexander Graf <agraf@csgraf.de>

import fileinput

values=[]
for line in fileinput.input():
    line = line.rstrip()
    for t in line.split(" "):
        if t == "00":
            values.append(0)
        else:
            values.append(1)

times=[]
last_val=0
last_time=0
for v in values:
    if last_val == v:
        last_time = last_time + 1
    else:
        times.append(last_time)
        last_val = v
        last_time = 0

for t in times:
    print t
