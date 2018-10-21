# (c) 2015-2018 Paul Sokolovsky. MIT license.
import array
import ffi
import uctypes
from ubinascii import hexlify


py = ffi.open(None)

def D(ret, name, args):
    globals()[name] = py.func(ret, name, args)

D("v", "mp_unix_alloc_exec", "Lpp")


def alloc_exec(sz):
    ptr = array.array("L", [0])
    size = array.array("L", [0])
    #print(ptr, size)
    mp_unix_alloc_exec(sz, ptr, size)
    #print(ptr, size)
    b = uctypes.bytearray_at(ptr[0], sz)
    #print(b)
    return b
