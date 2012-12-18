#!/usr/bin/env python
from llvm import *
from llvm.core import *

my_module = Module.new('my_module')

ty_int = Type.int()

ty_func = Type.function(ty_int, [ty_int, ty_int])

f_sum = my_module.add_function(ty_func, "sum")

f_sum.args[0].name = "a"
f_sum.args[1].name = "b"

bb = f_sum.append_basic_block("entry")

builder = Builder.new(bb)

tmp = builder.add(f_sum.args[0], f_sum.args[1], "tmp")
builder.ret(tmp)

print my_module

