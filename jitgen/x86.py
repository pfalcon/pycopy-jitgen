# pycopy-jitgen - Generate machine code from Pycopy
#
# This module is part of the Pycopy https://github.com/pfalcon/pycopy
# project.
#
# Copyright (c) 2018-2020 Paul Sokolovsky
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

import uctypes

from .base import BaseCodegen


MOD_IND = 0
MOD_IND8 = 1
MOD_IND32 = 2
MOD_REG = 3

PRE_OPSIZE = 0x66
PRE_ADDRSIZE = 0x67

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
ADD = 0x01
OR  = 0x09
ADC = 0x11
SBB = 0x19
AND = 0x21
SUB = 0x29
XOR = 0x31
CMP = 0x39

SHF32_1 = 0xd1
SHF32_IMM = 0xc1
SHF32_CL = 0xd3
SHF_SHL = 4
SHF_SHR = 5
SHF_SAR = 7

ARITH_IMM8 = 0x83
ARITH_IMM32 = 0x81
ADD_IMM = 0
OR_IMM  = 1
ADC_IMM = 2
SBB_IMM = 3
AND_IMM = 4
SUB_IMM = 5
XOR_IMM = 6
CMP_IMM = 7
MOV_RM_R_8 = 0x88
MOV_RM_R_32 = 0x89
MOV_R_RM_8 = 0x8a
MOV_R_RM_32 = 0x8b
TEST_EAX_IMM = 0xa9

ARITH_F7 = 0xf7
ARITH_F7_NOT = 2
ARITH_F7_NEG = 3
ARITH_F7_MUL = 4
ARITH_F7_IMUL = 5

EXT = 0xff
EXT_CALL_RM = 2

# Condition codes for jcond()
COND_O = 0x00
COND_NO = 0x01
COND_B = 0x02
COND_AE = 0x03
COND_Z = 0x04
COND_NZ = 0x05
COND_BE = 0x06
COND_A = 0x07
COND_S = 0x08
COND_NS = 0x09
COND_P = 0x0a
COND_NP = 0x0b
COND_L = 0x0c
COND_GE = 0x0d
COND_LE = 0x0e
COND_G = 0x0f


class Reg32:

    def __init__(self, id):
        self.id = id

    def __repr__(self):
        return "<Reg32 %d>" % self.id


EAX = Reg32(0)
ECX = Reg32(1)
EDX = Reg32(2)
EBX = Reg32(3)
ESP = Reg32(4)
EBP = Reg32(5)
ESI = Reg32(6)
EDI = Reg32(7)
EIP = Reg32(-1)


