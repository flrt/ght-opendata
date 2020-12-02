Organisations composant les GHT
===============================

Programme permettant de générer une représentation structure des GHT : [Groupements hospitaliers de territoire](https://solidarites-sante.gouv.fr/professionnels/gerer-un-etablissement-de-sante-medico-social/groupements-hospitaliers-de-territoire/)

Le programme fait suite aux articles : 

- [Informations GHT en Open Data](http://www.opikanoba.org/sante/ght-opendata)
- [Données GHT en open data au format FHIR](http://www.opikanoba.org/sante/ght-fhir)

La source des données provient de :

- la liste des établissements formant les GHT : Source ministère de la santé
- des données complémentaires fournies par la DRESS en open data sur [data.gouv.fr](https://data.gouv.fr)

Le programme `srcdata.py` permet de télécharger ces fichiers automatique :

- via le lien direct sur le fichier XSLX du ministère (qui ne changera pas)
- via l'[API de data.gouv.fr](https://www.data.gouv.fr/fr/apidoc/) pour retrouver la dernière version du fichier finess

# Informations sur le programme de génération des données
L'option `-h` permet de connaitre les différentes options disponibles :

```
➜  ght-opendata git:(master) python generator.py -h
usage: generator.py [-h] [--code CODE] [--list] [--dgosfile DGOSFILE]
                    [--finessfile FINESSFILE] [--outputdir OUTPUTDIR]

optional arguments:
  -h, --help            show this help message and exit
  --code CODE           code GHT en particulier : CODE (voir --list pour avoir
                        la liste). La valeur all permet de générer tous les
                        codes
  --list                Liste les codes GHT
  --dgosfile DGOSFILE   Fichier du ministère, donnant la liste des GHT
  --finessfile FINESSFILE
                        Fichier Finess des établissements
  --outputdir OUTPUTDIR
                        Repertoire de destination des fichiers générés

```

## Liste des codes disponibles
Les codes disponibles sont issus du fichier du ministère. Pour en connaitre la liste, il suffit de faire 

```
➜  ght-opendata git:(master) python generator.py --list
  MAR-01 : centre sud
  ARA-01 : territoire d'auvergne
  ARA-02 : Savoie Belley
  ARA-03 : Bresse Haut-Bugey
  ARA-04 : Cantal
  ARA-05 : Alpes Dauphiné
.../...
```

## Génération des fichiers FHIR pour 1 code en particulier
Il suffit de passer le code en paramètre 


```
➜  ght-opendata git:(master) python generator.py --code PACA-04 --outputdir output
Generation GHT PACA-04
```

# Validation des fichiers FHIR XML produits
Le programme `validate_xml.sh` permet de valider chaque document XML produit par rapport à son schéma XSD.
Les schémas XSD sont disponibles sur le site [HL7 FHIR, rubrique formats](https://www.hl7.org/fhir/xml.html).

En spécifiant la localisation du schéma XSD et le répertoire qui contient les fichiers XML, le programme va analyser chaque document fournir un statut de validation.

- arg1 : fichier XSD
- arg2 : répertoire contenant les XML

```
sh validate_xml.sh /Users/fred/dev/xsd/fhir-18sept/fhir-single.xsd output
output/ARA-01.xml validates
output/ARA-02.xml validates
output/ARA-03.xml validates
.../...
output/PDL-03.xml validates
output/PDL-04.xml validates
output/PDL-05.xml validates
Total 135 : OK=135 / KO=0

```

La validation utilise le programme [xmllint](http://xmlsoft.org/xmllint.html).


## Utilisation du container docker
Il suffit de constuire le container

```
$ docker build -t ght .
```

Créer un répertoire 'files' qui contient les fichiers téléchargés
```
mkdir files
``` 

Puis d'exécuter un bash
```
docker run -it -v "$PWD":/opt ght /bin/bash
```

Et de lancer le programme de génération ou de téléchargement des données sources
```
$ # Telechargement des donnnees

$ python srcdata.py 
Telechargement : https://static.data.gouv.fr/resources/finess-extraction-du-fichier-des-etablissements/20181011-114801/etalab-cs1100507-stock-20181011-0450.csv -> files/etalab-cs1100507-stock-20181011-0450.csv
Telechargement : https://solidarites-sante.gouv.fr/IMG/xlsx/dgos_ght_liste_2017_10_31.xlsx -> files/dgos_ght_liste_2017_10_31.xlsx

$ # Generation du bundle pour le GHT PDL-04

$ python generator.py --code PDL-04 
Generation GHT PDL-04
```

La validation peut se faire avec les fichiers XSD de FHIR.
Les schemas sont disponibles sur la [page Downloads](https://www.hl7.org/fhir/downloads.html) et le zip contenant les schémas XSD est [fhir-all-xsd.zip](https://www.hl7.org/fhir/fhir-all-xsd.zip) qu'il suffit de dézipper dans le répertoire `xsd` par exemple. Ensuite, en donnant le nom du fichier XSD global et le répertoire des fichiers générés, la validation peut se faire :

```
$ # Validation des documents XML produits

$ ./validate_xml.sh xsd/fhir-all-xsd/fhir-all.xsd output/
output//PDL-04.xml validates
Total 1 : OK=1 / KO=0

```