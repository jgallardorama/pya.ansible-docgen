import logging

from git import Repo, Tree, Blob, RemoteReference, TagReference
import re
from adoc.docmodel import (
    DocProject,
    DocArtifact,
    DocPlaybookArtifact,
    DocProperty,
    DocAnsibleCodeFile,
    doc_repo,
    DocRoleArtifact,
    DocRelationType,
    RepoAnchor
)
import adoc.parser
import adoc.parser_ansible


def scan_requirement_yaml(content):
    pass


def scan_inner_roles(pb_artifact: DocArtifact, ansible_roles_tree: Tree):
    for role_tree in ansible_roles_tree.trees:
        logging.info(f"*** INTERNAL ROLES ***")
        inner_role_artifact = DocRoleArtifact(
            pb_artifact.full_name,
            role_tree.name,
            pb_artifact.version,
            RepoAnchor.from_tree(role_tree)
        )

        doc_repo.add_artifact(inner_role_artifact)

        doc_repo.resolve_relation(
            pb_artifact, inner_role_artifact, DocRelationType.INTERNAL_ROLE
        )

        project_artifact = pb_artifact.get_project()
        doc_repo.resolve_relation(
            project_artifact, inner_role_artifact, DocRelationType.INCLUDE)


def scan_ansible_files(pb_artifact: DocArtifact, ansible_playbook_blobs: Blob):
    for ansible_playbook_blob in ansible_playbook_blobs:
        content = ansible_playbook_blob.data_stream.read()
        ansible_code_items = adoc.parser_ansible.parse_ansible_code_file(
            content)

        repo_anchor = RepoAnchor.from_blob(
            pb_artifact.version, ansible_playbook_blob)

        docPlaybookCode = DocAnsibleCodeFile(
            pb_artifact.full_name + ansible_playbook_blob.path,
            ansible_playbook_blob.name,
            pb_artifact.version,
            repo_anchor
        )

        docPlaybookCode.ansibleCodeObjects = ansible_code_items

        doc_repo.resolve_relation(
            pb_artifact, docPlaybookCode, DocRelationType.ANSIBLE_CODE
        )

    # lst = pb_artifact.get_relation_source(DocRelationType.ANSIBLE_CODE)
    # lst = lst.sort()


def scan_variable_files(pb_artifact: DocArtifact,
                        ansible_variables_blobs: Blob,
                        group_name: str):
    for ansible_variables_blob in ansible_variables_blobs:
        content = ansible_variables_blob.data_stream.read()
        variable_items = adoc.parser_ansible.parse_variable_file(content)
        if variable_items is not None:
            for key, value in variable_items.items():
                prop = DocProperty(key, value, ansible_variables_blob.path)
                pb_artifact._properties[prop.id] = prop


def scan_ansible_playbook(docProject: DocProject, repo_reference):
    tree = repo_reference.commit.tree
    trasverse = list(tree.traverse())
    repo_anchor = RepoAnchor.from_tree(repo_reference)

    pb_artifact = DocPlaybookArtifact(
        docProject.namespace, docProject.name, repo_reference.name, repo_anchor
    )
    doc_repo.add_artifact(pb_artifact)

    doc_repo.resolve_relation(docProject, pb_artifact, DocRelationType.INCLUDE)

    ansible_roles_tree: Tree = next(
        (x for x in trasverse if x.path ==
         "ansible/roles" and x.type == "tree"), None
    )
    if ansible_roles_tree is not None:
        scan_inner_roles(pb_artifact, ansible_roles_tree)

    requirement_blob: Blob = next(
        (x for x in trasverse if x.path == "roles/requirements.yml"), None
    )
    if requirement_blob is not None:
        scan_role_requirements(pb_artifact, repo_reference, requirement_blob)

    ansible_playbook_file_tree: Tree = list(
        filter(
            lambda x: re.search(
                r"ansible\/[a-zA-Z0-9-_]+\.(yml|yaml)", x.path) is not None
            and x.type == "blob",
            trasverse,
        )
    )
    if ansible_playbook_file_tree is not None:
        scan_ansible_files(pb_artifact, ansible_playbook_file_tree)


