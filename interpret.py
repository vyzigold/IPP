import xml.etree.ElementTree as tree
import argparse
import sys
import re

symbol_table = dict()
frame_stack = list()
instruction_pointer = 1
call_stack = list()
var_stack = list()
instruction_count = 0
var_count = 0
stats_file = None
source_file = None
input_file = None

def arg_error(tpm):
    exit(10)

#Parses program arguments and returns the correct source and input file
def get_inputs():
    #parse the args
    argparser = argparse.ArgumentParser(description = "Interpret XML made from z IPPcode19")
    argparser.add_argument("--source", nargs=1, help="input XML file")
    argparser.add_argument("--input", nargs=1, help="file with inputs to the program")
    argparser.add_argument("--stats", nargs=1, help="file to output the stats to")
    argparser.add_argument("--insts", action='store_const', const="aaa", help="instruction stats, reqs --stats")
    argparser.add_argument("--vars", action="store_const", const="aaa", help="most vars stats, reqs --stats")
    argparser.description = "Interpret for XML generated from IPPcode19"
    argparser.error = arg_error
    args = argparser.parse_args()

    if args.input == None and args.source == None:
        exit(10);

    #assign the correct files to correct variables
    try:
        if args.input == None:
            input_file = sys.stdin
        else:
            input_file = open(args.input[0], "r")

        if args.source == None:
            source_file = sys.stdin
        else:
            source_file = open(args.source[0], "r")
    except:
        exit(11)

    stats_file = None
    try:
        if args.stats != None:
            stats_file = open(args.stats[0], "w")
    except:
        exit(12)

    if (args.insts == "aaa" or args.vars == "aaa") and stats_file == None:
        exit(10)

    return (source_file, input_file, stats_file)

#inits the symbol table
def init_symbol_table():
    symbol_table["GF"] = dict()
    symbol_table["label"] = dict()

#defines label in the symbol table
def make_label(arguments, location):
    if len(arguments) != 1:
        exit(32)
    arg_type, var = arguments[0]

    if arg_type != "label":
        exit(53)
    if var in symbol_table["label"]:
        exit(52)
    symbol_table["label"][var] = int(location) - 1

#returns the code as {'order': ['opcode', [arg1, arg2, ...]], ...},
#where arg = (type, value)
def load_code(source_file):
    try:
        xml_program = tree.parse(source_file).getroot()
    except:
        exit(32)

    #check the program element
    program_checked = False
    for attribute, value in xml_program.attrib.items():
        if attribute == "language" and value == "IPPcode19":
            program_checked = True
        if attribute != "language" and attribute != "name" and attribute != "description":
            exit(32)
    if program_checked == False:
        exit(32)

    instructions = dict()
    missing = list()
    
    #load individual instructions
    for instruction in xml_program:
        if len(instruction.attrib) != 2:
            exit(32)

        order = instruction.attrib["order"]
        opcode = str.lower(instruction.attrib["opcode"])
        if order == None or opcode == "none":
            exit(32)

        if str(int(order) - 1) not in instructions and order != "1":
            missing.append(int(order) - 1)

        if int(order) in missing:
            missing.remove(int(order))

        if order in instructions:
            exit(32)
        
        instructions[order] = list()

        #load the arguments for the instruction
        datatypes = ["string", "int", "var", "float", "nil", "bool", "type", "label"]
        arguments = list()
        try:
            for i in range(len(list(instruction))):
                xml_arg = instruction.find("arg" + str(i + 1))
                if xml_arg.find("*") != None:
                    exit(32)
                if len(xml_arg.attrib) != 1:
                    exit(32)
                if not xml_arg.attrib["type"] in datatypes:
                    exit(53)
                forbiden_chars = ["#", "\n", " ", "\t", "\v", "\f", "\r"]
                if xml_arg.attrib["type"] == "string" and xml_arg.text != None and \
                        any(sub_s in xml_arg.text for sub_s in forbiden_chars):
                    exit(32)
                if xml_arg.attrib["type"] == "string" and xml_arg.text != None:
                   xml_arg.text = unescape(xml_arg.text)
                if xml_arg.attrib["type"] == "string" and xml_arg.text == None:
                    argument = ("string", "")
                else:
                    argument = (xml_arg.attrib["type"], xml_arg.text)
                arguments.append(argument)
                if(xml_arg.tail and xml_arg.tail.strip() != ""):
                    exit(32)
        except:
            exit(32)

        if opcode == "label":
            make_label(arguments, order)
        instructions[order].append(opcode)
        instructions[order].append(arguments)
        #if(instruction.tail.strip() != ""):
        #    exit(32)
        if(instruction.tail and instruction.tail.strip() != ""):
            exit(32)
        if(instruction.text and instruction.text.strip() != ""):
            exit(32)

    #print(xml_program.tail)
    #print(xml_program.text)
    #if(xml_program.)
    #print(xml_program.tail.strip())
    if(xml_program.tail and xml_program.tail.strip() != ""):
        exit(32)
    if(xml_program.text and xml_program.text.strip() != ""):
        exit(32)
    
    if(len(missing) > 0):
        exit(32)
    return instructions

#just checks if the symbol is a valid constant
def is_const(var_type):
    if var_type == "int" or var_type == "string" or \
            var_type == "bool" or var_type == "nil" or var_type == "float":
        return True
    else:
        return False

#returns the prefix and sufix around @
def process_at(var):
    at = var.find("@")
    prefix = var[:at]
    sufix = var[at+1:]

    if sufix.find("@") != -1:
        exit(52)
    return (prefix, sufix)

#checks if the symbol is defined in symbol_table
def is_defined(prefix, sufix):
    if prefix not in symbol_table:
        return 55

    if sufix not in symbol_table[prefix]:
        return 54
    return 0

