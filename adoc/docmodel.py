from git import Tree, Blob
import urllib
import os
import adoc.ansiblemodel
from typing import List
import re
from yaml import dump


# import urllib.parse


class RepoAnchor:
    def __init__(self, url):
        self.url = url

    def get_url(self):
        return self.url

    @classmethod
    def from_tree(cls, ref: Tree, *args):
        repo = ref.repo
        name = re.sub('^origin/', '', ref.name)

        origin_url = repo.remotes.origin.url
        without_ext_url = re.sub('\.git$', '', origin_url)
        url = without_ext_url + "/tree/" + name

        return cls(url)

    @classmethod
    def from_blob(cls, version: str, blob: Blob, *args):
        repo = blob.repo
        path = blob.path

        origin_url = repo.remotes.origin.url
        without_ext_url = re.sub('\.git$', '', origin_url)
        url = without_ext_url + "/blob/" + version + '/' + path

        return cls(url)


class RoleReference:
    def __init__(self, src: str, version: str, name: str, scm: str, *args):
        self.src = src
        self.version = version
        self.name = name
        self.scm = scm


class DocProjectInfo:
    def __init__(self, project, clone_path: str):
        self.name = project.name
        self.clone_path = clone_path
        self.path_with_namespace = project.attributes["path_with_namespace"]
        self.created_at = project.attributes.get("created_at", None)
        self.description = project.attributes.get("description", None)
        self.http_url_to_repo = project.attributes.get(
            "http_url_to_repo", None)
        self.issues = project.attributes.get("issues", None)
        self.last_activity_at = project.attributes.get(
            "last_activity_at", None)
        self.name_with_namespace = project.attributes.get(
            "name_with_namespace", None)
        self.open_issues_count = project.attributes.get(
            "open_issues_count", None)
        self.star_count = project.attributes.get("star_count", None)
        self.tag_list = project.attributes.get("tag_list", None)
        self.visibility = project.attributes.get("visibility", None)
        self.namespace = project.attributes.get("namespace", None)


class DocObject:
    def __init__(self, namespace: str, name: str, repo_anchor: RepoAnchor = None, *args):
        self.name = name
        self.namespace = namespace
        self.full_name = f"{namespace}/{name}"
        self.repo_anchor = repo_anchor
        self._id = f"{namespace}/{name}"
        self.path = self._id.replace("/", "__").replace("\\", "__")

        self._relations = {}
        self._properties = {}

    @property
    def id(self):
        return self._id

    @staticmethod
    def get_id(name: str, namespace: str):
        return f"{namespace}:{name}"

    def get_file_path(self, reference):
        return f"{self.path}_{reference}"

    def add_relation(self, docRelation):
        if self._relations.get(docRelation.id, None) is None:
            self._relations[docRelation.id] = docRelation

    def get_relation_source(self, relation_type: str):
        result = []
        if len(self._relations) > 0:
            result = [
                x
                for x in self._relations.values()
                if (
                    x.relation_type == relation_type
                    or relation_type == DocRelationType.ANY
                )
                and (x.source.id == self.id)
            ]
        return result

    def get_relation_target(self, relation_type: List[str]):
        result = []
        if len(self._relations) > 0:
            result = [
                x
                for x in self._relations.values()
                if (
                    x.relation_type in relation_type
                    or relation_type == DocRelationType.ANY
                )
                and (x.target.id == self.id)
            ]
        return result

    def get_properties(self, scope: str):
        result = []
        for key, value in self._properties.items():
            result.append(value)

        result = list(
            filter(
                lambda x: re.search(
                    scope, x.scope) is not None,
                self._properties.values(),
            )
        )

        return result

    def add_property(self, name: str, value, scope: str):
        doc_property: DocProperty = DocProperty(name, value, scope)
        self._properties[name] = doc_property

    def is_reference(self):
        return False

    def get_project_url(self):
        result = ''
        if self.repo_anchor:
            result = self.repo_anchor.get_url()

        return result


class DocRelationType:
    INCLUDE = "INCLUDE"
    INTERNAL_ROLE = "INTERNAL_ROLE"
    REQUIREMENTS = "REQUIREMENTS"
    ANSIBLE_CODE = "ANSIBLE_CODE"
    ANY = "ANY"


class DocRelation:
    def __init__(self, source: DocObject, target: DocObject, relation_type: str):
        self.source = source
        self.target = target
        self.relation_type = relation_type
        self.id = DocRelation.get_id(source, target, relation_type)

    @staticmethod
    def get_id(source: DocObject, target: DocObject, relation_type: str):
        return f"{source.id}:{relation_type}:{target.id}"


class DocProperty:
    def __init__(
        self, name: str, value, scope=None, *args
    ):
        self.id = (scope + "#" + name if scope else name)
        self.name = name
        self.value = value
        self.scope = scope
        self.value_yml = dump(value, default_flow_style=False)


