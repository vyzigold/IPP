Implementační dokumentace k 1. úloze do IPP 2018/2019
Jméno a příjmení: Jaromír Wysoglad
Login: xwysog00

Implementace je rozdělena do modulů: scan.php a parse.php

# scan.php
Obsahuje pouze třídu LexicalAnalyser.

## LexicalAnalyser
Třída pro načtení programu v IPPcode19 a jeho převádění na tokeny. Důležitými metodami jsou `getToken()` pro získání tokenu jako řetězce, `getTokenType()` pro získání typu tokenu, `getSufix()` pro získání části tokenu za '@' a `getPrefix()` pro získání části před '@'.
Metoda `nextToken()`, načítá znaky programu a načtený řetězec předává metodě `tokenCheck()`. Ta rozhoduje o typu a správnosti tokenu. Pokud byl předchozí token nový řádek, nový token musí být instrukce a provede se kontrola, zda v asociativním poli, jehož klíči jsou názvy instrukcí, existuje klíč rovný kontrolovanému řetězci. Pokud ne, je program ukončen s návratovým kódem 22. Pokud předchozím tokenem nebyl nový řádek, tak je řetězec argumentem. Pokud řetězec neobsahuje znak '@', musí to být label. Pokud obsahuje '@', tak se rozdělí na `prefix` a `sufix` (část před a za '@'). Pokud je `prefix` označením rámce, řetězec představuje proměnnou a provede se kontrola regulárním výrazem. Pokud prefix obsahuje datový typ tak se podle něj pomocí `$this->{"is" . ucfirst($prefix)}($sufix)` zavolá funkce, která provede kontrolu sufixu regulárním výrazem. Při chybě se script ukončí s návratovým kódem 23.

# parse.php
Při spuštění se provede kontrola parametrů a následně, pokud není zadán parametr `--help`, se volá funkce `XMLize()`.

## XMLize
Funkce v cyklu pomocí instance třídy `LexicalAnalyser` načítá instrukce, kontroluje jejich argumenty a při jejich správnosti pomocí DOMDocument tvoří a tiskne XML.

# Rozšíření
Implementace rozšíření STATP se nachází v modulu scan.php. Pro počítání výskytů instrukcí slouží asociativní pole, jehož klíči jsou instrukce a hodnotami jsou počty výskytů instrukce. Komentáře jsou počítány zvlášť