class Codegen(BaseCodegen):

    def emit32(self, v):
        v &= 0xffffffff
        for i in range(4):
            self.b[self.i] = v & 0xff
            self.i += 1
            v >>= 8

    def modrm(self, mod, r_op, r_m):
        self.emit((mod << 6) | (r_op << 3) | r_m)

    def modrm_ind(self, r_op, r_m, offset):
        if offset == 0:
            mod = MOD_IND
        elif -128 <= offset <= 127:
            mod = MOD_IND8
        else:
            mod = MOD_IND32
        self.emit((mod << 6) | (r_op << 3) | r_m)
        if mod == MOD_IND8:
            self.emit(offset)
        elif mod == MOD_IND32:
            self.emit32(offset)

    def opsize_pre(self, width):
        if width == 16:
            self.emit(PRE_OPSIZE)

    def mov_imm(self, r, v):
        self.emit(MOV_R_IMM + r)
        i = self.i
        self.emit32(v)
        return i

    def mov_rr32(self, dest_reg, src_reg):
        self.emit(MOV_R_RM_32)
        self.modrm(MOD_REG, dest_reg, src_reg)

    def mov(self, dst, src):
        if isinstance(src, Reg32):
            if src.id == EIP.id:
                self.call_rel(0)
                self.pop(dst)
            else:
                self.mov_rr32(dst.id, src.id)
        elif isinstance(src, int):
            self.mov_imm(dst.id, src)
        else:
            raise NotImplementedError

    def mov_mut(self, dst, val):
        assert isinstance(val, int)
        return self.mov_imm(dst.id, val)

    def load(self, dest_reg, base_reg, offset=0, width=32):
        self.opsize_pre(width)
        self.emit(MOV_R_RM_8 if width == 8 else MOV_R_RM_32)
        self.modrm_ind(dest_reg.id, base_reg.id, offset)

    def _load_ext(self, opcode, dest_reg, base_reg, offset=0, width=32):
        if width == 32:
            return self.load(dest_reg, base_reg, offset, width)
        self.emit(0x0f)
        self.emit(opcode if width == 8 else opcode + 1)
        self.modrm_ind(dest_reg.id, base_reg.id, offset)

    def load_sext(self, dest_reg, base_reg, offset=0, width=32):
        self._load_ext(0xbe, dest_reg, base_reg, offset, width)

    def load_zext(self, dest_reg, base_reg, offset=0, width=32):
        self._load_ext(0xb6, dest_reg, base_reg, offset, width)

    def store(self, src_reg, base_reg, offset=0, width=32):
        self.opsize_pre(width)
        self.emit(MOV_RM_R_8 if width == 8 else MOV_RM_R_32)
        self.modrm_ind(src_reg.id, base_reg.id, offset)

    def ret(self):
        self.emit(RET)

    def push_r(self, r):
        self.emit(PUSH_R + r)

    def pop_r(self, r):
        self.emit(POP_R + r)

    def push_imm(self, v):
        self.emit(PUSH_IMM32)
        self.emit32(v)

    def push(self, src):
        if isinstance(src, Reg32):
            self.push_r(src.id)
        elif isinstance(src, int):
            self.push_imm(src)
        else:
            raise NotImplementedError

    def pop(self, dst):
        if isinstance(dst, Reg32):
            self.pop_r(dst.id)
        else:
            raise NotImplementedError

    def jmp(self, label):
        self.emit(JMP_SHORT)
        self.ref_label(label)
        self.emit(0)

    def jcond(self, cond, label):
        self.emit(JCOND_SHORT + cond)
        self.ref_label(label)
        self.emit(0)

    def call_rel(self, v):
        self.emit(CALL)
        self.emit32(v)

    def call_imm(self, v):
        na = self._addr + self.i + 5
        self.call_rel(v - na)

    def call_sym(self, sym):
        p = self.lookup(sym)
        #print("Addr of %s:" % sym, hex(p))
        self.call_imm(p)

    def call_r(self, r):
        self.emit(EXT)
        self.modrm(MOD_REG, EXT_CALL_RM, r)

    def call(self, arg):
        if isinstance(arg, Reg32):
            self.call_r(arg.id)
        elif isinstance(arg, int):
            self.call_imm(arg)
        elif isinstance(arg, str):
            self.call_sym(arg)
        else:
            raise NotImplementedError

    def arith_rr32(self, op, reg1, reg2):
        self.emit(op)
        self.modrm(MOD_REG, reg2.id, reg1.id)

    def arith_r32_imm(self, op, reg, v):
        if -128 <= v <= 127:
            code = ARITH_IMM8
        else:
            code = ARITH_IMM32
        self.emit(code)
        self.modrm(MOD_REG, op, reg.id)
        if code == ARITH_IMM8:
            self.emit(v)
        else:
            self.emit32(v)

    def _arith(self, op, op_imm, arg1, arg2):
        if isinstance(arg2, int):
            self.arith_r32_imm(op_imm, arg1, arg2)
        else:
            self.arith_rr32(op, arg1, arg2)

    def add(self, arg1, arg2):
        self._arith(ADD, ADD_IMM, arg1, arg2)

    def sub(self, arg1, arg2):
        self._arith(SUB, SUB_IMM, arg1, arg2)

    def and_(self, arg1, arg2):
        self._arith(AND, AND_IMM, arg1, arg2)

    def or_(self, arg1, arg2):
        self._arith(OR, OR_IMM, arg1, arg2)

    def xor(self, arg1, arg2):
        self._arith(XOR, XOR_IMM, arg1, arg2)

    def cmp(self, arg1, arg2):
        self._arith(CMP, CMP_IMM, arg1, arg2)

    def test(self, arg1, arg2):
        if isinstance(arg2, int):
            if arg1.id == EAX.id:
                self.emit(TEST_EAX_IMM)
                self.emit32(arg2)
            else:
                raise NotImplementedError
        else:
            raise NotImplementedError

    # Signed/unsigned multiply, lower word of result
    def mul(self, arg1, arg2):
        if isinstance(arg2, int):
            self.emit(0x69)
            self.modrm(MOD_REG, arg1.id, arg1.id)
            self.emit32(arg2)
        else:
            self.emit(0x0f)
            self.emit(0xaf)
            self.modrm(MOD_REG, arg1.id, arg2.id)

    def _mul_long(self, op, arg1, arg2):
        assert arg1 is EAX
        assert isinstance(arg2, Reg32)
        self._arith_f7(op, arg2)

    def smul_long(self, arg1, arg2):
        self._mul_long(ARITH_F7_IMUL, arg1, arg2)

    def umul_long(self, arg1, arg2):
        self._mul_long(ARITH_F7_MUL, arg1, arg2)

    def _shift(self, op, arg1, arg2):
        imm = 1
        if isinstance(arg2, int):
            imm = arg2
            code = SHF32_IMM
            if arg2 == 1:
                code = SHF32_1
        else:
            assert arg2 is ECX
            code = SHF32_CL
        self.emit(code)
        self.modrm(MOD_REG, op, arg1.id)
        if imm != 1:
            self.emit(imm)

    def shl(self, arg1, arg2):
        self._shift(SHF_SHL, arg1, arg2)

    def shr(self, arg1, arg2):
        self._shift(SHF_SHR, arg1, arg2)

    def sar(self, arg1, arg2):
        self._shift(SHF_SAR, arg1, arg2)

    def _arith_f7(self, op, reg):
        self.emit(0xf7)
        self.modrm(MOD_REG, op, reg.id)

    def neg(self, reg):
        self._arith_f7(ARITH_F7_NEG, reg)

    def not_(self, reg):
        self._arith_f7(ARITH_F7_NOT, reg)

    def pop_args(self, num_args):
        self.sub(ESP, num_args * 4)

    def prolog(self):
        self.push(EBP)
        self.mov(EBP, ESP)

    def epilog(self):
        self.pop(EBP)
        self.ret()

    def patch_imm32(self, off, v):
        "Patch 32-bit immediate value at offset, as returned by mov_mut()."
        v &= 0xffffffff
        for i in range(4):
            self.b[off] = v & 0xff
            off += 1
            v >>= 8

    def link_labels(self):
        for l in self.labels:
            laddr = l[0]
            for ref in l[1:]:
                self.b[ref] = laddr - ref - 1