#returns value from symbol table and also does all the checks for it's existence
def get_symbol(symbol):
    prefix, sufix = process_at(symbol)
    ret_val = is_defined(prefix, sufix)
    if ret_val != 0:
        exit(ret_val)
    value = symbol_table[prefix][sufix]
    if value == None:
        exit(56)
    return value

#executes the defvar instruction: DEFVAR var
def defvar(arguments):
    if len(arguments) != 1:
        exit(32)

    arg_type, var = arguments[0]
    prefix, sufix = process_at(var)

    if arg_type != "var":
        exit(32)

    if prefix not in symbol_table:
        exit(55)

    symbol_table[prefix][sufix] = None

#executes the move instruction: MOVE var symb
def move(arguments):
    if len(arguments) != 2:
        exit(32)

    dest_type, dest = arguments[0]
    source_type, source = arguments[1]

    if dest_type != "var":
        exit(32)

    if source_type != "var" and not is_const(source_type):
        exit(32)

    dest_prefix, dest_sufix = process_at(dest)
    ret_val = is_defined(dest_prefix, dest_sufix)
    if ret_val != 0:
        exit(ret_val)

    if source_type == "var":
        variable = get_symbol(source)
    else:
        if source == None:
            source = ""
        variable = (source_type, source)

    symbol_table[dest_prefix][dest_sufix] = variable

#executes the createframe instruction: CREATEFRAME
def createframe(arguments):
    if len(arguments) != 0:
        exit(32)
    symbol_table["TF"] = dict()

#executes the pushframe instruction: PUHSFRAME
def pushframe(arguments):
    if len(arguments) != 0:
        exit(32)
    if "TF" not in symbol_table:
        exit(55)
    if "LF" in symbol_table:
        frame_stack.append(symbol_table["LF"])
    symbol_table["LF"] = symbol_table.pop("TF")

#executes the popframe instruction: POPFRAME
def popframe(arguments):
    if len(arguments) != 0:
        exit(32)
    if "LF" not in symbol_table:
        exit(55)
    symbol_table["TF"] = symbol_table.pop("LF")
    if len(frame_stack) > 0:
        symbol_table["LF"] = frame_stack.pop()

#executes the call instruction: CALL label
def call(arguments):
    if len(arguments) != 1:
        exit(32)
    
    arg_type, var = arguments[0]
    if arg_type != "label":
        exit(32)

    if var not in symbol_table["label"]:
        exit(52)

    global instruction_pointer
    call_stack.append(instruction_pointer)
    instruction_pointer = symbol_table["label"][var]

#executes the return instruction: RETURN
def return_instruction(arguments):
    if len(arguments) != 0:
        exit(32)
    
    if len(call_stack) == 0:
        exit(56)
    
    global instruction_pointer
    instruction_pointer = call_stack.pop()

#executes the pushs instruction: PUSHS symbol
def pushs(arguments):
    if len(arguments) != 1:
        exit(32)
    
    var_type, var = arguments[0]
    
    if var_type != "var" and not is_const(var_type):
        exit(32)

    if var_type == "var":
        variable = get_symbol(var)
    else:
       variable = (var_type, var)
    var_stack.append(variable)

#executes the pops instruction: POPS var
def pops(arguments):
    if len(arguments) != 1:
        exit(32)
    
    if len(var_stack) == 0:
        exit(56)

    var_type, var = arguments[0]

    if var_type != "var":
        exit(32)

    prefix, sufix = process_at(var)
    ret_val = is_defined(prefix, sufix)
    if ret_val != 0:
        exit(ret_val)

    symbol_table[prefix][sufix] = var_stack.pop()

#executes the clears instruction: CLEARS
def clears(arguments):
    if len(arguments) != 0:
        exit(32)
    
    var_stack.clear()

#executes the add instruction: ADD var symb symb
def add(arguments):
    if len(arguments) != 3:
        exit(32)
    
    dest_type, dest = arguments[0]
    arg1_type, arg1 = arguments[1]
    arg2_type, arg2 = arguments[2]

    dest_prefix, dest_sufix = process_at(dest)
    
    if dest_type != "var":
        exit(32)
    ret_val = is_defined(dest_prefix, dest_sufix)
    if ret_val != 0:
        exit(ret_val)

    if arg1_type == "var":
        arg1_type, arg1 = get_symbol(arg1)

    if arg2_type == "var":
        arg2_type, arg2 = get_symbol(arg2)

    if arg1_type == "int" and arg2_type == "int":
        symbol_table[dest_prefix][dest_sufix] = ("int", str(int(arg1) + int(arg2)))
    
    elif arg1_type == "float" and arg2_type == "float":
        symbol_table[dest_prefix][dest_sufix] = ("float", \
                float(float.fromhex(arg1) + float.fromhex(arg2)).hex())
    else:
        exit(53)

#executes the sub instruction: SUB var symb symb
def sub(arguments):
    if len(arguments) != 3:
        exit(32)
    
    dest_type, dest = arguments[0]
    arg1_type, arg1 = arguments[1]
    arg2_type, arg2 = arguments[2]

    dest_prefix, dest_sufix = process_at(dest)
    
    if dest_type != "var":
        exit(32)

    ret_val = is_defined(dest_prefix, dest_sufix)
    if ret_val != 0:
        exit(ret_val)

    if arg1_type == "var":
        arg1_type, arg1 = get_symbol(arg1)

    if arg2_type == "var":
        arg2_type, arg2 = get_symbol(arg2)

    if arg1_type == "int" and arg2_type == "int":
        symbol_table[dest_prefix][dest_sufix] = ("int", str(int(arg1) - int(arg2)))
    
    elif arg1_type == "float" and arg2_type == "float":
        symbol_table[dest_prefix][dest_sufix] = ("float", \
                float(float.fromhex(arg1) - float.fromhex(arg2)).hex())
    else:
        exit(53)

