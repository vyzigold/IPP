<?php

//class that represents the lexical analysis
class LexicalAnalyser
{
	//all the possible instructions.
	//Will increment every time the instruction gets used,
	//so I could have usage statistics for each instructions separately,
	//which I don't need, but I think it's cool so why not
	private $instructions = array(
		"move" => 0,
		"createframe" => 0,
		"pushframe" => 0,
		"popframe" => 0,
		"defvar" => 0,
		"call" => 0,
		"return" => 0,
		"pushs" => 0,
		"pops" => 0,
		"add" => 0,
		"sub" => 0,
		"mul" => 0,
		"idiv" => 0,
		"lt" => 0,
		"gt" => 0,
		"eq" => 0,
		"and" => 0,
		"or" => 0,
		"not" => 0,
		"int2char" => 0,
		"stri2int" => 0,
		"read" => 0,
		"write" => 0,
		"concat" => 0,
		"strlen" => 0,
		"getchar" => 0,
		"setchar" => 0,
		"type" => 0,
		"label" => 0,
		"jump" => 0,
		"jumpifeq" => 0,
		"jumpifneq" => 0,
		"exit" => 0,
		"dprint" => 0,
		"break" => 0,
	);
	//the comments counter for the extension
	private $comments;

	//the raw string exactly like in the source code
	private $token_string;

	//possible types:
	//new_line
	//EOF
	//instruction
	//variable
	//constant
	//label
	//lexical_error
	private $token_type;

	//last char read from stdin, the char doesn't have to be part of token_string
	//for example \n gets saved here, but not to the token_string
	private $last_char;

	public function __construct()
	{
		$this->last_char = "";
		$this->token_type = "";
		$this->token_string = "";
		$this->comments = 0;
		$this->nextToken();
	}
	
	//@return token as a string
	public function getToken()
	{
		return htmlSpecialChars($this->token_string);
	}

	//@return type of token
	public function getTokenType()
	{
		return $this->token_type;
	}

	//@brief reads and lexicaly processes next token from the source code
	public function nextToken()
	{
		//this processes new lines
		if($this->last_char == "\n")
		{
			$this->token_string = "\n";
			$this->token_type = "new_line";
			$this->last_char = "";
			return;
		}

		$this->token_string = "";
		do
		{
			while(!ctype_space($character = fgetc(STDIN)))
			{
				//EOF check
				if($character === false)
				{
					if($this->token_string != "")
						break;
					$this->token_type = "EOF";
					$this->token_string = "EOF";
					return;
				}
				//comment check
				if($character == "#")
				{
					$this->processComment();
					if($this->token_string == "")
					{
						$this->token_string = "\n";
						$this->token_type = "new_line";
						return;
					}
					else
					{
						$this->last_char = "\n";
						break;
					}
				}
				$this->token_string = $this->token_string . $character;
			}
			if($this->token_string != "")
				$this->tokenCheck();
			if($character != "#")
				$this->last_char = $character;
		} while($this->token_string == "" && $character != "\n");

		if($this->token_string == "")
		{
			$this->token_string = "\n";
			$this->token_type = "new_line";
			$this->last_char = "";
			return;
		}
	}

	//@return prefix of constant (part before @)
	public function getPrefix()
	{
		$position = strpos($this->token_string, "@");
		return substr($this->token_string, 0, $position);
	}

	//@return sufix of constant (part after @)
	public function getSufix()
	{
		$position = strpos($this->token_string, "@");
		return substr($this->token_string, $position + 1);
	}

	//@brief prints stats for the extension
	//@param $filename name of file to print to
	//@param $options comand line options
	public function printStats($filename, $options)
	{
		$printed = false;
		$file = fopen($filename, "w");
		unset($options["stats"]);
		if($file === false)
			exit(12);
		foreach($options as $key => $option)
		{
			//php magic, calls method according to option
			//eg. printLoc($file);
			$this->{"print" . ucfirst($key)}($file);
			$printed = true;
		}
		fclose($file);
		if($printed == false)
			exit(10);
	}

