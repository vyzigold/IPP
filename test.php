<?php

function getFiles($path)
{
	$files = array();
	$iterator = new RecursiveDirectoryIterator($path);

	foreach($iterator as $file)
	{
		if($file->getFilename() == "." or $file->getFilename() == "..")
			continue;
		if($file->isDir())
			$files = array_merge($files, getFiles($file->getPathname()));
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

	}
}

var_dump(getFiles("/home/jarda/gits/IPP"));

?>
