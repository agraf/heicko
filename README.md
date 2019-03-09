
# Heicko HR120028A / HREF packet generators

[Heicko](http://www.heicko.de/) has a number of wirelessly remote controllable components. There are window blind motors as well as remote controllable switches. Both of them use the same underlying protocol which these tools de- and encode.

## Protocol

The protocol itself is reasonably simple, but consists of a few layers. It is transmitted on 433Mhz with [OOK](https://en.wikipedia.org/wiki/On-off_keying). The actual payload is [Phase Encoded](https://en.wikipedia.org/wiki/Manchester_code) and looks like this:

| Bits |           Value             |
|------|-----------------------------|
|  16  | Bitmap of blinds to control |
|   8  | Command                     |
|   8  | Controller ID               |
|   8  | Zero?                       |
|   8  | Blind Number                |
|   8  | Rolling Code (obfuscated)   |
|   8  | XOR key                     |

The Command can be any of the following:

  *  DOWN = 0x21
  *  DOT  = 0x41
  *  UP   = 0x81

There are 2 additional commands that are currently unknown. They are probably used for registration/deregistration: 0x11 and 0xa1. I assume 0xa1 might just be Up/Down pressed together.

The Controller ID is unique per remote controller. To determine what your controller's ID is, please record a few frames and decode it.

The Blind Number is the channel printed on the remote control - 1. So if you want to control blind on CH01 then the Blind Number is 0. The Blind Bitmap is calculated as (1 << (Blind Number)).

The Rolling code is slightly obfuscated. It is (Blind Number) XOR Command XOR (Real Rolling Code). The Real Rolling Code is incremented by 1 on every new message. If a message gets sent again (long button press), it will not increase.

## Decoding

The first step to take ownership of your remote control devices is to determine the current Controller ID as well as Rolling Code. For that, I would recommend a simple 433Mhz receiver connected to a [BeagleBoneBlack](https://beagleboard.org/black) running [BeagleLogic](http://beaglelogic.net) firmware. Using that, you can just log into the system and record the 433Mhz signal using sigrok:

```bash
  $ sigrok-cli -d beaglelogic --channels P8_46 -c samplerate=10M -o /dev/shm/cap.sr --continuous
```

You can then copy that file away to any machine you like for post-processing using a script like this:

```bash
set -e
for i in *.sr; do
    SRNAME="$i"
    HEXNAME="${i%*.sr}.hex"
    CAPNAME="${i%*.sr}.cap"
    BINNAME="${i%*.sr}.bin"

    sigrok-cli -i $SRNAME -O hex | cut -d : -f 2- > $HEXNAME
    hex2cap.py $HEXNAME > $CAPNAME
    cap2bin.py $CAPNAME > $BINNAME
done
```

## Encoding

To encode a message all you need to do is run the cmd2cap.py script and then take the timing output from it and put it into a tool that can project it onto the 433Mhz band, such as [pilight](https://www.pilight.org/) or the [NodeMCU 433 Mhz gateway](http://github.com/agraf/nodemcu-433gw).

```bash
  $ cmd2cap.py -c down -b 0x1 -C 0x23
```

## HomeKit

If you want to integrate your Heicko controller window blinds into HomeKit, take a look at the [Homebridge Up/Down/Stop blind plugin](http://github.com/agraf/homebridge-updownstopblind).
