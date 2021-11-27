import io
import logging
import click

import shutil
import os

import coloredlogs
import yaml
from typing import List

from yaml import loader

import adoc.fetch
import adoc.render
import adoc.scanner
from adoc.abssystem import DFile

coloredlogs.install(fmt="%(asctime)s %(levelname)s %(message)s")

logging.basicConfig(level=logging.INFO)

def create_database(database):
    logging.info("Fetch remote projects")
    projectInfos = adoc.fetch.fetch_project_infos(False)

    adoc.fetch.download_repos(projectInfos, True)

    yaml_file = io.open(database, "w")
    yaml.dump(projectInfos, yaml_file)     

def gen_doc(database):
    
    logging.info("Read gitlab projects")
    yaml_file = io.open(database, "r")
    projectInfos = yaml.load(yaml_file, Loader=loader.Loader)

    projectInfos = list(
        filter(
            lambda x: "cia-automation/libraries" in x.http_url_to_repo,
            projectInfos
        )
    )[0:15]

    logging.info("Scan projects")
    adoc.scanner.scan_projects(projectInfos)

    logging.info("Render documentation")
    base_output_dir = "output"
    shutil.rmtree(base_output_dir, ignore_errors=True)
    shutil.copytree("static", os.path.join(base_output_dir, "static"))
    os.makedirs(base_output_dir, exist_ok=True)
    os.chdir(base_output_dir)

    output_dfiles: List[DFile] = []
    logging.info("Render documentation")
    adoc.render.render_doc(output_dfiles)

    index = 1
    for dfile in output_dfiles:
        logging.info(
            f"{index}/{len(output_dfiles)}: output {dfile.id}")
        index += 1
        dfile.write()

    # distutils.dir_util.copy_tree("./static", "./output/static")


@click.command()
@click.option("-c", "--create-db", "create_db", is_flag=True, default=False)
@click.option("-d", "--database", "database", default="db/db.yaml")
def main(create_db, database):
    
    if create_db:
        create_database(database)
   
    gen_doc(database)


if __name__ == '__main__':
    main()