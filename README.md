jitgen
======

jitgen is a (very bare) demo of generating machine code at runtime using
Pycopy (https://github.com/pfalcon/pycopy) and executing it.

Current, only x86 (32-bit) is supported. While demo is very bare (and set
of supported instructions is very limited), it tries to show something more
interesting than "a + b", namely, being able to do something about Python
objects. For this, the code generated calls back into Pycopy for
various API functions. For that to work, the executable should export
symbols for functions using -rdynamic linker flag.

Summing up, to try this demo, build Pycopy's Unix version with:

    make MICROPY_FORCE_32BIT=1 LDFLAGS_EXTRA=-rdynamic

License
-------

jitgen is written by Paul Sokolovsky and released under the MIT license.
