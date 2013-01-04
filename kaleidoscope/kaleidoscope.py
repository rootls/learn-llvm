#!/usr/bin/env python

import re

#########################################################
######################### LEXER ######################### 
#########################################################

# For "EOF" keyword lexer yields EOFToken()
class EOFToken(object):
    pass

# For "def" keyword lexer yields DefToken()    
class DefToken(object):
    pass

# For "extern" keyword lexer yields ExternToken()
class ExternToken(object):
    pass

# For identifier 'foo' lexer yields IdentifierToken('foo')
class IdentifierToken(object):
    def __init__(self, name):
        self.name = name

# For number 12.34 lexer yields NumberToken(12.34)
class NumberToken(object):
    def __init__(self, value):
        self.value = value

# For character '+' lexer yields CharacterToken('+')
class CharacterToken(object):
    def __init__(self, char):
        self.char = char
    def __eq__(self, other):
        return isinstance(other, CharacterToken) and self.char == other.char
    def __ne__(self, other):
        return not self == other

# Regular expressions to parse tokens
REGEX_NUMBER = re.compile('[0-9]+(?:.[0-9]+)?')
REGEX_IDENTIFIER = re.compile('[a-zA-Z][a-zA-Z0-9]\ *')
REGEX_COMMENT = re.compile('#.*')

# Takes a string and yields tokens, uses regular expressions to parse tokens
def Tokenize(string):
    # Scan string ignoring white spaces
    while string:
        if string[0].isspace():
            string = string[1:]
            continue

        # Run regexes
        comment_match = REGEX_COMMENT.match(string)
        number_match = REGEX_NUMBER.match(string)
        identifier_token = REGEX_IDENTIFIER.match(string)

        # Check if any regexes match
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

#########################################################
########################## AST ##########################
#########################################################

# We have expression, prototype and function object

# Base class for all expression nodes
class ExpressionNode(object):
    pass

# Expression class for numberic literals like '1.0'
class NumberExpressionNode(ExpressionNode):
    def __init__(self, value):
        self.value = value

# Expression class for variables like 'a'
class VariableExpressionNode(ExpressionNode):
    def __init__(self, name):
        self.name = name

# Expression class for binary operator
class BinaryOperatorExpressionNode(ExpressionNode):
    def __init__(self, operator, left, right):
        self.operator = operator
        self.left = left
        self.right = right

# Expression class for function call
class CallExpressionNode(ExpressionNode):
    def __init__(self, calee, args):
        self.calee = calee
        self.args = args

# Prototype class for function which captures it name and argument names
class PrototypeNode(object):
    def __init__(self, name, args):
        self.name = name
        self.args = args

# Function class for function definition
class FunctionNode(object):
    def __init__(self, prototype, body):
        self.prototype = prototype
        self.body = body

#########################################################
######################### PARSER ########################
#########################################################

