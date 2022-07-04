#!/bin/sh

# This basic program is used for unpacking .nb0 file of FIH Firmware(Nokia etc) used for flashing.
# can run in dash. dd, od, tr are used mainly
#
# Created : 3rd July 2022
# Author  : HemanthJabalpuri

if [ $# -lt 2 ]; then
  echo "Usage: nb0-unpack.sh file.nb0 outdir"
  exit
fi

nb0f="$1"
outdir="$2"

mkdir -p "$outdir" 2>/dev/null

getData() {
  dd if="$nb0f" bs=1 skip=$1 count=$2 2>/dev/null
}

getInt() {
  getData $1 4 | od -A n -t u4 | tr -d ' '
}

file_count="$(getInt 0)"
data_offset="$((4+file_count*64))"

echo "--File Count: $file_count--"
echo "--Data Offset: $data_offset--"
echo

seekoff=4
for i in $(seq $file_count); do
  hiFileSize="$(getInt $((seekoff+12)))"
  loFileSize="$(getInt $((seekoff+4)))"
  fileSize="$((hiFileSize*0x100000000+loFileSize))"
  filename="$(getData $((seekoff+16)) 48)"
  if [ $fileSize -ne 0 ] && ! [ -f "$outdir/$filename" ]; then
    hiOffset="$(getInt $((seekoff+8)))"
    loOffset="$(getInt $((seekoff)))"
    offset="$((data_offset+hiOffset*0x100000000+loOffset))"
    echo "--FileName: $filename--"
    echo "--Size: $fileSize--"
    echo "--Offset: $offset--"

    dd if="$nb0f" of="$outdir/$filename" iflag=skip_bytes,count_bytes status=progress bs=4096 skip=$offset count=$fileSize
    echo
  fi
  seekoff=$((seekoff+64))
done
