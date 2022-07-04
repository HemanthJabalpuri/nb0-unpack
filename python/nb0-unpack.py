#!/usr/bin/env python3

# This program is used for unpacking .nb0 file of FIH Firmware(Nokia etc) used for flashing.
# requires Python 3.6+
#
# Created : 4th July 2022
# Author  : HemanthJabalpuri
#

import argparse, os, struct, sys


# 64 bytes = 4+4+4+4+(48*1)
FILE_HEADER_FMT = 'I I I I 48s'

fiveSpaces = ' ' * 5


def abort(msg):
    sys.exit(msg)


def getString(name):
    return name.decode('ascii').rstrip('\0')


def checkFile(nb0file, hdrsEnd, fileHeaders, debug):
    lastf = len(fileHeaders) - 1
    fsizefromhdr = fileHeaders[lastf]['dataOffset'] + fileHeaders[lastf]['fileSize']
    fsize = os.stat(nb0file).st_size

    if fsize != fsizefromhdr:
        if debug:
            print(f'FileSize is {fsize} and from header it is {fsizefromhdr}')
        abort(f'{nb0file} is not a .nb0 firmware.')


def printP(name, value):
    print(f'{name.ljust(13)} = {value}')


def printFileHeader(fh):
    printP('FileName', fh['fileName'])
    if fh['hiFileSize'] == 0x00:
        printP('FileSize', fh['fileSize'])
    else:
        printP('HiFileSize', fh['hiFileSize'])
        printP('LoFileSize', fh['loFileSize'])
        printP('FileSize', fh['fileSize'])
    if fh['hiDataOffset'] == 0x00:
        printP('DataOffset', fh['dataOffset'])
    else:
        printP('HiDataOffset', fh['hiDataOffset'])
        printP('LoDataOffset', fh['loDataOffset'])
        printP('DataOffset', fh['dataOffset'])
    print()


def parseFiles(f, hdrsEnd, fileHeaders, debug):
    fileHeader = {}
    (
        fileHeader['loDataOffset'],  # the low data offset
        fileHeader['loFileSize'],    # low file size
        fileHeader['hiDataOffset'],  # high data offset
        fileHeader['hiFileSize'],    # high file size
        fileHeader['fileName']       # file name in the bin file
    ) = struct.unpack(FILE_HEADER_FMT, f.read(struct.calcsize(FILE_HEADER_FMT)))

    fileHeader['fileName'] = fileHeader['fileName'].decode('ascii').rstrip('\0')
    fileHeader['dataOffset'] = hdrsEnd + fileHeader['hiDataOffset'] * 0x100000000 + fileHeader['loDataOffset']
    fileHeader['fileSize'] = fileHeader['hiFileSize'] * 0x100000000 + fileHeader['loFileSize']

    if debug:
        printFileHeader(fileHeader)

    fileHeaders.append(fileHeader)


def extractFile(f, fh, outdir, debug):
    tempsize = fh['fileSize']
    if tempsize == 0:
        return
    outpath = os.path.join(outdir, fh['fileName'])
    if os.path.isfile(outpath) and os.stat(outpath).st_size == fh['fileSize']:
        if debug:
            print(f'Duplicate entry found {fh["fileName"]}, so skipping')
        return

    print(f'{fiveSpaces}{fh["fileName"]}', end='')

    f.seek(fh['dataOffset'])
    size = 4096
    tsize = tempsize
    with open(outpath, 'wb') as ofile:
        while tempsize > 0:
            if tempsize < size:
                size = tempsize
            dat = f.read(size)
            tempsize -= size
            ofile.write(dat)
            print(f'\r{int(100 - ((100 * tempsize) / tsize))}%', end='')

    print(f'\r{fh["fileName"]}{fiveSpaces}')


# main('path/to/nb0file')
def main(nb0file, outdir=None, debug=False, printInfo=False):
    if outdir is None:  # use 'outdir' as default output directory if None specified
        outdir = os.path.join(os.getcwd(), 'outdir')
    if os.path.isfile(outdir):
        abort(f'file with name "{outdir}" exists')

    with open(nb0file, 'rb') as f:
        file_count = struct.unpack('I', f.read(4))[0]
        hdrsEnd = 4 + file_count * struct.calcsize(FILE_HEADER_FMT)

         # Unpack file Headers
        fileHeaders = []
        f.seek(4)
        for i in range(file_count):
            parseFiles(f, hdrsEnd, fileHeaders, debug)

        # Check if it is a .nb0 file or not
        checkFile(nb0file, hdrsEnd, fileHeaders, debug)
 
        if printInfo:
            return

        # Extract partitions using partition headers
        print(f'\nExtracting to {outdir}\n')
        os.makedirs(outdir, exist_ok=True)
        for i in range(file_count):
            extractFile(f, fileHeaders[i], outdir, debug)

    print('\nDone...')


if __name__ == '__main__':
    if not sys.version_info >= (3, 6):
        # Python 3.6 for f-strings
        abort('Requires Python 3.6+')

    parser = argparse.ArgumentParser()
    parser.add_argument('nb0file', help='.nb0 file')
    parser.add_argument('outdir', nargs='?', help='output directory to extract files')
    parser.add_argument('-d', dest='debug', action='store_true', help='enable debug output')
    parser.add_argument('-i', dest='printInfo', action='store_true', help='print information of file and exit')
    args = parser.parse_args()

    main(args.nb0file, args.outdir, args.debug, args.printInfo)