def scan_ansible_role(docProject, repo_reference, meta_file_blob):
    data = meta_file_blob.data_stream.read()
    meta_info = adoc.parser.parse_meta_file(data)
    role_artifact = doc_repo.resolve_role_by_params(
        docProject.namespace, docProject.name, repo_reference.name
    )

    doc_repo.resolve_relation(
        docProject, role_artifact, DocRelationType.INCLUDE)
    role_artifact.meta_info = meta_info

    tree = repo_reference.commit.tree

    role_artifact.repo_anchor = RepoAnchor.from_tree(repo_reference)

    trasverse = list(tree.traverse())

    ansible_playbook_file_tree: Tree = list(
        filter(
            lambda x: re.search(
                r"tasks\/[a-zA-Z0-9-_]+\.(yml|yaml)", x.path) is not None
            and x.type == "blob",
            trasverse,
        )
    )
    if ansible_playbook_file_tree is not None:
        scan_ansible_files(role_artifact, ansible_playbook_file_tree)

    vars_file_tree: Tree = list(
        filter(
            lambda x: re.search(
                r"vars\/[a-zA-Z0-9-_]+\.(yml|yaml)", x.path) is not None
            and x.type == "blob",
            trasverse,
        )
    )
    if vars_file_tree is not None:
        scan_variable_files(role_artifact, vars_file_tree, "vars")

    vars_file_tree: Tree = list(
        filter(
            lambda x: re.search(
                r"defaults\/[a-zA-Z0-9-_]+\.(yml|yaml)", x.path) is not None
            and x.type == "blob",
            trasverse,
        )
    )
    if vars_file_tree is not None:
        scan_variable_files(role_artifact, vars_file_tree, "defaults")

    return role_artifact


def scan_role_requirements(doc_artifact: DocArtifact, reference, requirement_blob):
    content = requirement_blob.data_stream.read()
    req_roles = adoc.parser.parse_requirement_file(content)

    for req_role in req_roles:
        if req_role.scm is not None:
            doc_role_artifact = doc_repo.resolve_role(req_role)
            doc_repo.resolve_relation(
                doc_artifact, doc_role_artifact, DocRelationType.REQUIREMENTS
            )


def scan_repo_reference(docProject: DocProject, repo_ref):
    try:

        docProject.resolve_repo_ref(repo_ref.name, type(repo_ref).__name__)

        tree = repo_ref.commit.tree
        trasverse = list(tree.traverse())

        ansible_tree: Blob = next(
            (x for x in trasverse if x.path == "ansible"), None)
        if ansible_tree is not None:
            logging.info(
                f" : Scanning Ansible Playbook: {docProject.name} {repo_ref.name}"
            )
            scan_ansible_playbook(docProject, repo_ref)

        meta_file_blob: Blob = next(
            (x for x in trasverse if x.path == "meta/main.yml"), None
        )
        if meta_file_blob is not None:
            logging.info(
                f" : Scanning Ansible Role: {docProject.name} {repo_ref.name}")
            scan_ansible_role(docProject, repo_ref, meta_file_blob)

    except Exception:
        logging.exception("")


def filter_repo_ref(repo_ref):
    result = isinstance(repo_ref, TagReference)
    result = result or (
        isinstance(repo_ref, RemoteReference)
        and repo_ref.name.startswith("origin")
        and not repo_ref.name.endswith("HEAD")
    )
    return result


def scan_repo(docProject: DocProject, repo: Repo):
    for repo_ref in repo.references:
        if filter_repo_ref(repo_ref):
            logging.info(
                f" : Scanning Repo Reference {docProject.name} {repo_ref.name}")
            scan_repo_reference(docProject, repo_ref)
        else:
            logging.warn(f"Skip {docProject.name} {repo_ref.name}")


def scan_project(project_info):
    namespace: str = project_info.namespace["full_path"]
    target: str = project_info.clone_path
    docProject = doc_repo.resolve_project(
        namespace, project_info.name, project_info
    )

    for property_name, property_value in vars(project_info).items():
        docProject.add_property(
            property_name, property_value, "project-info")

    repo = Repo(target)
    scan_repo(docProject, repo)


def scan_projects(project_infos):
    index: int = 0
    num_projects = len(project_infos)
    for project_info in project_infos:
        logging.info(f"{index}/{num_projects}: Scanning {project_info.name}")
        index += 1
        try:
            scan_project(project_info)
        except Exception:
            logging.exception("Scan projects")