	//@brief print LOC stats
	//@param $file file to printe the stats to
	private function printLoc($file)
	{
		$count = 0;
		foreach($this->instructions as $instruction)
			$count += $instruction;
		fprintf($file, $count . "\n");
	}

	//@brief print Comments stats
	//@param $file file to printe the stats to
	private function printComments($file)
	{
		fprintf($file, $this->comments . "\n");
	}

	//@brief print Labels stats
	//@param $file file to printe the stats to
	private function printLabels($file)
	{
		fprintf($file, $this->instructions["label"] . "\n");
	}

	//@brief print Jumps stats
	//@param $file file to printe the stats to
	private function printJumps($file)
	{
		$jumps = $this->instructions["jump"];
		$jumps += $this->instructions["jumpifeq"];
		$jumps += $this->instructions["jumpifneq"];
		fprintf($file, $jumps . "\n");
	}

	//method for "eating" the comment, the output will be new line token,
	//which is harmless for the rest of this script
	private function processComment()
	{
		$character = "#";	
		while($character != "\n" && $character !== false)
			$character = fgetc(STDIN);
		$this->comments++;
		$this->last_char = "\n";
	}

	//@brief method which checks and assigns token type
	private function tokenCheck()
	{
		if($this->token_type == "new_line") //after \n has to be instruction
		{
			if($this->isInstruction())
			{
				$this->token_type = "instruction";
			}
			else
			{
				$this->token_type = "lexical_error";
				exit(22);
			}
		}
		else if(strpos($this->token_string, "@") !== false)
		{
			$frames = array("GF", "LF", "TF");
			$var_types = array("string", "int", "bool", "nil");
			$prefix = $this->getPrefix();
			$sufix = $this->getSufix();
			if(in_array($prefix, $frames) && $this->isVariable($sufix))
			{
				$this->token_type = "variable";
			}
			else if(in_array($prefix, $var_types))
			{
				//php magic - calls method according to prefix
				//eg. $this->isBool();
				if($this->{"is" . ucfirst($prefix)}($sufix)!== false)
				{
					$this->token_type = "constant";
				}
				else
				{
					$this->token_type = "lexical_error";
					exit(23);
				}
			}
			else
			{
				$this->token_type = "lexical_error";
				exit(23);
			}
		}
		else
			$this->token_type = "label";
	}

	//@brief method which checkes if the token is correctly writen instruction
	//@return true when the token is corect and false otherwise
	private function isInstruction()
	{
		if(array_key_exists(strtolower($this->token_string), $this->instructions))
		{
			$this->instructions[strtolower($this->token_string)]++;
			return true;
		}
		else
		{
			return false;
		}
	}

	//@brief method which checks if the token is a correctly writen variable
	//@return true when the token is corect and false otherwise
	private function isVariable($name)
	{
		//begins with letter or one of _$&%*!?- and continues
		//with letters or _$&%*!?- or numbers
		if(preg_match('/^[A-Za-z_$&%*!?-][A-Za-z0-9_$&%*!?-]*$/', $name) == 1)
			return true;
		else
			return false;
	}

	//@brief method which checks if the token is a correctly written bool
	//@return true when the token is corect and false otherwise
	private function isBool($value)
	{
		if($value == "true" || $value == "false")
			return true;
		else
			return false;
	}

	//@brief method which checks if token can be a Nil
	//@return true when the token is corect and false otherwise
	private function isNil($value)
	{
		if($value == "nil")
			return true;
		else
			return false;
	}

	//@brief method which checks if the token is a correct string
	//@return true when the token is corect and false otherwise
	private function isString($value)
	{
		//check escape sequences
		for($i = 0; ($pos = strpos(substr($value, $i), '\\')) !== false; $i = $pos + 4)
		{
			$pos += $i;
			if(!preg_match("/^[0-9]{3}$/", substr($value, $pos + 1, 3)))
				return false;
		}

		return true;
	}

	//@brief method which checks if the really is an integer
	//@return true when the token is corect and false otherwise
	private function isInt($value)
	{
		if(preg_match('/^[\+\-]?[0-9]*$/', $value) == 1)
			return true;
		else
			return false;
	}
}

?>