#executes the mul instruction: MUL var symb symb
def mul(arguments):
    if len(arguments) != 3:
        exit(32)
    
    dest_type, dest = arguments[0]
    arg1_type, arg1 = arguments[1]
    arg2_type, arg2 = arguments[2]

    dest_prefix, dest_sufix = process_at(dest)
    
    if dest_type != "var":
        exit(32)

    ret_val = is_defined(dest_prefix, dest_sufix)
    if ret_val != 0:
        exit(ret_val)

    if arg1_type == "var":
        arg1_type, arg1 = get_symbol(arg1)

    if arg2_type == "var":
        arg2_type, arg2 = get_symbol(arg2)

    if arg1_type == "int" and arg2_type == "int":
        symbol_table[dest_prefix][dest_sufix] = ("int", str(int(arg1) * int(arg2)))
    
    elif arg1_type == "float" and arg2_type == "float":
        symbol_table[dest_prefix][dest_sufix] = ("float", \
                str(float(float.fromhex(arg1) * float.fromhex(arg2)).hex()))
    else:
        exit(53)

#executes the idiv instruction: IDIV
def idiv(arguments):
    if len(arguments) != 3:
        exit(32)
    
    dest_type, dest = arguments[0]
    arg1_type, arg1 = arguments[1]
    arg2_type, arg2 = arguments[2]

    dest_prefix, dest_sufix = process_at(dest)
    
    if dest_type != "var":
        exit(32)

    ret_val = is_defined(dest_prefix, dest_sufix)
    if ret_val != 0:
        exit(ret_val)

    if arg1_type == "var":
        arg1_type, arg1 = get_symbol(arg1)

    if arg2_type == "var":
        arg2_type, arg2 = get_symbol(arg2)

    if arg1_type != "int" or arg2_type != "int":
        exit(53)

    if int(arg2) == 0:
        exit(57)

    symbol_table[dest_prefix][dest_sufix] = ("int", int(int(arg1) // int(arg2)))

#executes the adds instruction: ADDS
def adds(arguments):
    if len(arguments) != 0:
        exit(32)
    
    arg2_type, arg2 = var_stack.pop()
    arg1_type, arg1 = var_stack.pop()

    if arg1_type == "var":
        arg1_type, arg1 = get_symbol(arg1)

    if arg2_type == "var":
        arg2_type, arg2 = get_symbol(arg2)

    if arg1_type == "int" and arg2_type == "int":
        var_stack.append(("int", str(int(arg1) + int(arg2))))
    
    elif arg1_type == "float" and arg2_type == "float":
        var_stack.append(("float", \
                float(float.fromhex(arg1) + float.fromhex(arg2)).hex()))
    else:
        exit(53)

#executes the subs instruction: SUBS
def subs(arguments):
    if len(arguments) != 0:
        exit(32)
    
    arg2_type, arg2 = var_stack.pop()
    arg1_type, arg1 = var_stack.pop()

    if arg1_type == "var":
        arg1_type, arg1 = get_symbol(arg1)

    if arg2_type == "var":
        arg2_type, arg2 = get_symbol(arg2)

    if arg1_type == "int" and arg2_type == "int":
        var_stack.append(("int", str(int(arg1) - int(arg2))))
    
    elif arg1_type == "float" and arg2_type == "float":
        var_stack.append(("float", \
                float(float.fromhex(arg1) - float.fromhex(arg2)).hex()))
    else:
        exit(53)

#executes the muls instruction: MULS
def muls(arguments):
    if len(arguments) != 0:
        exit(32)
    
    arg2_type, arg2 = var_stack.pop()
    arg1_type, arg1 = var_stack.pop()

    if arg1_type == "var":
        arg1_type, arg1 = get_symbol(arg1)

    if arg2_type == "var":
        arg2_type, arg2 = get_symbol(arg2)

    if arg1_type == "int" and arg2_type == "int":
        var_stack.append(("int", str(int(arg1) * int(arg2))))
    
    elif arg1_type == "float" and arg2_type == "float":
        var_stack.append(("float", \
                float(float.fromhex(arg1) * float.fromhex(arg2)).hex()))
    else:
        exit(53)

#executes the idivs instruction: IDIVS
def idivs(arguments):
    if len(arguments) != 0:
        exit(32)
    
    arg2_type, arg2 = var_stack.pop()
    arg1_type, arg1 = var_stack.pop()

    if arg1_type == "var":
        arg1_type, arg1 = get_symbol(arg1)

    if arg2_type == "var":
        arg2_type, arg2 = get_symbol(arg2)

    if arg1_type != "int" or arg2_type != "int":
        exit(53)

    if int(arg2) == 0:
        exit(57)

    var_stack.append(("int", int(int(arg1) // int(arg2))))

#executes the div instruction: DIV
def div(arguments):
    if len(arguments) != 3:
        exit(32)
    
    dest_type, dest = arguments[0]
    arg1_type, arg1 = arguments[1]
    arg2_type, arg2 = arguments[2]

    dest_prefix, dest_sufix = process_at(dest)
    
    if dest_type != "var":
        exit(32)

    ret_val = is_defined(dest_prefix, dest_sufix)
    if ret_val != 0:
        exit(ret_val)

    if arg1_type == "var":
        arg1_type, arg1 = get_symbol(arg1)

    if arg2_type == "var":
        arg2_type, arg2 = get_symbol(arg2)

    if arg1_type != "float" or arg2_type != "float":
        exit(53)

    if float.fromhex(arg2) == 0:
        exit(57)

    symbol_table[dest_prefix][dest_sufix] = ("float", \
            float(float.fromhex(arg1) / float.fromhex(arg2)).hex())

#executes the lt instruction: LT var symb symb
def lt(arguments):
    if len(arguments) != 3:
        exit(32)
    
    dest_type, dest = arguments[0]
    arg1_type, arg1 = arguments[1]
    arg2_type, arg2 = arguments[2]

    dest_prefix, dest_sufix = process_at(dest)
    
    if dest_type != "var":
        exit(32)

    ret_val = is_defined(dest_prefix, dest_sufix)
    if ret_val != 0:
        exit(ret_val)

    if arg1_type == "var":
        arg1_type, arg1 = get_symbol(arg1)

    if arg2_type == "var":
        arg2_type, arg2 = get_symbol(arg2)

    if arg1_type != arg2_type:
        exit(53)

    if arg1_type == "int":
        symbol_table[dest_prefix][dest_sufix] = ("bool", str(int(arg1) < int(arg2)).lower())
    
    elif arg1_type == "bool":
        if arg1 == "false" and arg2 == "true":
            symbol_table[dest_prefix][dest_sufix] = ("bool", "true")
        
        else:
            symbol_table[dest_prefix][dest_sufix] = ("bool", "false")
    
    elif arg1_type == "string":
        symbol_table[dest_prefix][dest_sufix] = ("bool", str(arg1 < arg2).lower())

    elif arg1_type == "float":
        symbol_table[dest_prefix][dest_sufix] = ("bool", str(float.fromhex(arg1) < float.fromhex(arg2)).lower())
    
    else:
        exit(53)

#executes the gt instruction: GT var symb symb
def gt(arguments):
    if len(arguments) != 3:
        exit(32)
    
    dest_type, dest = arguments[0]
    arg1_type, arg1 = arguments[1]
    arg2_type, arg2 = arguments[2]

    dest_prefix, dest_sufix = process_at(dest)
    
    if dest_type != "var":
        exit(32)

    ret_val = is_defined(dest_prefix, dest_sufix)
    if ret_val != 0:
        exit(ret_val)

    if arg1_type == "var":
        arg1_type, arg1 = get_symbol(arg1)

    if arg2_type == "var":
        arg2_type, arg2 = get_symbol(arg2)

    if arg1_type != arg2_type:
        exit(53)

    if arg1_type == "int":
        symbol_table[dest_prefix][dest_sufix] = ("bool", str(int(arg1) > int(arg2)).lower())
    
    elif arg1_type == "bool":
        if arg1 == "true" and arg2 == "false":
            symbol_table[dest_prefix][dest_sufix] = ("bool", "true")
    
        else:
            symbol_table[dest_prefix][dest_sufix] = ("bool", "false")
    
    elif arg1_type == "string":
        symbol_table[dest_prefix][dest_sufix] = ("bool", str(arg1 > arg2).lower())

    elif arg1_type == "float":
        symbol_table[dest_prefix][dest_sufix] = ("bool", str(float.fromhex(arg1) > float.fromhex(arg2)).lower())
    
    else:
        exit(53)

#executes the eq instruction: EQ var symb symb
def eq(arguments):
    if len(arguments) != 3:
        exit(32)
    
    dest_type, dest = arguments[0]
    arg1_type, arg1 = arguments[1]
    arg2_type, arg2 = arguments[2]

    dest_prefix, dest_sufix = process_at(dest)
    
    if dest_type != "var":
        exit(32)

    ret_val = is_defined(dest_prefix, dest_sufix)
    if ret_val != 0:
        exit(ret_val)

    if arg1_type == "var":
        arg1_type, arg1 = get_symbol(arg1)

    if arg2_type == "var":
        arg2_type, arg2 = get_symbol(arg2)

    if arg1_type == "nil" or arg2_type == "nil":
        symbol_table[dest_prefix][dest_sufix] = ("bool", str(arg1_type == arg2_type).lower())
        return

    if arg1_type != arg2_type:
        exit(53)

    if arg1_type == "int":
        symbol_table[dest_prefix][dest_sufix] = ("bool", str(int(arg1) == int(arg2)).lower())
    
    elif arg1_type == "string" or arg1_type == "bool":
        symbol_table[dest_prefix][dest_sufix] = ("bool", str(arg1 == arg2).lower())
    
    elif arg1_type == "nil":
        symbol_table[dest_prefix][dest_sufix] = ("bool", "true") 

    elif arg1_type == "float":
        symbol_table[dest_prefix][dest_sufix] = ("bool", str(float.fromhex(arg1) == float.fromhex(arg2)).lower())

    else:
        exit(53)

#executes the lts instruction: LTS
def lts(arguments):
    if len(arguments) != 0:
        exit(32)
    
    arg2_type, arg2 = var_stack.pop()
    arg1_type, arg1 = var_stack.pop()

    if arg1_type == "var":
        arg1_type, arg1 = get_symbol(arg1)

    if arg2_type == "var":
        arg2_type, arg2 = get_symbol(arg2)

    if arg1_type != arg2_type:
        exit(53)

    if arg1_type == "int":
        var_stack.append(("bool", str(int(arg1) < int(arg2)).lower()))
    
    elif arg1_type == "bool":
        if arg1 == "false" and arg2 == "true":
            var_stack.append(("bool", "true"))
        
        else:
            var_stack.append(("bool", "false"))
    
    elif arg1_type == "string":
        var_stack.append(("bool", str(arg1 < arg2).lower()))

    elif arg1_type == "float":
        var_stack.append(("bool", str(float.fromhex(arg1) < float.fromhex(arg2)).lower()))
    
    else:
        exit(53)

#executes the gts instruction: GTS
def gts(arguments):
    if len(arguments) != 0:
        exit(32)
    
    arg2_type, arg2 = var_stack.pop()
    arg1_type, arg1 = var_stack.pop()

    if arg1_type == "var":
        arg1_type, arg1 = get_symbol(arg1)

    if arg2_type == "var":
        arg2_type, arg2 = get_symbol(arg2)

    if arg1_type != arg2_type:
        exit(53)

    if arg1_type == "int":
        var_stack.append(("bool", str(int(arg1) > int(arg2)).lower()))
    
    elif arg1_type == "bool":
        if arg1 == "true" and arg2 == "false":
            var_stack.append(("bool", "true"))
    
        else:
            var_stack.append(("bool", "false"))
    
    elif arg1_type == "string":
        var_stack.append(("bool", str(arg1 > arg2).lower()))

    elif arg1_type == "float":
        var_stack.append(("bool", str(float.fromhex(arg1) > float.fromhex(arg2)).lower()))
    
    else:
        exit(53)

#executes the eqs instruction: EQS
def eqs(arguments):
    if len(arguments) != 0:
        exit(32)
    
    arg2_type, arg2 = var_stack.pop()
    arg1_type, arg1 = var_stack.pop()

    if arg1_type == "var":
        arg1_type, arg1 = get_symbol(arg1)

    if arg2_type == "var":
        arg2_type, arg2 = get_symbol(arg2)

    if arg1_type == "nil" or arg2_type == "nil":
        var_stack.append(("bool", str(arg1_type == arg2_type).lower()))
        return

    if arg1_type != arg2_type:
        exit(53)

    if arg1_type == "int":
        var_stack.append(("bool", str(int(arg1) == int(arg2)).lower()))
    
    elif arg1_type == "string" or arg1_type == "bool":
        var_stack.append(("bool", str(arg1 == arg2).lower()))
    
    elif arg1_type == "nil":
        var_stack.append(("bool", "true") )

    elif arg1_type == "float":
        var_stack.append(("bool", str(float.fromhex(arg1) == float.fromhex(arg2)).lower()))

    else:
        exit(53)

#executes the and instruction: AND var symb symb
def and_instruction(arguments):
    if len(arguments) != 3:
        exit(32)
    
    dest_type, dest = arguments[0]
    arg1_type, arg1 = arguments[1]
    arg2_type, arg2 = arguments[2]

    dest_prefix, dest_sufix = process_at(dest)
    
    if dest_type != "var":
        exit(32)

    ret_val = is_defined(dest_prefix, dest_sufix)
    if ret_val != 0:
        exit(ret_val)

    if arg1_type == "var":
        arg1_type, arg1 = get_symbol(arg1)

    if arg2_type == "var":
        arg2_type, arg2 = get_symbol(arg2)
    
    if arg1_type != "bool" or arg2_type != "bool":
        exit(53)
    
    if arg1 == "true" and arg2 == "true":
        symbol_table[dest_prefix][dest_sufix] = ("bool", "true")
    
    else:
        symbol_table[dest_prefix][dest_sufix] = ("bool", "false")

#executes the or instruction: OR var symb symb
def or_instruction(arguments):
    if len(arguments) != 3:
        exit(32)
    
    dest_type, dest = arguments[0]
    arg1_type, arg1 = arguments[1]
    arg2_type, arg2 = arguments[2]

    dest_prefix, dest_sufix = process_at(dest)
    
    if dest_type != "var":
        exit(32)

    ret_val = is_defined(dest_prefix, dest_sufix)
    if ret_val != 0:
        exit(ret_val)

    if arg1_type == "var":
        arg1_type, arg1 = get_symbol(arg1)

    if arg2_type == "var":
        arg2_type, arg2 = get_symbol(arg2)
    
    if arg1_type != "bool" or arg2_type != "bool":
        exit(53)
    
    if arg1 == "true" or arg2 == "true":
        symbol_table[dest_prefix][dest_sufix] = ("bool", "true")
    
    else:
        symbol_table[dest_prefix][dest_sufix] = ("bool", "false")

#executes the not instruction: NOT var symb
def not_instruction(arguments):
    if len(arguments) != 2:
        exit(32)
    
    dest_type, dest = arguments[0]
    arg1_type, arg1 = arguments[1]

    dest_prefix, dest_sufix = process_at(dest)
    
    if dest_type != "var":
        exit(32)

    ret_val = is_defined(dest_prefix, dest_sufix)
    if ret_val != 0:
        exit(ret_val)

    if arg1_type == "var":
        arg1_type, arg1 = get_symbol(arg1)

    if arg1_type != "bool":
        exit(53)
    
    if arg1 == "true":
        symbol_table[dest_prefix][dest_sufix] = ("bool", "false")
    
    else:
        symbol_table[dest_prefix][dest_sufix] = ("bool", "true")

#executes the ands instruction: ANDS
def ands(arguments):
    if len(arguments) != 0:
        exit(32)
    
    arg2_type, arg2 = var_stack.pop()
    arg1_type, arg1 = var_stack.pop()

    if arg1_type == "var":
        arg1_type, arg1 = get_symbol(arg1)

    if arg2_type == "var":
        arg2_type, arg2 = get_symbol(arg2)
    
    if arg1_type != "bool" or arg2_type != "bool":
        exit(53)
    
    if arg1 == "true" and arg2 == "true":
        var_stack.append(("bool", "true"))
    
    else:
        var_stack.append(("bool", "false"))

#executes the ors instruction: ORS
def ors(arguments):
    if len(arguments) != 0:
        exit(32)
    
    arg2_type, arg2 = var_stack.pop()
    arg1_type, arg1 = var_stack.pop()

    if arg1_type == "var":
        arg1_type, arg1 = get_symbol(arg1)

    if arg2_type == "var":
        arg2_type, arg2 = get_symbol(arg2)
    
    if arg1_type != "bool" or arg2_type != "bool":
        exit(53)
    
    if arg1 == "true" or arg2 == "true":
        var_stack.append(("bool", "true"))
    
    else:
        var_stack.append(("bool", "false"))

#executes the nots instruction: NOTS
def nots(arguments):
    if len(arguments) != 0:
        exit(32)
    
    arg1_type, arg1 = var_stack.pop()

    if arg1_type == "var":
        arg1_type, arg1 = get_symbol(arg1)

    if arg1_type != "bool":
        exit(53)
    
    if arg1 == "true":
        var_stack.append(("bool", "false"))
    
    else:
        var_stack.append(("bool", "true"))

#executes the int2char instruction: INT2CHAR var symb
def int2char(arguments):
    if len(arguments) != 2:
        exit(32)
    
    dest_type, dest = arguments[0]
    arg1_type, arg1 = arguments[1]

    dest_prefix, dest_sufix = process_at(dest)
    
    if dest_type != "var":
        exit(32)

    ret_val = is_defined(dest_prefix, dest_sufix)
    if ret_val != 0:
        exit(ret_val)

    if arg1_type == "var":
        arg1_type, arg1 = get_symbol(arg1)

    if arg1_type != "int":
        exit(53)

    try:
        symbol_table[dest_prefix][dest_sufix] = ("string", chr(int(arg1)))
    except:
        exit(58)

#executes the stri2int instruction: STRI2INT var symb symb
def stri2int(arguments):
    if len(arguments) != 3:
        exit(32)
    
    dest_type, dest = arguments[0]
    arg1_type, arg1 = arguments[1]
    arg2_type, arg2 = arguments[2]

    dest_prefix, dest_sufix = process_at(dest)
    
    if dest_type != "var":
        exit(32)

    ret_val = is_defined(dest_prefix, dest_sufix)
    if ret_val != 0:
        exit(ret_val)

    if arg1_type == "var":
        arg1_type, arg1 = get_symbol(arg1)

    if arg2_type == "var":
        arg2_type, arg2 = get_symbol(arg2)
    
    if arg1_type != "string" or arg2_type != "int":
        exit(53)
    try:
        symbol_table[dest_prefix][dest_sufix] = ("int", ord(arg1[int(arg2)]))
    except:
        exit(58)

#executes the int2chars instruction: INT2CHARS
def int2chars(arguments):
    if len(arguments) != 0:
        exit(32)
    
    arg1_type, arg1 = var_stack.pop()

    if arg1_type == "var":
        arg1_type, arg1 = get_symbol(arg1)

    if arg1_type != "int":
        exit(53)

    try:
        var_stack.append(("string", chr(int(arg1))))
    except:
        exit(58)

#executes the stri2ints instruction: STRI2INTS
def stri2ints(arguments):
    if len(arguments) != 0:
        exit(32)
    
    arg2_type, arg2 = var_stack.pop()
    arg1_type, arg1 = var_stack.pop()

    if arg1_type == "var":
        arg1_type, arg1 = get_symbol(arg1)

    if arg2_type == "var":
        arg2_type, arg2 = get_symbol(arg2)
    
    if arg1_type != "string" or arg2_type != "int":
        exit(53)

    try:
        var_stack.append(("int", ord(arg1[int(arg2)])))
    except:
        exit(58)

#executes the int2float instruction: INT2FOLAT var symb
def int2float(arguments):
    if len(arguments) != 2:
        exit(32)
    
    dest_type, dest = arguments[0]
    arg1_type, arg1 = arguments[1]

    dest_prefix, dest_sufix = process_at(dest)
    
    if dest_type != "var":
        exit(32)

    ret_val = is_defined(dest_prefix, dest_sufix)
    if ret_val != 0:
        exit(ret_val)

    if arg1_type == "var":
        arg1_type, arg1 = get_symbol(arg1)

    if arg1_type != "int":
        exit(53)

    try:
        symbol_table[dest_prefix][dest_sufix] = ("float", float(int(arg1)).hex())
    except:
        exit(58)

#executes the float2int instruction: FLOAT2INT var symb
def float2int(arguments):
    if len(arguments) != 2:
        exit(32)
    
    dest_type, dest = arguments[0]
    arg1_type, arg1 = arguments[1]

    dest_prefix, dest_sufix = process_at(dest)
    
    if dest_type != "var":
        exit(32)

    ret_val = is_defined(dest_prefix, dest_sufix)
    if ret_val != 0:
        exit(ret_val)

    if arg1_type == "var":
        arg1_type, arg1 = get_symbol(arg1)

    if arg1_type != "float":
        exit(53)

    try:
        symbol_table[dest_prefix][dest_sufix] = ("int", int(float.fromhex(arg1)))
    except:
        exit(58)
    
#executes the read instruction: READ var type
def read(arguments):
    if len(arguments) != 2:
        exit(32)
    
    dest_type, dest = arguments[0]
    arg1_type, arg1 = arguments[1]

    dest_prefix, dest_sufix = process_at(dest)
    
    if dest_type != "var":
        exit(32)
        
    ret_val = is_defined(dest_prefix, dest_sufix)
    if ret_val != 0:
        exit(ret_val)

    if arg1_type != "type":
        exit(53)

    try:
        value = input()
    except:
        value = ""

    if arg1 == "int":
        try:
            symbol_table[dest_prefix][dest_sufix] = ("int", str(int(value)))
        except:
            symbol_table[dest_prefix][dest_sufix] = ("int", 0)
    elif arg1 == "string":
        try:
            symbol_table[dest_prefix][dest_sufix] = ("string", str(value))
        except:
            symbol_table[dest_prefix][dest_sufix] = ("string", "")
    elif arg1 == "bool":
        try:
            if str(value).lower() == "true":
                symbol_table[dest_prefix][dest_sufix] = ("bool", "true")
            else:
                symbol_table[dest_prefix][dest_sufix] = ("bool", "false")
        except:
            symbol_table[dest_prefix][dest_sufix] = ("bool", "false")
    elif arg1 == "float":
        try:
            symbol_table[dest_prefix][dest_sufix] = ("float", float.fromhex(value).hex())
        except:
            symbol_table[dest_prefix][dest_sufix] = ("float", 0)
    elif arg1 == "nil":
        exit(32)
    else:
        exit(57)

def unescape(string):
    for i, sub in enumerate(string.split("\\")):
        if i == 0:
            string = sub
        else:
            string = string + chr(int(sub[0:3])) + sub[3:]
    return string

#executes the write instruction: WRITE symb
def write(arguments):
    if len(arguments) != 1:
        exit(32)
    
    dest_type, dest = arguments[0]
    if dest_type == "var":
        if(get_symbol(dest)) == None:
            exit(56)
        dest_type, dest = get_symbol(dest)
    
    if dest_type == "nil":
        print("", end='')
    else:
        if dest_type == "float":
            try:
                print(str(float.fromhex(dest).hex()), end='')
            except:
                print(float(dest).hex(), end='')
        else:
            print(dest, end='')
    
#executes the concat instruction: CONCAT var symb symb
def concat(arguments):
    if len(arguments) != 3:
        exit(32)
    
    dest_type, dest = arguments[0]
    arg1_type, arg1 = arguments[1]
    arg2_type, arg2 = arguments[2]

    dest_prefix, dest_sufix = process_at(dest)
    
    if dest_type != "var":
        exit(32)
        
    ret_val = is_defined(dest_prefix, dest_sufix)
    if ret_val != 0:
        exit(ret_val)

    if arg1_type == "var":
        arg1_type, arg1 = get_symbol(arg1)

    if arg2_type == "var":
        arg2_type, arg2 = get_symbol(arg2)
    
    if arg1_type != "string" or arg2_type != "string":
        exit(53)

    symbol_table[dest_prefix][dest_sufix] = ("string", arg1 + arg2)

#executes the strlen instruction: STRLEN var symb
def strlen(arguments):
    if len(arguments) != 2:
        exit(32)
    
    dest_type, dest = arguments[0]
    arg1_type, arg1 = arguments[1]

    dest_prefix, dest_sufix = process_at(dest)
    
    if dest_type != "var":
        exit(32)
        
    ret_val = is_defined(dest_prefix, dest_sufix)
    if ret_val != 0:
        exit(ret_val)

    if arg1_type == "var":
        arg1_type, arg1 = get_symbol(arg1)

    if arg1_type != "string":
        exit(53)

    symbol_table[dest_prefix][dest_sufix] = ("int", len(arg1))

#executes the getchar instruction: GETCHAR var symb symb
def getchar(arguments):
    if len(arguments) != 3:
        exit(32)
    
    dest_type, dest = arguments[0]
    arg1_type, arg1 = arguments[1]
    arg2_type, arg2 = arguments[2]

    dest_prefix, dest_sufix = process_at(dest)
    
    if dest_type != "var":
        exit(32)
    
    ret_val = is_defined(dest_prefix, dest_sufix)
    if ret_val != 0:
        exit(ret_val)

    if arg1_type == "var":
        arg1_type, arg1 = get_symbol(arg1)

    if arg2_type == "var":
        arg2_type, arg2 = get_symbol(arg2)
    
    if arg1_type != "string" or arg2_type != "int":
        exit(53)

    try:
        symbol_table[dest_prefix][dest_sufix] = ("string", arg1[int(arg2)])
    except:
        exit(58)

#executes the setchar instruction: SETCHAR var symb symb
def setchar(arguments):
    if len(arguments) != 3:
        exit(32)
    
    dest_type, dest = arguments[0]
    arg1_type, arg1 = arguments[1]
    arg2_type, arg2 = arguments[2]

    dest_prefix, dest_sufix = process_at(dest)
    
    if dest_type != "var":
        exit(32)
        
    ret_val = is_defined(dest_prefix, dest_sufix)
    if ret_val != 0:
        exit(ret_val)

    dest_type, dest = get_symbol(dest)

    if arg1_type == "var":
        arg1_type, arg1 = get_symbol(arg1)

    if arg2_type == "var":
        arg2_type, arg2 = get_symbol(arg2)

    if arg1_type != "int" or arg2_type != "string" or dest_type != "string":
        exit(53)

    if len(arg2) < 1:
        exit(58)

    if int(arg1) >= len(arg2) or int(arg1) < 0:
        exit(58)

    try:
        dest = dest[:int(arg1)] + arg2[0:1] + dest[int(arg1) + 1:]
    except:
        exit(58)

    symbol_table[dest_prefix][dest_sufix] = ("string", dest)

#does nothing, because everything is already done in make_label method
def label(arguments):
    pass

#executes the type instruction: TYPE var symb
def type_instruction(arguments):
    if len(arguments) != 2:
        exit(32)
    
    dest_type, dest = arguments[0]
    arg1_type, arg1 = arguments[1]

    dest_prefix, dest_sufix = process_at(dest)
    
    if dest_type != "var":
        exit(32)
    
    ret_val = is_defined(dest_prefix, dest_sufix)
    if ret_val != 0:
        exit(ret_val)

    if arg1_type == "var":
        prefix, sufix = process_at(arg1)
        ret_val = is_defined(prefix, sufix)
        if ret_val != 0:
            exit(ret_val)
        value = symbol_table[prefix][sufix]
        if value == None:
            arg1_type = ""
        else:
            arg1_type, arg1 = get_symbol(arg1)

    symbol_table[dest_prefix][dest_sufix] = ("string", arg1_type)

#executes the jump instruction: JUMP label
def jump(arguments):
    if len(arguments) != 1:
        exit(32)
    
    var_type, var = arguments[0]
    
    if var_type != "label":
        exit(32)
    
    if var not in symbol_table["label"]:
        exit(52)
    
    global instruction_pointer
    instruction_pointer = symbol_table["label"][var]

#executes the jumpifeq instruction: JUMPIFEQ label symb symb
def jumpifeq(arguments):
    if len(arguments) != 3:
        exit(32)
    
    dest_type, dest = arguments[0]
    arg1_type, arg1 = arguments[1]
    arg2_type, arg2 = arguments[2]

    if dest_type != "label":
        exit(32)

    if dest not in symbol_table["label"]:
        exit(52)

    if arg1_type == "var":
        arg1_type, arg1 = get_symbol(arg1)

    if arg2_type == "var":
        arg2_type, arg2 = get_symbol(arg2)
    
    if arg1_type != arg2_type:
        exit(53)

    if arg1 == arg2:
        global instruction_pointer
        instruction_pointer = symbol_table["label"][dest]

#executes the jumpifneq instruction: JUMPIFNEQ label symb symb
def jumpifneq(arguments):
    global instruction_pointer
    if len(arguments) != 3:
        exit(32)
    
    dest_type, dest = arguments[0]
    arg1_type, arg1 = arguments[1]
    arg2_type, arg2 = arguments[2]

    if dest_type != "label":
        exit(32)

    if dest not in symbol_table["label"]:
        exit(52)

    if arg1_type == "var":
        arg1_type, arg1 = get_symbol(arg1)

    if arg2_type == "var":
        arg2_type, arg2 = get_symbol(arg2)

    if arg1_type != arg2_type:
        exit(53)

    if arg1 != arg2:
        instruction_pointer = symbol_table["label"][dest]

#executes the jumpifeqs instruction: JUMPIFEQS label
def jumpifeqs(arguments):
    if len(arguments) != 1:
        exit(32)
    
    dest_type, dest = arguments[0]
    arg2_type, arg2 = var_stack.pop()
    arg1_type, arg1 = var_stack.pop()

    if dest_type != "label":
        exit(32)

    if dest not in symbol_table["label"]:
        exit(52)

    if arg1_type == "var":
        arg1_type, arg1 = get_symbol(arg1)

    if arg2_type == "var":
        arg2_type, arg2 = get_symbol(arg2)

    if arg1_type != arg2_type:
        exit(53)

    if arg1 == arg2:
        global instruction_pointer
        instruction_pointer = symbol_table["label"][dest]

#executes the jumpifneqs instruction: JUMPIFNEQS label
def jumpifneqs(arguments):
    global instruction_pointer
    if len(arguments) != 1:
        exit(32)
    
    dest_type, dest = arguments[0]
    arg2_type, arg2 = var_stack.pop()
    arg1_type, arg1 = var_stack.pop()

    if dest_type != "label":
        exit(32)

    if dest not in symbol_table["label"]:
        exit(52)

    if arg1_type == "var":
        arg1_type, arg1 = get_symbol(arg1)

    if arg2_type == "var":
        arg2_type, arg2 = get_symbol(arg2)

    if arg1_type != arg2_type:
        exit(53)

    if arg1 != arg2:
        instruction_pointer = symbol_table["label"][dest]

#executes the exit instruction: EXIT symb
def exit_instruction(arguments):
    if len(arguments) != 1:
        exit(32)
    
    var_type, var = arguments[0]
    
    if var_type == "var":
        var_type, var = get_symbol(var)

    if var_type != "int":
        exit(53)

    if int(var) < 0 or int(var) > 49:
        exit(57)

    for arg in sys.argv:
        if arg == "--insts":
            stats_file.write(str(instruction_count) + "\n")
        if arg == "--vars":
            stats_file.write(str(var_count) + "\n")
    if stats_file != None:
        stats_file.close()
    source_file.close()
    input_file.close()

    exit(int(var))

#executes the dprint instruction, which does nothing: DPRINT
def dprint(arguments):
    if len(arguments) != 1:
        exit(32)

#executes the break instruction, which does nothing: BREAK
def break_instruction(arguments):
    pass

def count_variables():
    count = 0
    for var in symbol_table["GF"]:
        if var != None:
            count = count + 1
    if "LF" in symbol_table and symbol_table["LF"] != None:
        for var in symbol_table["LF"]:
            if var != None:
                count = count + 1
    if "TF" in symbol_table and symbol_table["TF"] != None:
        for var in symbol_table["TF"]:
            if var != None:
                count = count + 1
    return count
    
def main():
    global instruction_count
    global var_count
    global source_file
    global input_file
    global stats_file
    source_file, input_file, stats_file = get_inputs()
    init_symbol_table()
    global instruction_pointer
    try:
        program = load_code(source_file)
    except:
        exit(32)
    sys.stdin = input_file
    lang_keywords = ["return", "and", "or", "not", "type", "break", "exit"]
    while instruction_pointer <= len(program):
        instruction = program[str(instruction_pointer)]

        if stats_file != None:
            instruction_count = instruction_count + 1

        if instruction[0] not in lang_keywords and instruction[0] not in globals():
            exit(32)
        if instruction[0] in lang_keywords:
            globals()[instruction[0] + "_instruction"](instruction[1])
        else:
            globals()[instruction[0]](instruction[1])
        instruction_pointer = instruction_pointer + 1
        
        if stats_file != None:
            var_count = max(var_count, count_variables())

    for arg in sys.argv:
        if arg == "--insts":
            stats_file.write(str(instruction_count) + "\n")
        if arg == "--vars":
            stats_file.write(str(var_count) + "\n")
    if stats_file != None:
        stats_file.close()
    source_file.close()
    input_file.close()


if __name__ == "__main__":
    main()