class Parser(object):
    def __init__(self, tokens, binop_precedence):
        self.tokens = tokens
        self.binop_precedence = binop_precedence
        self.Next()

    def Next(self):
        # self.current is the current token that needs to be parsed
        self.current = self.tokens.next()

    # Get precedence of current token, or -1 if not binary operator
    def GetCurrentTokenPrecedence(self):
        if isinstance(self.current, CharacterToken):
            return self.binop_precedence.get(self.current.char, -1)
        else:
            return -1

    # identifierexpr ::= identifier | identifier '(' expression* ')'
    def ParseIdentifierExpr(self):
        identifier_name = self.current.name
        self.Next()

        if self.current != CharacterToken('('):
            return VariableExpressionNode(identifier_name)

        # Call
        self.Next()
        args = []
        if self.current != CharacterToken(')'):
            while True:
                args.append(self.ParseExpression())
                if self.current == CharacterToken(')'):
                    break
                elif self.current != CharacterToken(','):
                    raise RuntimeError('Expected ")" or "," in argument list')
                self.Next()

        self.Next()
        return CallExpressionNode(identifier_name, args)

    def ParseNumberExpr(self):
        result = NumberExpressionNode(self.current.value)
        self.Next() # eat number
        return result

    def ParseParenExpr(self):
        self.Next() # eat '('
        contents = self.ParseExpression()
        if self.current != CharacterToken(')'):
            raise RuntimeError('Expected ")"')
        self.Next() # eat ')'
        return contents

    # primary ::= identifierexpr | numberexpr | parenexpr
    def ParsePrimary(self):
        if isinstance(self.current, IdentifierToken):
            return self.ParseIdentifierExpr()
        elif isinstance(self.current, NumberToken):
            return self.ParseNumberExpr()
        elif self.current == CharacterToken('('):
            return self.ParseParenExpr()
        else:
            raise RuntimeError('Unknown token when expecting a expression.')

    # binoprhs ::= (operator primary)*
    def ParseBinOpRHS(self, left, left_precedence):
        # If this is a binary operator find its precedence
        while True:
            precedence = self.GetCurrentTokenPrecedence()
            if precedence < left_precedence:
                return left
            binary_operator = self.current.char
            self.Next()
            right = self.ParsePrimary()
            next_precedence = self.GetCurrentTokenPrecedence()
            if precedence < next_precedence:
                right = self.ParseBinOpRHS(right, precedence + 1)
            left = BinaryOperatorExpressionNode(binary_operator, left, right)

    # expression ::= primary binoprhs
    def ParseExpression(self):
        left = self.ParsePrimary()
        return self.ParseBinOpRHS(left, 0)

    # prototype ::= id '(' id* ')'
    def ParsePrototype(self):
        if not isinstance(self.current, IdentifierToken):
            raise RuntimeError('Expected function name in prototype')

        function_name = self.current.name
        self.Next()

        if self.current != CharacterToken('('):
            raise RuntimeError('Expected "(" in prototype')
        self.Next()

        arg_names = []
        while isinstance(self.current, IdentifierToken):
            arg_names.append(self.current.name)
            self.Next()

        if self.current != CharacterToken(')'):
            raise RuntimeError('Expected ")" in prototype')

        self.Next()

        return PrototypeNode(function_name, arg_names)

    # definition ::= def prototype expression
    def ParseDefinition(self):
        self.Next()
        proto = self.ParsePrototype()
        body = self.ParseExpression()
        return FunctionNode(proto, body)

    # toplevelexpr ::= expression
    def ParseTopLevelExpr(self):
        proto = PrototypeNode('', [])
        return FunctionNode(proto, self.ParseExpression())

    # external ::= 'extern' prototype
    def ParseExtern(self):
        self.Next()
        return self.ParsePrototype()

    # Top-Level parsing
    def HandleDefinition(self):
        self.Handle(self.ParseDefinition, 'Parsed a function definition.')

    def HandleExtern(self):
        self.Handle(self.ParseExtern, 'Parsed a extern')

    def HandleTopLevelExpression(self):
        self.Handle(self.ParseTopLevelExpr, 'Parsed a Top-level expression.')

    def Handle(self, function, message):
        try:
            function()
            print message
        except Exception, e:
            print 'Error:', e
            try:
                self.Next()
            except:
                pass

def main():
    operator_precedence = {
        '<' : 10,
        '+' : 20,
        '-' : 30,
        '*' : 40
    }

    while True:
        print 'ready>',
        try:
            raw = raw_input()
        except KeyboardInterrupt:
            return

        parser = Parser(Tokenize(raw), operator_precedence)
        while True:
            # top ::= definition | external | expression | EOF
            if isinstance(parser.current, EOFToken):
                break
            if isinstance(parser.current, DefToken):
                parser.HandleDefinition()
            elif isinstance(parser.current, ExternToken):
                parser.HandleExtern()
            else:
                parser.HandleTopLevelExpression()

if __name__ == '__main__':
    main()

