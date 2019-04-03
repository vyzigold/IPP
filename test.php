<?php

$tests_failed = 0;
$test_results = array();

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
			$test["rc"] = file_get_contents(substr($src, 0, -3) . "rc");
		else
			$test["rc"] = 0;
		if($test["rc"] === false)
			exit(11);
		
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

function arrayToStr($array, $item)
{
	$array .= $item . "\n";
	return $array;
}

function printHTML($tests, $outputs)
{
	$html = file_get_contents("results.tmpl");
	if($html === false)
		exit(11);
	global $tests_failed;
	if($tests_failed == 0)
	{
		$html = str_replace("~~overall~~", "All tests passed", $html);
		$html = str_replace("~~main_display_color~~", "green", $html);
	}
	else
	{
		$html = str_replace("~~overall~~", $tests_failed . " Errors", $html);
		$html = str_replace("~~main_display_color~~", "red", $html);
	}

	$results = "";
	global $test_results;
	for($i = 0; $i < sizeof($tests); $i++)
	{
		$results .= "<h3 class='test_name' onclick='change(". $i .")'";
		if($test_results[$i] == "success")
			$results .= "style='color:green'";
		else
			$results .= "style='color:red'";
		$results .= ">";
		if($test_results[$i] == "success")
			$results .= "&#x2713; ";
		else
			$results .= "&#x26CC; ";
		$results .= $tests[$i]["src"];
		$results .= "</h3>";
		$results .= "<div style='display:none' id='". $i ."'>";
		$results .= "<h4>Source code</h4>";
		$results .= "<div>" . htmlSpecialChars(file_get_contents($tests[$i]["src"])) . "</div>";
		if($tests[$i]["out"] != "" && $outputs[$i]["out"] !== false)
		{
			$results .= "<h4>Expected output</h4>";
			$results .= "<div>" . htmlSpecialChars(file_get_contents($tests[$i]["out"])) . "</div>";
			$results .= "<h4>Output</h4>";
			$results .= "<div>" . htmlSpecialChars($outputs[$i]["out"]) . "</div>";
		}
		$results .= "<h4>Diff</h4>";
		$results .= "<p>" . htmlSpecialChars($outputs[$i]["diff"]) . "</p>";
		$results .= "<h4>Return code</h4>";
		$results .= "<p>Expected: " . $tests[$i]["rc"] . "     Got: " . $outputs[$i]["rc"] . "</p>";
		$results .= "</div>";
		$results .= "<hr/>";
	}
	
	$html = str_replace("~~tests~~", $results, $html);
	//var_dump($outputs);
	echo $html;
}

//@brief prints the help
//@param $argc the argc variable so the function can check if "help" is the only arg.
function help($argc)
{
	if($argc != 2)
		exit(10);
	print 
"Script for testing the parse.php and interpret.py

Usage:
--help                 prints this help
--directory=path       directory to look for tests in
--recursive            tries to search for tests recursively
--parse-script=file    path to parser script
--int-script=file      path to interpreter script
--parse-only           test only parser
--int-only             test only interpreter";
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
{
	$interpret = false;
	if(array_key_exists("int-script", $options) || array_key_exists("int-only", $options))
		exit(10);
}

if(array_key_exists("int-only", $options))
{
	$parse = false;
	if(array_key_exists("parse-script", $options) || array_key_exists("parse-only", $options))
		exit(10);
}

//get all the test filenames
$files = getFiles($directory, $recursive);
$tests = fileSort($files);

//run the tests and diff the results
$outputs = array();

for($i = 0; $i < sizeof($tests); $i++)
{
	$command = "";
	$output = array();
	$output["rc"] = 0;
	if($parse)
	{
		$command = "php7.3 " . $parser . " < '" . $tests[$i]["src"] . "'";
		exec($command, $output["out"], $output["rc"]);
		$output["out"] = substr(array_reduce($output["out"], "arrayToStr"), 0, -1);
	}
	if($parse && $interpret && $output["rc"] == 0)
		$command .= " | ";
	if($interpret && $output["rc"] == 0)
	{
		$in = ($tests[$i]["in"] == "") ? $tests[$i]["src"] : $tests[$i]["in"];
		$command .= "python3.6 " . $interpreter . " --input='" . $in . "'";
	}
	if($interpret && !$parse)
	{
		$command .= " < '" . $tests[$i]["src"] . "'";
	}
	exec($command, $output["out"], $output["rc"]);
	$output["out"] = substr(array_reduce($output["out"], "arrayToStr"), 0, -1);

	//diff or JExamXml the results
	if($interpret)
	{
		if($tests[$i]["out"] === "")
		{
			if($output["out"] != "")
				$output["diff"] = $output["out"];
			else
				$output["diff"] = NULL;
		}
		else
		{
			exec("echo -n '" . $output["out"] . "' | diff '" . $tests[$i]["out"] . "' -", $output["diff"]);
			$output["diff"] = array_reduce($output["diff"], "arrayToStr");
		}
	}

	else
	{
		if($tests[$i]["out"] === "")
		{
			if($output["out"] != "")
				$output["diff"] = $output["out"];
			else
				$output["diff"] = NULL;
		}
		else
		{
			$file = fopen("tmp.out", "w");
			if($file === false)
				exit(12);
			fwrite($file, $output["out"]);
			fclose($file);
			exec("/bin/bash -c \"java -jar /pub/courses/ipp/jexamxml/jexamxml.jar '" . $tests[$i]["out"] . "' tmp.out diffs.xml /D /pub/courses/ipp/jexamxml/options\"", $jout, $jrc);
			unlink("tmp.out");
			if($jrc != 0)
			{
				$output["diff"] = false;
				if(file_exists("diff.xml"))
					$output["diff"] = file_get_contents("diff.xml");
				if($output["diff"] === false)
					$output["diff"] = "failed to compare with jexamxml";
				else
					unlink("diff.xml");
			}
			else
			{
				$output["diff"] = NULL;
			}
		}
	}

	//detect if the test failed
	if($tests[$i]["rc"] != $output["rc"] || ($output["diff"] !== NULL && $output["rc"] == 0))
	{
		$tests_failed++;
		$test_results[] = "fail";
	}
	else
		$test_results[] = "success";
	$outputs[] = $output;
	unset($output);
}
printHTML($tests, $outputs)

?>
