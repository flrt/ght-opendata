#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

    Programme de generation de resources FHIR/JSON/XML a partir des donnees
    - du fichier contenant la liste des GHT, disponible sur le site du ministère de la santé
    - de l'extraction des finess, publiée sur le site data.gouv.fr

    L'execution de python generator.py -h permet d'avoir des informations sur les parametres
    attendus ou facultatifs


Contenu du fichier http://solidarites-sante.gouv.fr/IMG/xlsx/dgos_ght_liste_2017_10_31.xlsx

 REGION                     : Nouvelle Aquitaine
 DENOMINATION GHT           : Limousin
 CODE GHT                   : NA-04
 FINESS                     : 870000015
 CATEGORIE                  : C.H.R.
 DENOMINATION ETABLISSEMENT : C H U DE LIMOGES
 COMMUNE                    : Limoges
 CODE POSTAL                : 87042


region, ght_libelle, ght_code, finess, categorie, etablissement, commune, code_postal
"""
__author__ = "Frederic Laurent"
__version__ = "1.0"
__copyright__ = "Copyright 2018, Frederic Laurent"
__license__ = "MIT"


import argparse
import os.path
import os

import pandas
import numpy as np
import math
import json
import io
import re
import codecs
from pyproj import Proj, transform
import lxml.etree
from lxml.etree import Element, SubElement

import srcdata


def xmlelt(parent, tag, attrs=None):
    """
    Production d'un noeud XML avec positionnement des attributs

    :param attrs:
    :param text:
    :param parent: parent de l'element XML
    :param tag: balise
    :return: element cree
    """

    if tag:
        if parent is None:
            elem = Element(tag)
        else:
            elem = SubElement(parent, tag)
    else:
        elem = parent

    if attrs:
        for (k, v) in attrs.items():
            elem.attrib[k] = v

    return elem


def xml2text(elem, encoding="utf-8", xml_decl=True):
    """
        Retourne une version indentée de l'arbre XML
    :param encoding: encodage des données
    :param elem: noeud de l'arbre XML
    :return: Texte avec XML indenté
    """
    # rough_string = xml.etree.ElementTree.tostring(elem, encoding=encoding)
    # reparsed = minidom.parseString(rough_string)
    # return reparsed.toprettyxml(indent="  ")

    data = lxml.etree.tostring(
        elem, encoding=encoding, pretty_print=True, xml_declaration=xml_decl
    )
    return data.decode(encoding)


class GHT:
    GHT_KEYS = [
        "region",
        "ght_libelle",
        "ght_code",
        "finess",
        "categorie",
        "etablissement",
        "commune",
        "code_postal",
    ]
    FINESS_KEYS = [
        "structureet",
        "nofinesset",
        "nofinessej",
        "rs",
        "rslongue",
        "complrs",
        "compldistrib",
        "numvoie",
        "typvoie",
        "voie",
        "compvoie",
        "lieuditbp",
        "commune",
        "departement",
        "libdepartement",
        "ligneacheminement",
        "telephone",
        "telecopie",
        "categetab",
        "libcategetab",
        "categagretab",
        "libcategagretab",
        "siret",
        "codeape",
        "codemft",
        "libmft",
        "codesph",
        "libsph",
        "dateouv",
        "dateautor",
        "datemaj",
        "numuai",
    ]
    GEOFINESS_KEYS = [
        "geolocalisation",
        "nofinesset",
        "coordxet",
        "coordyet",
        "sourcecoordet",
        "datemaj",
    ]

    SRCDIR = "files"

    def __init__(self):
        self.df_ght = None
        self.df_finess = None
        self.df_finess_geo = None

    def load_data(self, ght_def_filename, etalab_filename):
        """
            lecture definition GHT
        :param ght_def_filename: Fichier des données contenant la liste des etablissements
        :param etalab_filename: Fichier des finess
        :return: -

        """

        local_filename = ght_def_filename
        if not ght_def_filename or not os.path.exists(ght_def_filename):
            dgosfiles = sorted(
                list(
                    filter(
                        lambda x: x == srcdata.SANTE_GOUV_GHT_FILENAME,
                        os.listdir(GHT.SRCDIR),
                    )
                )
            )
            if len(dgosfiles):
                # fichier present
                local_filename = os.path.join(GHT.SRCDIR, dgosfiles[0])
            else:
                # aucun fichier, telechargement
                local_filename = srcdata.download_sante_gouv_ght(GHT.SRCDIR)

        # Lecture du fichier excel, changement des noms de colonnes
        self.df_ght = pandas.read_excel(local_filename, sheet_name=0, dtype=str)
        _keys = list(self.df_ght.columns).copy()
        _keys[0:len(GHT.GHT_KEYS)] = GHT.GHT_KEYS
        self.df_ght.columns = _keys

        local_filename = etalab_filename
        if not etalab_filename or not os.path.exists(etalab_filename):
            # recherche d'un fichier present
            etalabfiles = sorted(
                list(
                    filter(
                        lambda x: x.startswith(srcdata.DATA_GOUV_FINESS_GEO),
                        os.listdir(GHT.SRCDIR),
                    )
                )
            )
            if len(etalabfiles):
                # fichier present
                local_filename = os.path.join(GHT.SRCDIR, etalabfiles[0])
            else:
                # fichier absent, telechargement
                local_filename = srcdata.download_data_gouv_finess(GHT.SRCDIR)

        # lecture fichier etalab
        finess = io.StringIO()
        finess_geo = io.StringIO()

        with codecs.open(local_filename, "r", "iso-8859-1") as fin:
            for line in fin.readlines():
                if line.startswith("structureet"):
                    finess.write(line)
                if line.startswith("geolocalisation"):
                    finess_geo.write(line)

        finess.seek(0)
        finess_geo.seek(0)

        self.df_finess = pandas.read_csv(
            finess,
            delimiter=";",
            names=GHT.FINESS_KEYS,
            header=0,
            index_col=False,
            dtype=str,
        )
        self.df_finess_geo = pandas.read_csv(
            finess_geo,
            delimiter=";",
            names=GHT.GEOFINESS_KEYS,
            header=0,
            index_col=False,
        )

    def ght_codes(self):
        """
            Liste des codes des GHT trouvés
        :return: liste des codes GHT
        """
        return self.df_ght["ght_code"].dropna().unique().tolist()

    def ght_all(self):
        """
            Retourne la liste des codes/libellés des GHT
        :return: liste de textes formattés
        """
        # version concat : self.df_ght[['ght_code', 'ght_libelle']].dropna().astype(str).apply(lambda x: ' '.join(x), axis=1).unique().tolist()
        li = []
        for elem in self.df_ght[["ght_code", "ght_libelle"]].dropna().values.tolist():
            newelem = "{:>8} : {}".format(elem[0], elem[1])
            if newelem not in li:
                li.append(newelem)
        return li

    def make_ght_bundle(self, ght_code):
        """
            Construction du bundle pour 1 GHT donné.

        :param ght_code: id du GHT. Remplacement des _ par des -
        :return: bundle FHIR en JSON
        """

        # ght-MAR_01 n'est pas 1 ID valid -> ght-MAR-01
        id_ght = "ght-%s" % ght_code.replace("_", "-")
        bundle = dict(resourceType="Bundle", id=f"bundle-{id_ght}", entry=[])
        bundle["type"] = "document"

        ght_name = self.df_ght.loc[
            self.df_ght.ght_code == ght_code
        ].ght_libelle.unique()[0]
        ght_state = self.df_ght.loc[self.df_ght.ght_code == ght_code].region.unique()[0]

        ej_count = len(self.df_ght[self.df_ght.ght_code == ght_code])

        org_ght = dict(
            resourceType="Organization",
            id=id_ght,
            text=dict(
                status="generated",
                div=f"""<div xmlns=\"http://www.w3.org/1999/xhtml\">GHT {ght_name} - Région {ght_state} - {ej_count} établissements juridiques</div>""",
            ),
            identifier=[
                dict(use="official", system="urn:fr-gouv-sante:ght", value=id_ght)
            ],
            name=f"GHT {ght_name.capitalize()}",
            address=[dict(state=ght_state)],
        )

        bundle["entry"].append(dict(resource=org_ght))

        for index, row in self.df_ght[self.df_ght.ght_code == ght_code].iterrows():
            # entite juridique
            ej_id = "%s-%s" % (str(row.finess).strip(), index)

            res_org = dict(
                resourceType="Organization",
                id=ej_id,
                text=dict(
                    status="generated",
                    div=f"""<div xmlns=\"http://www.w3.org/1999/xhtml\">Entité Juridique - finess {row.finess}</div>""",
                ),
                name=row.etablissement,
            )
            res_org["identifier"] = [
                dict(
                    use="official",
                    system="urn:fr-gouv-sante-finess:ej",
                    value=str(row.finess).strip(),
                )
            ]
            res_org["type"] = [
                dict(
                    coding=[
                        dict(
                            system="http://hl7.org/fhir/organization-type",
                            code="prov",
                            display="Healthcare Provider",
                        )
                    ]
                )
            ]
            res_org["partOf"] = dict(reference=f"Organization/{str(id_ght)}")
            bundle["entry"].append(dict(resource=res_org))

            for index_et, row_et in self.df_finess[
                self.df_finess.nofinessej == row.finess
            ].iterrows():
                # categetab	libcategetab
                # 355	Centre Hospitalier (C.H.)
                # 101	Centre Hospitalier Régional (C.H.R.)
                eg_id = "%s-%s" % (str(row.finess).strip(), row_et.nofinesset)

                if row_et.categetab:
                    # in ["101", "355"]:
                    # entite geo
                    res_org_et = dict(
                        resourceType="Organization",
                        id=eg_id,
                        text=dict(
                            status="generated",
                            div=f"""<div xmlns=\"http://www.w3.org/1999/xhtml\">Entité Géographique - finess {row.finess}</div>""",
                        ),
                        name=row_et.rs,
                        meta={"lastUpdated": f"{row_et.datemaj}T00:00:00Z"},
                        extension=[],
                    )

                    # code APE
                    if str(row_et.codeape) != "nan":
                        ape_ext = dict(
                            url="https://opikanoba.org/fhir/StructureDefinition/fr-insee-APE",
                            valueCoding=dict(
                                system="http://insee.fr/valuesets/APE",
                                code=row_et.codeape,
                            ),
                        )
                        res_org_et["extension"].append(ape_ext)

                    # categorie etab
                    if str(row_et.categetab) != "nan":
                        cat_ext = dict(
                            url="https://opikanoba.org/fhir/StructureDefinition/fr-gouv-sante-finess-cat-etab",
                            valueCoding=dict(
                                system="http://finess.sante.gouv.fr/valuesets/CAT_ETAB",
                                code=row_et.categetab,
                                display=row_et.libcategetab,
                            ),
                        )
                        res_org_et["extension"].append(cat_ext)

                    # categorie agregat etab
                    if str(row_et.categagretab) != "nan":
                        catagr_ext = dict(
                            url="https://opikanoba.org/fhir/StructureDefinition/fr-gouv-sante-finess-cat-agr-etab",
                            valueCoding=dict(
                                system="http://finess.sante.gouv.fr/valuesets/CAT_AGR_ETAB",
                                code=row_et.categagretab,
                                display=row_et.libcategagretab,
                            ),
                        )
                        res_org_et["extension"].append(catagr_ext)

                    # MFT
                    if str(row_et.codemft) != "nan":
                        mft_ext = dict(
                            url="https://opikanoba.org/fhir/StructureDefinition/fr-gouv-sante-finess-MFT",
                            valueCoding=dict(
                                system="http://finess.sante.gouv.fr/valuesets/MFT",
                                code=row_et.codemft,
                                display=row_et.libmft,
                            ),
                        )
                        res_org_et["extension"].append(mft_ext)

                    # SPH
                    if str(row_et.codesph) != "nan":
                        sph_ext = dict(
                            url="https://opikanoba.org/fhir/StructureDefinition/fr-gouv-sante-finess-SPH",
                            valueCoding=dict(
                                system="http://finess.sante.gouv.fr/valuesets/SPH",
                                code=row_et.codesph,
                                display=row_et.libsph,
                            ),
                        )
                        res_org_et["extension"].append(sph_ext)

                    res_org_et["identifier"] = [
                        dict(
                            use="official",
                            system="urn:fr-gouv-sante-finess:eg",
                            value=row_et.nofinesset,
                            period={"start": row_et.dateouv},
                        )
                    ]
                    if str(row_et.siret) != "nan":
                        res_org_et["identifier"].append(
                            dict(
                                use="official",
                                system="urn:fr-insee:SIRET",
                                value=row_et.siret,
                            )
                        )
                    res_org_et["type"] = [
                        dict(
                            coding=[
                                dict(
                                    system="http://hl7.org/fhir/organization-type",
                                    code="prov",
                                    display="Healthcare Provider",
                                )
                            ]
                        )
                    ]
                    line_vals = []

                    if str(row_et.numvoie) != "nan":
                        line_vals.append(str(row_et.numvoie))
                    if row_et.typvoie:
                        line_vals.append(str(row_et.typvoie))
                    if str(row_et.compvoie) != "nan":
                        line_vals.append(str(row_et.compvoie))
                    if row_et.voie:
                        line_vals.append(str(row_et.voie))

                    res_org_et["address"] = [
                        dict(use="work", line=[" ".join(line_vals)])
                    ]
                    res = re.match(r"(\d+)\s(.*)", row_et.ligneacheminement)
                    if res:
                        postalCode, city = res.groups()
                        res_org_et["address"][0]["postalCode"] = postalCode
                        res_org_et["address"][0]["city"] = city

                    res_org_et["partOf"] = dict(reference=f"Organization/{ej_id}")
                    bundle["entry"].append(dict(resource=res_org_et))

                    # Localisation GPS
                    location = dict(resourceType="Location", id="%s-loc" % eg_id)
                    geo = self.df_finess_geo[
                        self.df_finess_geo.nofinesset == row_et.nofinesset
                    ]
                    if geo.sourcecoordet.str.contains("LAMBERT_93").bool():
                        x, y = self.convert_coordinates(
                            float(geo.coordxet), float(geo.coordyet), "LAMBERT_93"
                        )
                    else:
                        x, y = float(geo.coordxet), float(geo.coordyet)

                    location["position"] = dict(longitude=x, latitude=y)
                    location["managingOrganization"] = dict(
                        reference=f"Organization/{eg_id}"
                    )
                    bundle["entry"].append(dict(resource=location))
        return bundle

    def convert_coordinates(self, xin, yin, proj):
        if proj == "LAMBERT_93":
            inProj = Proj(init="epsg:2154")
            outProj = Proj(init="epsg:4326")
            xout, yout = transform(inProj, outProj, xin, yin)
        else:
            xout, yout = xin, yin
        return xout, yout

    def toxml(self, orgs):
        """
            Production du fichier XML du bundle contenant les établissements du GHT
        :param orgs: bundle FHIR JSON contenant les entités du GHT
        :return: bundle FHIR XML
        """
        bundle = xmlelt(None, "Bundle", {"xmlns": "http://hl7.org/fhir"})
        xmlelt(bundle, "type", {"value": orgs["type"]})

        bundle.append(lxml.etree.Comment(f"Entry count = {len(orgs['entry'])}"))

        for entry in orgs["entry"]:
            container = xmlelt(
                xmlelt(xmlelt(bundle, "entry"), "resource"),
                entry["resource"]["resourceType"],
            )
            xmlelt(container, "id", {"value": str(entry["resource"]["id"])})

            if (
                "meta" in entry["resource"]
                and "lastUpdated" in entry["resource"]["meta"]
            ):
                xmlelt(
                    xmlelt(container, "meta"),
                    "lastUpdated",
                    {"value": entry["resource"]["meta"]["lastUpdated"]},
                )

            if "text" in entry["resource"]:
                text = xmlelt(container, "text")
                xmlelt(text, "status", {"value": entry["resource"]["text"]["status"]})
                text.append(lxml.etree.fromstring(entry["resource"]["text"]["div"]))

            if "extension" in entry["resource"]:
                for ext in entry["resource"]["extension"]:
                    ext_elem = xmlelt(container, "extension", {"url": ext["url"]})
                    if "valueCoding" in ext:
                        val_coding = xmlelt(ext_elem, "valueCoding")
                        xmlelt(
                            val_coding,
                            "system",
                            {"value": ext["valueCoding"]["system"]},
                        )

                        xmlelt(
                            val_coding, "code", {"value": ext["valueCoding"]["code"]}
                        )

                        if "display" in ext["valueCoding"]:
                            xmlelt(
                                val_coding,
                                "display",
                                {"value": ext["valueCoding"]["display"]},
                            )
                    if "valueCode" in ext:
                        xmlelt(
                            ext_elem, "valueCode", {"value": ext["valueCode"]["value"]}
                        )

            if "identifier" in entry["resource"]:
                for ident in entry["resource"]["identifier"]:
                    ident_elem = xmlelt(container, "identifier")
                    xmlelt(ident_elem, "use", {"value": ident["use"]})
                    xmlelt(ident_elem, "system", {"value": ident["system"]})
                    xmlelt(ident_elem, "value", {"value": ident["value"]})
                    if "period" in ident:
                        xmlelt(
                            xmlelt(ident_elem, "period"),
                            "start",
                            {"value": ident["period"]["start"]},
                        )

            if "type" in entry["resource"]:
                for current_type in entry["resource"]["type"]:
                    if "coding" in current_type:
                        for cod in current_type["coding"]:
                            coding = xmlelt(xmlelt(container, "type"), "coding")

                            xmlelt(coding, "system", {"value": cod["system"]})
                            xmlelt(coding, "code", {"value": cod["code"]})
                            xmlelt(coding, "display", {"value": cod["display"]})

            if "name" in entry["resource"]:
                xmlelt(container, "name", {"value": entry["resource"]["name"]})

            if "address" in entry["resource"]:
                for addr in entry["resource"]["address"]:

                    addr_elem = xmlelt(container, "address")
                    if "use" in addr:
                        xmlelt(addr_elem, "use", {"value": addr["use"]})
                    if "line" in addr:
                        for line in addr["line"]:
                            xmlelt(addr_elem, "line", {"value": line})

                    if "city" in addr:
                        xmlelt(addr_elem, "city", {"value": addr["city"]})
                    if "postalCode" in addr:
                        xmlelt(addr_elem, "postalCode", {"value": addr["postalCode"]})
                    if "state" in addr:
                        xmlelt(addr_elem, "state", {"value": addr["state"]})

            if "partOf" in entry["resource"]:
                xmlelt(
                    xmlelt(container, "partOf"),
                    "reference",
                    {"value": entry["resource"]["partOf"]["reference"]},
                )
            if "position" in entry["resource"]:
                pos = xmlelt(container, "position")
                xmlelt(
                    pos,
                    "longitude",
                    {"value": str(entry["resource"]["position"]["longitude"])},
                )
                xmlelt(
                    pos,
                    "latitude",
                    {"value": str(entry["resource"]["position"]["latitude"])},
                )
            if "managingOrganization" in entry["resource"]:
                xmlelt(
                    xmlelt(container, "managingOrganization"),
                    "reference",
                    {"value": entry["resource"]["managingOrganization"]["reference"]},
                )
        return bundle


