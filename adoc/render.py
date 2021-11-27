from pathlib import Path
from graphviz import Digraph
from typing import List
from adoc.docmodel import DocProject, DocArtifact, doc_repo, DocRelationType, DocPlaybookArtifact, DocRoleArtifact
from adoc.template_manager import TemplateManager
from adoc.abssystem import DFile

import os
import logging

templateManager = TemplateManager()


def render_project_graph(doc_project: DocProject):
    dot = Digraph(
        comment=f"Project {doc_project.name}",
        name="Project {doc_project.name}",
        graph_attr={"rankdir": "LR"},
    )

    dot.node(
        doc_project.name, doc_project.name, href=f"{doc_project.path}", target="_top"
    )

    content = dot.pipe(format="svg").decode('utf-8')
    return DFile(doc_project.get_file_path("included.svg"), content)


def render_project(doc_project: DocProject, output_dfiles: List[DFile]):
    project_path = Path(doc_project.get_file_path("index.html"))
    templateManager.render(output_dfiles,
                           "project", project_path.name, project=doc_project)


def get_node_attr(values):
    attr = {}
    if DocRelationType.INTERNAL_ROLE in values:
        inner_role = {"fillcolor": "lightblue", "style": "filled"}
        attr = {**attr, **inner_role}
    if "IS_REFERENCE" in values:
        inner_role = {"fillcolor": "lightyellow", "style": "filled"}
        attr = {**attr, **inner_role}
    return attr


def get_edge_attr(values):
    attr = {}
    if DocRelationType.INTERNAL_ROLE in values:
        inner_role = {"style": "bold"}
        attr = {**attr, **inner_role}
    if DocRelationType.REQUIREMENTS in values:
        inner_role = {"style": "dashed"}
        attr = {**attr, **inner_role}
    return attr


def render_included_graph(doc_artifact: DocArtifact, output_dfiles: List[DFile]):
    dot = Digraph(
        comment=f"Project {doc_artifact.name}",
        name="Project {doc_artifact.name}",
        graph_attr={"rankdir": "LR"},
    )

    with dot.subgraph(name="cluster_0") as subgraph:
        attr = {"fillcolor": "lightyellow", "style": "filled"}

        subgraph.node(
            doc_artifact.id,
            f"{{ { doc_artifact.name } | { doc_artifact.version } }}",
            attr,
            shape="record",
            href=doc_artifact.get_file_path("index.html"),
            target="_top",
        )

        relations = doc_artifact.get_relation_source(
            DocRelationType.INTERNAL_ROLE)
        for relation in relations:
            attr_labels = [
                DocRelationType.INTERNAL_ROLE,
                "IS_REFERENCE" if relation.target.is_reference() else "IS_NOT_REFERENCE",
            ]
            attr = get_node_attr(attr_labels)
            subgraph.node(
                relation.target.id,
                f"{{ { relation.target.name } | { relation.target.version } }}",
                attr,
                shape="record",
                href=relation.target.get_file_path("index.html"),
                target="_top",
            )
            dot.edge(relation.source.id, relation.target.id,
                     relation.relation_type)

    relations = doc_artifact.get_relation_source(DocRelationType.REQUIREMENTS)
    for relation in relations:
        attr_labels = [
            DocRelationType.REQUIREMENTS,
            "IS_REFERENCE" if relation.target.is_reference() else "IS_NOT_REFERENCE",
        ]

        attr = get_node_attr(attr_labels)
        dot.node(
            relation.target.id,
            f"{{ { relation.target.name } |{ relation.target.version } }}",
            attr,
            shape="record",
            href=relation.target.get_file_path("index.html"),
            target="_top",
        )
        attr = get_edge_attr(attr_labels)
        dot.edge(relation.source.id, relation.target.id,
                 relation.relation_type, attr)

    content = dot.pipe(format="svg").decode('utf-8')
    dfile = DFile(doc_artifact.get_file_path("included.svg"), content)

    output_dfiles.append(dfile)


def render_included_by_graph(doc_artifact: DocArtifact, output_dfiles: List[DFile]):
    dot = Digraph(
        comment=f"Included By {doc_artifact.name}",
        name="Included By {doc_artifact.name}",
        graph_attr={"rankdir": "LR"},
        node_attr={"rankdir": "TB"},
    )
    attr = get_node_attr([])
    dot.node(
        doc_artifact.id,
        f"{{ { doc_artifact.name } | { doc_artifact.version } }}",
        attr,
        shape="record",
        href=doc_artifact.get_file_path("index.html"),
        target="_top",
    )

    relations = doc_artifact.get_relation_target(
        [DocRelationType.INTERNAL_ROLE, DocRelationType.REQUIREMENTS])
    for relation in relations:
        attr = get_node_attr(
            [
                DocRelationType.INTERNAL_ROLE,
                "IS_REFERENCE" if relation.target.is_reference() else "IS_NOT_REFERENCE",
            ]
        )
        dot.node(
            relation.source.id,
            f"{{ { relation.source.name } |{ relation.source.version } }}",
            shape="record",
            href=relation.source.get_file_path("index.html"),
            target="_top",
        )
        dot.edge(relation.source.id, relation.target.id,
                 relation.relation_type)

    content = dot.pipe(format="svg").decode('utf-8')
    dfile = DFile(doc_artifact.get_file_path("included_by.svg"), content)
    output_dfiles.append(dfile)


def get_artifact_template(doc_artifact: DocArtifact):
    result: str = "artifact"
    if type(doc_artifact) is DocRoleArtifact:
        result = "artifact_role"
    elif type(doc_artifact) is DocPlaybookArtifact:
        result = "artifact_playbook"
    else:
        result = "artifact"

    return result


def render_artifact(doc_artifact: DocArtifact, output_dfiles: List[DFile]):

    file_path = Path(doc_artifact.get_file_path("index.html"))

    artifact_template = get_artifact_template(doc_artifact)

    templateManager.render(output_dfiles,
                           artifact_template, file_path.name, artifact=doc_artifact, doc_repo=doc_repo
                           )

    render_included_graph(doc_artifact, output_dfiles)
    render_included_by_graph(doc_artifact, output_dfiles)


def render_projects(output_dfiles: List[DFile]):
    projects = doc_repo.projects.values()
    num_projects = len(projects)
    index = 1
    for doc_project in projects:
        logging.info(
            f"{index}/{num_projects}: rendering project {doc_project.name}")
        index += 1
        render_project(doc_project, output_dfiles)


def render_artifacts(output_dfiles: List[DFile]):
    index = 1
    num_artifacts = len(doc_repo.artifacts)
    for doc_artifact in doc_repo.artifacts.values():
        logging.info(
            f"{index}/{num_artifacts}: rendering artifact {doc_artifact.name} :"
            + f"{doc_artifact.version}"
        )
        index += 1
        render_artifact(doc_artifact, output_dfiles)


def render_doc(output_dfiles: List[DFile]):

    templateManager.render(output_dfiles, "main",
                           "index.html", doc_repo=doc_repo)
    templateManager.render(output_dfiles, "projects",
                           "projects.html", doc_repo=doc_repo)
    templateManager.render(output_dfiles, "artifacts",
                           "artifacts.html", doc_repo=doc_repo)

    render_projects(output_dfiles)

    render_artifacts(output_dfiles)
