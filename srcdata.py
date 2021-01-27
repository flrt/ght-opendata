#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
    Telechargement des fichiers source necessaires
    - fichier de la liste des GHT : ministere de la santé
    - fichier des finess : data.gouv.fr

"""

__author__ = "Frederic Laurent"
__version__ = "1.0"
__copyright__ = "Copyright 2018, Frederic Laurent"
__license__ = "MIT"

import requests
import json
import os.path
import os
import shutil

DATA_GOUV_FINESS_DATASET_ID = "53699569a3a729239d2046eb"
DATA_GOUV_FINESS_URL = (
    f"https://www.data.gouv.fr/api/1/datasets/{DATA_GOUV_FINESS_DATASET_ID}/"
)
DATA_GOUV_FINESS_GEO = "etalab-cs1100507-stock"

SANTE_GOUV_GHT_FILENAME = "dgos_ght_liste_290119_2.xlsx"
SANTE_GOUV_GHT_URL = (
    f"https://solidarites-sante.gouv.fr/IMG/xlsx/{SANTE_GOUV_GHT_FILENAME}"
)


def download(url, filename):
    """
        Telechargement de l'URL dans le fichier destination
    :param url: URL a telecharger
    :param filename: fichier de destination
    """

    print(f"Telechargement : {url} -> {filename}")
    #r = requests.get(url)
    #with open(filename, "wb") as fd:
    #    for chunk in r.iter_content(chunk_size=128):
    #        fd.write(chunk)


    req = requests.get(url, stream=True)
    with open(filename, 'wb') as f:
        shutil.copyfileobj(req.raw, f)
    return filename


def download_data_gouv_finess(outputdir):
    """
        Telechargement du fichier des finess en interrogeant l'API data.gouv.fr pour avoir la dernière version

    :param outputdir: répertoire de destination
    :return: -
    """
    if not os.path.exists(outputdir):
        os.makedirs(outputdir)

    req = requests.get(DATA_GOUV_FINESS_URL)
    if req.status_code == 200:
        dataset_info = json.loads(req.text)
        for entry in dataset_info["resources"]:
            # url etalab-cs1100502-stock-20181011-0458.csv
            if entry["mime"] == "text/csv" and DATA_GOUV_FINESS_GEO in entry["url"]:
                filename = os.path.basename(entry["url"])
                return download(entry["url"], os.path.join(outputdir, filename))
    else:
        print(f"Error HTTP : {req.status_code}")
    return None


def download_sante_gouv_ght(outdir):
    """
        Telechargement du fichier contenant la liste des GHT

    :param outputdir: répertoire de destination
    :return: -
    """
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    return download(SANTE_GOUV_GHT_URL, os.path.join(outdir, SANTE_GOUV_GHT_FILENAME))

if __name__ == "__main__":
    download_data_gouv_finess("files")
    download_sante_gouv_ght("files")
    