def main():
    """
        Programme principal

        - parse les arguments
        - lance les traitements
    """

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--code",
        help="code GHT en particulier : CODE (voir --list pour avoir la liste). La valeur all permet de générer tous les codes",
    )
    parser.add_argument("--list", action="store_true", help="Liste les codes GHT")
    parser.add_argument(
        "--dgosfile", help="Fichier du ministère, donnant la liste des GHT"
    )
    parser.add_argument("--finessfile", help="Fichier Finess des établissements")
    parser.add_argument(
        "--outputdir",
        help="Repertoire de destination des fichiers générés",
        default="output",
    )
    args = parser.parse_args()

    ght = GHT()
    ght.load_data(args.dgosfile, args.finessfile)

    # Liste les codes GHT disponibles
    if args.list:
        for g in ght.ght_all():
            print(g.replace("_", "-"))

    # Traitement d'un code en particulier (ou tous les codes si all)
    if args.code:
        if not os.path.exists(args.outputdir):
            print(f"Creation de {args.outputdir}")
            os.makedirs(os.path.abspath(args.outputdir))

        codes = []
        if args.code == "all":
            codes.extend(ght.ght_codes())
        else:
            if args.code not in ght.ght_codes():
                print(
                    f"Code GHT [{args.code}] inconnu ! Pour connaitre la liste des codes GHT, utiliser l'option --list"
                )
            else:
                codes.append(args.code)

        for ght_code in codes:
            print(f"Generation GHT {ght_code}")
            orgs = ght.make_ght_bundle(ght_code)
            orgs_xml = ght.toxml(orgs)

            with open(os.path.join(args.outputdir, f"{ght_code}.json"), "w") as fout:
                fout.write(json.dumps(orgs, indent=2))

            with open(os.path.join(args.outputdir, f"{ght_code}.xml"), "w") as fout:
                fout.write(xml2text(orgs_xml))


if __name__ == "__main__":
    main()
