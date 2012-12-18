from llvm.core import *

module = Module.new("tut1")

ty_int = Type.int(32)
func_type = Type.function(ty_int, (ty_int,)*3)

mul_add = Function.new(module, func_type, "mul_add")
mul_add.calling_convention = CC_C
x = mul_add.args[0]; x.name = "x"
y = mul_add.args[1]; y.name = "y"
z = mul_add.args[2]; z.name = "z"

blk = mul_add.append_basic_block("entry")

bldr = Builder.new(blk)
tmp_1 = bldr.mul(x, y, "tmp_1")
tmp_2 = bldr.add(tmp_1, z, "tmp_2")

bldr.ret(tmp_2)

print(module)

