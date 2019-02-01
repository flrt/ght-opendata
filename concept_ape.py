#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
    Construction du Code System APE
    en FHIR (https://www.hl7.org/fhir/codesystem.html).

    Fichier source : https://insee.fr/fr/information/2120875

"""

__author__ = "Frederic Laurent"
__version__ = "1.0"
__copyright__ = "Copyright 2018, Frederic Laurent"
__license__ = "MIT"

import os
import os.path
import argparse
import pandas
import json
import lxml.etree
from generator import *

class APE:
    APE_KEYS = ["ligne", "code", "lib", "lib65", "lib40"]

    def __init__(self, **kwargs):
        for attribute, value in kwargs.items():
            setattr(self, attribute, value)

    def load(self):
        xl = pandas.ExcelFile(self.filename, dtype=str)
        self.df_ape = xl.parse("NAF rév. 2")
        self.df_ape.columns = APE.APE_KEYS

    def code_system(self):
        """
        Definition code NAF
        5 niveaux
        https://www.insee.fr/fr/metadonnees/definition/c1078
        """

        cs = dict(
            resourceType="CodeSystem",
            id="APE",
            text=dict(
                status="generated",
                div=f"""<div xmlns=\"http://www.w3.org/1999/xhtml\">CODE APE</div>""",
            ),
            identifier=[dict(use="official", system="urn:fr-gouv-sante:ght", value=0)],
            version=self.version,
            name=f"Code APE",
            status="draft",
            experimental=True,
            date=self.date,
            publisher="FLT",
            caseSensitive=True,
            content="complete",
            concept=[],
        )
        for index, elem in self.df_ape[self.df_ape["code"].str.len() == 6].iterrows():
            cs["concept"].append({"code": elem["code"], "display": elem["lib"]})

        return cs

    def cs_toxml(self, cs):
        resxml = xmlelt(None, cs['resourceType'], {"xmlns": "http://hl7.org/fhir"})
        resxml.append(lxml.etree.Comment(f"Concept count = {len(cs['concept'])}"))

        for concept in cs["concept"]:
            conc = xmlelt(resxml, "concept")
            xmlelt(conc, "code", {'value': concept["code"]})
            xmlelt(conc, "display", {'value': concept["display"]})
        
        return resxml

def main():
    """
        Programme principal

        - parse les arguments
        - lance les traitements
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("--file", help="Fichier des codes APE")
    parser.add_argument("--version", help="Version de la nomenclature (defaut=NAF rév. 2)", default=u"NAF rév. 2")
    parser.add_argument("--date", help="Date de la version de la nomenclature (defaut=2008-01-01)", default="2008-01-01")


    parser.add_argument(
        "--outputdir",
        help="Repertoire de destination des fichiers générés",
        default="output",
    )
    args = parser.parse_args()
    if args.file:
        if not os.path.exists(args.outputdir):
            print(f"Creation de {args.outputdir}")
            os.makedirs(os.path.abspath(args.outputdir))

        ape = APE(filename=args.file, version=args.version, date=args.date)
        ape.load()
        cs = ape.code_system()
        with open(os.path.join(args.outputdir, "cs_ape.json"), "w") as fout:
            fout.write(json.dumps(cs, indent=2))
        with open(os.path.join(args.outputdir, "cs_ape.xml"), "w") as fout:
            fout.write(xml2text(ape.cs_toxml(cs)))


if __name__ == "__main__":
    main()
