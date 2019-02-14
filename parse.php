<?php

include 'scan.php';

//@brief checks if the token can be 'type'
//@param $token_type token type returned by lexical analysis
//@param $token token as string returned by lexical analysis
//@return true if the token can be type, false otherwise
function isType($token_type, $token)
{
	return $token_type == "label" &&
		($token == "string" || $token == "int" || $token == "bool");
}

//@brief checks if the token can be 'symbol'
//@param $token_type token type returned by lexical analysis
//@return true if the token can be symbol, false otherwise
function isSymbol($token_type)
{
	return $token_type == "variable" || $token_type == "constant";
}

//@brief Takes IPPcode19 from stdin and outputs it as XML to stdout
//@param $scanner instance of Lexical analyser
function XMLize($scanner)
{
	//all of the instructions with all the operands they need
	$instruction_operands = array(
		"move" => array("variable", "symbol"),
		"createframe" => array(),
		"pushframe" => array(),
		"popframe" => array(),
		"defvar" => array("variable"),
		"call" => array("label"),
		"return" => array(),
		"pushs" => array("symbol"),
		"pops" => array("variable"),
		"add" => array("variable", "symbol", "symbol"),
		"sub" => array("variable", "symbol", "symbol"),
		"mul" => array("variable", "symbol", "symbol"),
		"idiv" => array("variable", "symbol", "symbol"),
		"lt" => array("variable", "symbol", "symbol"),
		"gt" => array("variable", "symbol", "symbol"),
		"eq" => array("variable", "symbol", "symbol"),
		"and" => array("variable", "symbol", "symbol"),
		"or" => array("variable", "symbol", "symbol"),
		"not" => array("variable", "symbol", "symbol"),
		"int2char" => array("variable", "symbol"),
		"stri2int" => array("variable", "symbol", "symbol"),
		"read" => array("variable", "type"),
		"write" => array("symbol"),
		"concat" => array("variable", "symbol", "symbol"),
		"strlen" => array("variable", "symbol"),
		"getchar" => array("variable", "symbol", "symbol"),
		"setchar" => array("variable", "symbol", "symbol"),
		"type" => array("variable", "symbol"),
		"label" => array("label"),
		"jump" => array("label"),
		"jumpifeq" => array("label", "symbol", "symbol"),
		"jumpifneq" => array("label", "symbol", "symbol"),
		"exit" => array("symbol"),
		"dprint" => array("symbol"),
		"break" => array());
	$xml = new DOMDocument("1.0", "UTF-8");
	$order = 1;

	//check the first line for the .IPPcode19 header
	if($scanner->getToken() != ".IPPcode19")
		exit(21);

	//remove all unnecessary preceding empty lines
	do
	{
		$scanner->nextToken();
	} while($scanner->getTokenType() == "new_line");

	while($scanner->getTokenType() != "EOF")
	{
		if($scanner->getTokenType() != "instruction")
		{
			exit(23);
		}

		//create the instruction element
		$xml_instruction = $xml->createElement("instruction");
		$xml_instruction->setAttribute("order", $order);
		$xml_instruction->setAttribute("opcode", strtoupper($scanner->getToken()));

		$instruction = strtolower($scanner->getToken());
		$arg_count = 1;

		//check the instruction arguments - syntactic analysis
		foreach($instruction_operands[$instruction] as $expecting)
		{
			$scanner->nextToken();
			$xml_argument = $xml->createElement("arg" . $arg_count);
			$arg_count++;

			if($expecting == "type" && 
				isType($scanner->getTokenType(), $scanner->getToken()))
			{
				$xml_argument->setAttribute("type", "type");
				$xml_argument->nodeValue = $scanner->getToken();
				$xml_instruction->appendChild($xml_argument);
				continue;
			}
			if($expecting == "variable" && $scanner->getTokenType() == "variable")
			{
				$xml_argument->setAttribute("type", "var");
				$xml_argument->nodeValue = $scanner->getToken();
				$xml_instruction->appendChild($xml_argument);
				continue;
			}
			if($expecting == "label" && $scanner->getTokenType() == "label")
			{
				$xml_argument->setAttribute("type", "label");
				$xml_argument->nodeValue = $scanner->getToken();
				$xml_instruction->appendChild($xml_argument);
				continue;
			}
			if($expecting == "symbol" && isSymbol($scanner->getTokenType()))
			{
				if($scanner->getTokenType() == "variable")
					$xml_argument->setAttribute("type", "var");
				else
					$xml_argument->setAttribute("type", $scanner->getPrefix());
				$xml_argument->nodeValue = $scanner->getSufix();
				$xml_instruction->appendChild($xml_argument);
				continue;
			}
			exit(23);
		}
		$xml->appendChild($xml_instruction);
		unset($expecting);
		do
		{
			$scanner->nextToken();
		} while($scanner->getTokenType() == "new_line");
		$order++;
	}
	print $xml->saveXML();
}

//@brief prints the help
//@param $argc the argc variable so the function can check if "help" is the only arg.
function help($argc)
{
	if($argc != 2)
		exit(10);
	print "Script typu filtr nacte ze standardniho vstup zdrojovy kod v IPPcode19, ".
		"zkontroluje lexikalni a syntaktickou spravnost kodu a vypise na " .
		"na standardni vystup XML reprezentaci programu dle specifikace.\n";
	exit(0);
}

$scanner = new LexicalAnalyser();

//all the possible command line arguments
$possible_args = array(
	"stats:",
	"loc",
	"comments",
	"labels",
	"jumps",
	"help"
);

//parse command line args
$options = getopt("", $possible_args);
if($options === false)
	exit(10);

if(array_key_exists("help", $options))
	help($argc);

//checks if a filename was given along with the stats option
if(in_array("--stats", $argv) && !array_key_exists("stats", $options))
	exit(10); //missing file

XMLize($scanner);

if(array_key_exists("stats", $options))
{
	$scanner->printStats($options["stats"], $options);
}
?>
