# (c) 2015-2018 Paul Sokolovsky. MIT license.
from ubinascii import hexlify
from jitgen import alloc_exec
from jitgen.x86 import *


b = alloc_exec(64)
addr = uctypes.addressof(b)
print("Buf addr:", hex(addr & 0xffffffff))

c = Codegen(b)
c.mov_imm(EAX, 10000)
c.ret()
print(b)
f = ffi.func("i", addr, "")
print(f)
print(f())

c = Codegen(b)
c.push_imm(0)
c.call_sym("mp_obj_new_dict")
c.pop_args(1)
c.ret()
print("code:", hexlify(b))

f = ffi.func("O", uctypes.addressof(b), "")
print(f())

c = Codegen(b)
c.prolog()
c.load(EAX, EBP, 8)
c.load(EBX, EAX, 0)
c.load(ECX, EBX, 5*4)  # unaryop
c.push(EAX)
c.push_imm(5)  # __len__
c.call_r(ECX)
c.pop_args(2)
c.epilog()
print("code:", hexlify(b))

f = ffi.func("O", uctypes.addressof(b), "O")
res = f({1:2})
print("res:", res)