class DocRepoRef(DocObject):
    def __init__(self, name: str, repo_ref_type: str):
        self.name = name
        self.repo_ref_type = repo_ref_type


class DocProject(DocObject):
    def __init__(self, namespace: str,
                 name: str,
                 project_info: DocProjectInfo,
                 repo_anchor: RepoAnchor = None,
                 *args):
        super(DocProject, self).__init__(namespace, name, "", *args)

        self.project_info = project_info
        self.repo_refs = {}

    def resolve_repo_ref(self, name: str, repo_ref_type: str):
        repo_ref = self.repo_refs.get(name, None)
        if repo_ref is None:
            repo_ref = DocRepoRef(name, repo_ref_type)
            self.repo_refs[repo_ref.name] = repo_ref
        return repo_ref


class DocArtifact(DocObject):
    def __init__(
        self,
        namespace: str,
        name: str,
        version: str,
        repo_anchor: RepoAnchor = None,
        *args
    ):
        super(DocArtifact, self).__init__(namespace, name, repo_anchor, *args)
        self.version = version.replace("origin/", "")
        self.is_version = re.match("^v([(\d+\.]+)", self.version) is not None
        self._id = f"{namespace}/{name}/{self.version}"
        self.path = self._id.replace("/", "__")

    @staticmethod
    def get_id(namespace, name, version):
        id = f"{namespace}/{name}/{version}"
        return id

    def get_project(self):
        result = []
        if len(self._relations) > 0:
            result = next(iter(
                x.source
                for x in self._relations.values()
                if x.relation_type == DocRelationType.INCLUDE
                and (x.target.id == self.id)
            ), None)
        return result

    def is_reference(self):
        return self.get_project() is None


class DocRoleArtifact(DocArtifact):
    def __init__(
        self,
        namespace: str,
        name: str,
        version: str,
        repo_anchor: RepoAnchor = None,
        *args
    ):
        super(DocRoleArtifact, self).__init__(
            namespace, name, version, repo_anchor, *args)


class DocInnerRoleArtifact(DocRoleArtifact):
    def __init__(
        self,
        namespace: str,
        name: str,
        version: str,
        repo_anchor: RepoAnchor = None,
        *args
    ):
        super(DocInnerRoleArtifact, self).__init__(
            namespace, name, version, repo_anchor, *args)


class DocPlaybookArtifact(DocArtifact):
    def __init__(
        self,
        namespace: str,
        name: str,
        version: str,
        repo_anchor: RepoAnchor = None,
        *args
    ):
        super(DocPlaybookArtifact, self).__init__(
            namespace, name, version, repo_anchor, *args)


class DocAnsibleCodeFile(DocArtifact):
    def __init__(
        self,
        namespace: str,
        name: str,
        version: str,
        repo_anchor: RepoAnchor = None,
        *args,
    ):
        super(DocAnsibleCodeFile, self).__init__(
            namespace, name, version, repo_anchor, *args
        )
        self.ansibleCodeObjects: [adoc.ansiblemodel.AnsibleCodeObject] = None


class DocRepo:
    def __init__(self):
        self._artifacts = {}
        self._projects = {}
        self._relations = {}

    @property
    def artifacts(self):
        return self._artifacts

    @property
    def projects(self):
        return self._projects

    def add_artifact(self, docArtifact: DocArtifact):
        doc_repo.artifacts[docArtifact.id] = docArtifact

    def resolve_project(self, namespace: str, name: str, project_info):
        project_id = DocProject.get_id(namespace, name)
        doc_project = doc_repo.projects.get(project_id, None)
        if doc_project is None:
            doc_project = DocProject(namespace, name, project_info)

            doc_repo.projects[project_id] = doc_project

        return doc_project

    def resolve_relation(self, source: DocObject, target: DocObject, relation_type: str):
        id = DocRelation.get_id(source, target, relation_type)
        relation = self._relations.get(id, None)
        if relation is None:
            relation = DocRelation(source, target, relation_type)
            self._relations[relation.id] = relation
            source.add_relation(relation)
            target.add_relation(relation)
        return relation

    def resolve_role_by_params(self, namespace: str, name: str, version: str):
        id = DocArtifact.get_id(namespace, name, version)
        role = self._artifacts.get(id, None)
        if role is None:
            role = DocRoleArtifact(namespace, name, version, None)
            self._artifacts[role.id] = role
        return role

    def resolve_role(self, role_reference: RoleReference):
        path = urllib.parse.urlparse(role_reference.src).path
        namespace = os.path.dirname(path).strip("/")
        name = os.path.splitext(os.path.basename(path))[0]

        version = role_reference.version
        if version is None:
            version = "master"
        role = self.resolve_role_by_params(namespace, name, version)
        return role

    def find_artifacts(self, namespace: str, name: str):
        result = [
            x
            for x in self.artifacts.values()
            if x.namespace == namespace and x.name == name
        ]
        return result


doc_repo = DocRepo()
