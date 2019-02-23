<?php

function getFiles($path, $recursive)
{
	$files = array();
	$iterator = new RecursiveDirectoryIterator($path);

	foreach($iterator as $file)
	{
		if($file->getFilename() == "." or $file->getFilename() == "..")
			continue;
		if($file->isDir())
		{
			if($recursive == false)
				continue;
			$files = array_merge($files, getFiles($file->getPathname(), $recursive));
		}
		else
			array_push($files, $file->getPathname());
	}
	return $files;
}

function fileSort($files)
{
	$srcs = array();

	foreach($files as $file)
	{
		if(substr($file, -4, 4) == ".src")
			$srcs[] = $file;
	}

	$tests = array();

	foreach($srcs as $src)
	{
		$test = array();
		$test["src"] = $src;

		if(in_array(substr($src, 0, -3) . "rc", $files))
			$test["rc"] = substr($src, 0, -3) . "rc";
		else
			$test["rc"] = "";
		
		if(in_array(substr($src, 0, -3) . "in", $files))
			$test["in"] = substr($src, 0, -3) . "in";
		else
			$test["in"] = "";

		if(in_array(substr($src, 0, -3) . "out", $files))
			$test["out"] = substr($src, 0, -3) . "out";
		else
			$test["out"] = "";
		$tests[] = $test;
	}
	return $tests;
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

//all the possible command line arguments
$possible_args = array(
	"directory::",
	"help",
	"recursive",
	"parse-script::",
	"int-script::",
	"parse-only",
	"int-only"
);

//parse command line args
try
{
	$options = getopt("", $possible_args);
	if($options === false)
		exit(10);
}
catch(Exception $e)
{
	exit(10);
}

var_dump($options);
if(array_key_exists("help", $options))
	help($argc); 
$directory = ".";
if(array_key_exists("directory", $options))
{
	if($options["directory"] === false)
		exit(10);
	$directory = $options["directory"];
}

$recursive = false;
if(array_key_exists("recursive", $options))
	$recursive = true;

$parser = "./parse.php";
if(array_key_exists("parse-script", $options))
{
	if($options["parse-script"] === false)
		exit(10);
	$parser = $options["parse-script"];
}

$interpreter = "./interpret.py";
if(array_key_exists("int-script", $options))
{
	if($options["int-script"] === false)
		exit(10);
	$interpreter = $options["int-script"];
}

$parse = true;
$interpret = true;
if(array_key_exists("parse-only", $options))
	$interpret = false;

if(array_key_exists("int-only", $options))
	$parse = false;

$files = getFiles($directory, $recursive);
$tests = fileSort($files);

for($i = 0; $i < sizeof($tests); $i++)
{
	$command = "";
	if($parse)
		$command = "php7.3 " . $parser . " < " . $tests[$i]["src"];
	if($parse && $interpret)
		$command .= " | ";
	if($interpret)
	{
		$in = ($tests[$i]["in"] == "") ? $tests[$i]["src"] : $tests[$i]["in"];
		$command .= "python3.6 " . $interpreter . " --input=" . $in;
	}
	if($interpret && !$parse)
	{
		$command .= " < " . $tests[$i]["src"];
	}
	echo $command . "\n";
	exec($command, $output, $status);
	echo $output[0] . "\n";
	echo $status . "\n";

}

var_dump($tests);
?>
