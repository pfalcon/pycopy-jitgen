# pycopy-jitgen - Generate machine code from Pycopy
#
# This module is part of the Pycopy https://github.com/pfalcon/pycopy
# project.
#
# Copyright (c) 2018 Paul Sokolovsky
#
# The MIT License
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import ffi
import uctypes


RET = 0xc3
MOV_R_IMM = 0xb8
PUSH_R = 0x50
POP_R = 0x58
PUSH_IMM32 = 0x68
JCOND_SHORT = 0x70
JMP_SHORT = 0xeb
JMP = 0xe9
CALL = 0xe8
#JMP_ABS = 0xea
#CALL_ABS = 0x9a
ARITH_IMM8 = 0x83
ARITH_ADD = 0
ARITH_SUB = 5
ARITH_CMP = 7
MOV_RM_R_32 = 0x89
MOV_R_RM_32 = 0x8b

EXT = 0xff
EXT_CALL_RM = 2

EAX = 0
ECX = 1
EDX = 2
EBX = 3
ESP = 4
EBP = 5
ESI = 6
EDI = 7


py = ffi.open(None)


class Codegen:

    def __init__(self, buf):
        self.b = buf
        self._addr = uctypes.addressof(buf)
        self.i = 0

    def emit(self, b):
        self.b[self.i] = b
        self.i += 1

    def emit32(self, v):
        v &= 0xffffffff
        for i in range(4):
            self.b[self.i] = v & 0xff
            self.i += 1
            v >>= 8

    def modrm(self, mod, r_op, r_m):
        return (mod << 6) | (r_op << 3) | r_m

    def mov_imm(self, r, v):
        self.emit(MOV_R_IMM + r)
        self.emit32(v)

    def mov_rr32(self, dest_reg, src_reg):
        self.emit(MOV_R_RM_32)
        self.emit(self.modrm(3, dest_reg, src_reg))

    def load(self, dest_reg, base_reg, offset):
        self.emit(MOV_R_RM_32)
        self.emit(self.modrm(1, dest_reg, base_reg))
        self.emit(offset & 0xff)

    def ret(self):
        self.emit(RET)

    def push(self, r):
        self.emit(PUSH_R + r)

    def pop(self, r):
        self.emit(POP_R + r)

    def push_imm(self, v):
        self.emit(PUSH_IMM32)
        self.emit32(v)

    def call(self, v):
        self.emit(CALL)
        na = self._addr + self.i + 4
        #print(na, v, v - na)
        self.emit32(v - na)

    def call_sym(self, sym):
        p = py.addr(sym)
        #print("Addr of %s:" % sym, hex(p))
        self.call(p)

    def call_r(self, r):
        self.emit(EXT)
        self.emit(self.modrm(3, EXT_CALL_RM, r))

    def sub_imm(self, r, v):
        self.emit(ARITH_IMM8)
        self.emit(self.modrm(3, ARITH_ADD, r))
        self.emit(v)

    def pop_args(self, num_args):
        self.sub_imm(ESP, num_args * 4)

    def prolog(self):
        self.push(EBP)
        self.mov_rr32(EBP, ESP)

    def epilog(self):
        self.pop(EBP)
        self.ret()
