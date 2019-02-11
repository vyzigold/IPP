<?php

//class that represents tokens
class Token
{
	//all the possible instructions.
	//Will increment every time the instruction gets used,
	//so I could have usage statistics for each instructions separately,
	//which I don't need, but I think it's cool
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
	private $comments = 0;

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
		$this->nextToken();
	}
	
	public function getToken()
	{
		return $this->token_string;
	}

	public function getTokenType()
	{
		return $this->token_type;
	}

	//method that reads and lexicaly processes next token from the source code
	public function nextToken()
	{
		//this processec new lines
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
						break;
				}
				$this->token_string = $this->token_string . $character;
			}
			if($this->token_string != "")
				$this->tokenCheck();
			$this->last_char = $character;
		} while($this->token_string == "");
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

	//method which checks and assigns token type
	private function tokenCheck()
	{
		if($this->token_type == "new_line")
		{
			if($this->isInstruction())
			{
				$this->token_type = "instruction";
			}
			else
			{
				$this->token_type = "lexical_error";
				echo "150";
				exit(22);
			}
		}
		else if($position = strpos($this->token_string, "@"))
		{
			$frames = array("GF", "LF", "TF");
			$var_types = array("string", "int", "bool", "nil");
			$prefix = substr($this->token_string, 0, $position);
			$sufix = substr($this->token_string, $position + 1);

			var_dump($prefix);
			var_dump($sufix);
			if(in_array($prefix, $frames) && $this->isVariable($sufix))
			{
				$this->token_type = "variable";
			}
			else if(in_array($prefix, $var_types))
			{
				//php magic - calls method according to prefix
				//eg. $this->isBool();
				echo "is" . ucfirst($prefix);
				if($this->{"is" . ucfirst($prefix)}($sufix))
				{
					$this->token_type = "constant";
				}
				else
				{
					$this->token_type = "lexical_error";
					echo "179";
					exit(22);
				}
			}
			else
			{
				$this->token_type = "lexical_error";
				echo "186";
				exit(22);
			}
		}
		else
			$this->token_type = "other";
	}

	//method which checkes if the token is correctly writen instruction
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

	//mathod which checks if the token is a correctly writen variable
	private function isVariable($name)
	{
		//begins with letter or one of _$&%*!?- and continues
		//with letters or _$&%*!?- or numbers
		if(preg_match('/^[A-Za-z_$&%*!?-][A-Za-z0-9_$&%*!?-]*$/', $name) == 1)
			return true;
		else
			return false;
	}

	private function isBool($value)
	{
		if($value == "true" || $value == "false")
			return true;
		else
			return false;
	}

	private function isNul($value)
	{
		if($value == "nul")
			return true;
		else
			return false;
	}

	private function isString($value)
	{
		echo "inhere";
		//check escape sequences
		for($i = 0; ($pos = strpos("\\", substr($value, $i))) !== false; $i = $pos + 4)
		{
			if(!preg_match("/^[0-9]{3}$/", substr($value, $pos + 1, 3)))
				return false;
		}
		return true;
	}

	private function isInt($value)
	{
		if(preg_match('/^[0-9]*$/', $value) == 1)
			return true;
		else
			return false;
	}
}

$token = new Token();

while($token->getTokenType() != "EOF")
{
	echo $token->getToken() . "    " . $token->getTokenType() . "\n";
	$token->nextToken();
}

?>
