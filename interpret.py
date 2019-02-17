import xml.etree.ElementTree as tree
import argparse
import sys
from collections import Counter

symbol_table = dict()
frame_stack = list()
def get_inputs():
    argparser = argparse.ArgumentParser(description = "Interpret XML made from z IPPcode19")
    argparser.add_argument("--source", nargs=1, help="input XML file")
    argparser.add_argument("--input", nargs=1, help="file with inputs to the program")
    args = argparser.parse_args()
    if args.input == None and args.source == None:
        exit(10);

    try:
        if args.input == None:
            input_file = sys.stdin
        else:
            input_file = open(args.input[0], "r")

        if args.source == None:
            source_file == sys.stdin
        else:
            source_file = open(args.source[0], "r")
    except:
        exit(11)

    return (source_file, input_file)

def init_symbol_table():
    symbol_table["GF"] = None
    symbol_table["label"] = None

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
    for instruction in xml_program:
        if len(instruction.attrib) != 2:
            print(52)
            exit(32)

        order = instruction.attrib["order"]
        opcode = str.lower(instruction.attrib["opcode"])
        if order == None or opcode == "none":
            print(58)
            exit(32)

        if str(int(order) - 1) not in instructions and order != "1":
            print(order)
            missing.append(int(order) - 1)

        if int(order) in missing:
            missing.remove(int(order))

        if order in instructions:
            print(62)
            exit(32)
        
        instructions[order] = list()

        arguments = list()
        try:
            for i in range(len(list(instruction))):
                xml_arg = instruction.find("arg" + str(i + 1))
                if len(xml_arg.attrib) != 1:
                    print(71)
                    exit(32)
                argument = (xml_arg.attrib["type"], xml_arg.text)
                arguments.append(argument)
        except:
            print(76)
            exit(32)

        instructions[order].append(opcode)
        instructions[order].append(arguments)
    
    if(len(missing) > 0):
        print(missing)
        exit(32)
    print(instructions)
    #print(instructions[1])
    return instructions


def main():
    source_file, input_file = get_inputs()
    try:
        load_code(source_file)
    except:
        exit(32)
    #xml = tree.parse(sys.stdin)
    #for child in xml.getroot():
    #    for cc in child:
    #        print(cc)
    source_file.close()
    input_file.close()


if __name__ == "__main__":
    main()
