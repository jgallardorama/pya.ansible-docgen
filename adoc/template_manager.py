from jinja2 import Environment, FileSystemLoader, Template

import os
from typing import List
from adoc.abssystem import DFile


class TemplateManager:
    def __init__(self, *args):
        template_dir = os.path.dirname(
            os.path.realpath(__file__)) + "/templates"
        print("+***" + template_dir)
        env = Environment(loader=FileSystemLoader(template_dir))
        self._templates = {}

        self._templates["projects"] = env.get_template("projects.html.j2")
        self._templates["project"] = env.get_template("project.html.j2")
        self._templates["artifact_playbook"] = env.get_template(
            "artifact_playbook.html.j2")
        self._templates["artifact_role"] = env.get_template(
            "artifact_role.html.j2")
        self._templates["artifact"] = env.get_template("artifact.html.j2")
        self._templates["artifacts"] = env.get_template("artifacts.html.j2")
        self._templates["main"] = env.get_template("main.html.j2")

    def get_template(self, template_name: str) -> Template:
        return self._templates[template_name]

    def render(
        self, output_dfiles: List[DFile], template_name: str, output_path: str, *args, **kwargs
    ):
        template = self.get_template(template_name)
        output = template.render(*args, **kwargs)

        dfile = DFile(output_path, output)
        output_dfiles.append(dfile)
