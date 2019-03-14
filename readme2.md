Implementační dokumentace k 1. úloze do IPP 2018/2019
Jméno a příjmení: Jaromír Wysoglad
Login: xwysog00

Implementace je rozdělena do modulů: scan.php a parse.php

# interpret.py
Interpret jako první volá funkci `get_inputs`, která pomocí argparse zpracuje argumenty programu a pokud nebyl zadán argument --help vrátí soubor s programem a soubor s uživatelskými vstupy. Dále se pokračuje funkcí `load_code`, která pomocí xml.etree.ElementTree rozparsuje a zkontroluje vstupní XML a vrátí ho jako: `{'order': ['opcode', [arg1, arg2, ...]], ...}`, kde arg znamená `(type, value)`. Díky použití slovníku s klíčem `order` se provede seřazení instrukcí, s tím že kontrola případných chybějících instrukcí se provádí zkontrolováním přítomnosti instrukce s pořadím `order - 1` ve slovníku a pokud chybí, tak se zapíše do seznamu chybějících instrukcí, ze ketrého se při jejím načtení vymaže. Pokud je seznam chybějících instrukcí prázdný, jsou přítomny všechny instrukce. Při tomto načítání se také zpracovávají labely, které se zapisují do tabulky symbolů, která má podobu: `{'GF': {'nazev': 'hodnota'}, 'label': {'nazev': pozice}}`, klíče LF a TF přibívají a mizí podle stavu programu. Po načtení se v cyklu začne program provádět. Pro každou instrukci je napsána funkce, která provádí kontrolu argumentů instrukce a následně provádí samotnou instrukci.

## Rozšíření
Implementovány jsou všechna rozšíření. FLOAT je implementován pouhým přidáním nového datového typu k funkcím, které kontrolují datové typy a malým upravením aritmetickách funkí tak, aby podporovaly i tento typ. STACK je implementován pomocí pouhého nakopírování funkcí, které pracují s parametry a jejich přizpůsobení pro práci se stackem. STATI vyžadoval přidání dalších parametrů do funkce `get_inputs()`, která zpracovává vstupní argumenty, dále bylo potřeba přidat počítadla provedených instrukcí a proměnných a funkci, která počítadlo proměnných aktualizuje, pokud je proměnných více.

# test.php
Jako přvní se provádí kontrola argumentů programu. Poté se volá funkce `$files = getFiles($path, $recursive)`, která prochází složku zadanou parametrem `$path`, což je buď aktuální adresář, nebo adresář zadaný argumentem `--directory`. Parametr `$recurive` je `true`, pokud je zadán argument programu `--recursive`. Funkce vrací podle parametru `$recursive` pole cest ke všem souborům zadané složky, nebo ke všem souborům v celém adresářovém stromu počínaje zadanou složkou. Toto pole se následně předá funkci `fileSort($files)`, která v souborech vyhledá všechny soubory se zdrojovým kódem (přípona .src) a pro každý takto nalezený test sestaví asociativní pole s indexy `src, rc, in, out` a jehož hodnotami jsou cesty k odpovídajícím souborům testu, nebo prázdný řetězec v případě neexistence souboru. Každé takové pole je nakonec přidáno do pole všech testů a to je pak z funkce vráceno.
Každý test je podle zadaných vstupních parametrů proveden a jeho výstupy jsou porovnány pomocí diff, nebo jexamxml a výstupy porovnávání jsou uloženy do pole výstupů. Pole výstupů s polem cest k souborům testů je poté předáno do funkce `printHTML()`, která načte soubor results.tmpl, což je html šablona s jednoduchým CSS a javascriptem. A do této šablony pro každý test vloží: kód testu, výstup testu, předpokládaný výstup, návratový kód, předpokládaný návratový kód a v případě existence i výstup z diff (při neúspěchu). Všechny výstupy jsou skryty pomocí javascriptu a zobrazují se až po kliknutí na daný test.

## Testy
V adresáři tests se nachází několik mnou implementovaných testů, dálší testy jsem čerpal ze sdíleného repozitáře https://github.com/BlueCircleButton/IPP-test.php 

## Rozšíření
Rozšíření files jsem se rozhodl neimplementovat, protože oproti ostatním rozšířením mi přišlo jako zbytečně moc práce za pouze jeden bod.
