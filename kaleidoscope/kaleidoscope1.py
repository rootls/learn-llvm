import re
from llvm.core import Module, Constant, Type, Function, Builder, FCMP_ULT
from llvm.ee import ExecutionEngine, TargetData
from llvm.passes import FunctionPassManager
from llvm.passes import (PASS_INSTRUCTION_COMBINING,
                        PASS_REASSOCIATE,
                        PASS_GVN,
                        PASS_CFG_SIMPLIFICATION)

# Globals
g_llvm_module = Module.new('my cool jit')
g_llvm_builder = None
g_named_values = {}
g_llvm_pass_manager = FunctionPassManager.new(g_llvm_module)
g_llvm_executor = ExecutionEngine.new(g_llvm_module)

class EOFToken(object):
    pass

class DefToken(object):
    pass

class ExternToken(object):
    pass

class IdentifierToken(object):
    def __init__(self, name):
        self.name = name

class NumberToken(object):
    def __init__(self, value):
        self.value = value

class CharacterToken(object):
    def __init__(self, char):
        self.char = char
    def __eq__(self, other):
        return isinstance(other, CharacterToken) and self.char == other.char
    def __ne__(self, other):
        return not self == other

# Regular expressions
REGEX_NUMBER = re.compile('[0-9]+(?:\.[0-9]+)?')
REGEX_IDENTIFIER = re.compile('[a-zA-Z][a-zA-Z0-9]*')
REGEX_COMMENT = re.compile('#.*')

def Tokenize(string):
    while string:
        if string[0].isspace():
            string = string[1:]
            continue

        # Run regexes
        comment_match = REGEX_COMMENT.match(string)
        number_match = REGEX_NUMBER.match(string)
        identifier_match = REGEX_IDENTIFIER.match(string)

        # Check if any of the regexes matched
        if comment_match:
            comment = comment_match.group(0)
            string = string[len(comment):]
        elif number_match:
            number = number_match.group(0)
            yield NumberToken(float(number))
            string = string[len(number):]
        elif identifier_match:
            identifier = identifier_match.group(0)
            if identifier == 'def':
                yield DefToken()
            elif identifier == 'extern':
                yield ExternToken()
            else:
                yield IdentifierToken(identifier)
            string = string[len(identifier):]
        else:
            yield CharacterToken(string[0])
            string = string[1:]

yield EOFToken()

def main():
    # Setup optimizer pipeline
    g_llvm_pass_manager.add(g_llvm_executor.target_data)
    # Do peephole and bit-twiddling optimizations
    g_llvm_pass_manager.add(PASS_INSTRUCTION_COMBINING)
    # Reassociate expression
    g_llvm_pass_manager.add(PASS_REASSOCIATE)
    # Eliminate common sub-expression
    g_llvm_pass_manager.add(PASS_GVN)
    # Simplify the control flow graph
    g_llvm_pass_manager.add(PASS_CFG_SIMPLIFICATION)

    g_llvm_pass_manager.initialize()

    operator_precedence = {
        '<': 10,
        '+': 20,
        '-': 20,
        '*':40
    }

    while True:
        print 'ready>'
        try:
            raw = raw_input()
        except KeyboardInterrupt:
            break

        parser = Parser(Tokenize(raw), operator_precedence)
        while True:
            if isinstance(parser.current, EOFToken):
                break
            if isinstance(parser.current, DefToken):
                parser.HandleDefinition()
            elif isinstance(parser.current, ExternToken):
                parser.HandleExtern()
            else:
                parser.HandleTopLevelExpression()

    print '', g_llvm_module

if __name__ == '__main__':
    main()

