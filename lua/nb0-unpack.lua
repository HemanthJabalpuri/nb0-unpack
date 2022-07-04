#!/usr/bin/env lua

-- This program is used for unpacking .nb0 file of FIH Firmware(Nokia etc) for flashing.
-- requires Lua 5.3+
--
-- Author: HemanthJabalpuri
-- Created: July 3rd 2022

if #arg < 1 then
  abort("Usage: nb0-unpack.lua [-d] nb0file\n" .. "\t-d\tenable dubug output\n")
end

debug = false
if arg[1] == "-d" then
  debug = true
end
nb0f = arg[#arg]

f = io.open(nb0f, "rb")
data = f:read(4)

fiveSpaces = "     "

function getString(off, n)
  local b = { string.unpack(string.rep("b", n), data, off) }
  local str = ""
  for i = 1, #b - 1 do
    if b[i] ~= 0 then
      str = str .. string.char(b[i])
    end
  end
  return str
end

function getInt(off)
  return string.unpack("I4", data, off)
end

function printFileHdr(fHdr)
  print("FileName\t= " .. fHdr.fileName)
  print("FileOff\t\t= " .. fHdr.offset)
  print("FileSize\t= " .. fHdr.fileSize)
  print("")
end

function extractFile(fHdr)
  tempsize = fHdr.fileSize
  if tempsize == 0 or fHdr.exists then
    return
  end
  io.write(fiveSpaces .. fHdr.fileName)
  f:seek("set", fHdr.offset)
  size = 4096
  tsize = tempsize
  of = io.open(fHdr.fileName, "wb")
  while tempsize > 0 do
    if tempsize < size then
      size = tempsize
    end
    dat = f:read(size)
    tempsize = tempsize - size
    of:write(dat)
    prg = math.floor(100 - ((100 * tempsize) / tsize))
    io.write("\r", prg, "%")
    -- io.flush()
  end
  print("\r" .. fHdr.fileName .. fiveSpaces)
  of:close()
end

file_count = getInt(1)
data_offset = 4 + file_count * 64

lastfHdrOff = 4 + (file_count - 1) * 64
f:seek("set", lastfHdrOff)
data = f:read(64)
fsizefromhdr = data_offset + getInt(9) * 0x100000000 + getInt(1) + getInt(13) * 0x100000000 + getInt(5)
fsize = f:seek("end")
if fsize ~= fsizefromhdr then
  abort(nb0f .. " is not a nb0 firmware.")
end

fHdrs = {}
f:seek("set", 4)
for i = 1, file_count do
  data = f:read(64)
  fName = getString(17, 48)
  duplicate = false
  for j = 1, i - 1 do
    if fHdrs[j].fileName == fName then
      duplicate = true
      break
    end
  end

  fHdrs[i] = {
    offset = data_offset + getInt(9) * 0x100000000 + getInt(1),
    fileSize = getInt(13) * 0x100000000 + getInt(5),
    fileName = fName,
    exists = duplicate
  }

  if debug then
    printFileHdr(fHdrs[i])
  end
end

print("\nExtracting...\n")
for i = 1, file_count do
  extractFile(fHdrs[i])
end

f:close()
