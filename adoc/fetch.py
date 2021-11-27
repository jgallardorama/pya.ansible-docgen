from gitlab import gitlab, Gitlab
import os
from git import Repo
from adoc.docmodel import DocProjectInfo
import logging
from typing import List


def get_gitlab():
    hostname = "gitlab.cia.com"
    url = "https://" + hostname

    with open("secrets/" + hostname, "r") as file:
        token = file.read()

    gl: Gitlab = gitlab.Gitlab(url, private_token=token)
    gl.auth()

    return gl


def get_base_clone_dir():
    base_dir: str = "C:\\repos\\"
    return base_dir


def fetch_project_infos(fetch: bool):

    gl = get_gitlab()
    # cia_group = gl.groups.list(search="cia-iac")[0]
    # cia_group = gl.groups.list(search="cia-iac")[0]

    index = 1
    projects = gl.projects.list(all=True, include_subgroups=True)
    num_project = len(projects)

    gitlab_projects = []

    for project in projects:
        try:
            logging.info(f"{index} / {num_project} : {project.name}")
            index += 1

            # url: str = project.attributes["http_url_to_repo"]
            namespace: str = project.namespace["full_path"]
            clone_path: str = os.path.join(
                get_base_clone_dir(), namespace, project.name)

            gitlab_project = DocProjectInfo(project, clone_path)
            gitlab_projects.append(gitlab_project)
        except:
            logging.exception(f"{index} / {num_project} : {project.name}")

    return gitlab_projects


def download_repos(gitlab_projects: List[DocProjectInfo], fetch: bool):
    gitlab_project: DocProjectInfo
    num_project = len(gitlab_projects)
    index: int = 0
    for gitlab_project in gitlab_projects:
        try:
            logging.info(f"{index} / {num_project} : {gitlab_project.name}")
            index += 1
            if not os.path.isdir(gitlab_project.clone_path):
                os.makedirs(gitlab_project.clone_path, exist_ok=True)
                repo: Repo = Repo.clone_from(
                    url=gitlab_project.http_url_to_repo, to_path=gitlab_project.clone_path
                )
            elif fetch:
                os.makedirs(gitlab_project.clone_path, exist_ok=True)
                repo: Repo = Repo(gitlab_project.clone_path)
                for remote in repo.remotes:
                    remote.fetch()
        except:
            logging.exception(
                f"{index} / {num_project} : {gitlab_project.name}")
