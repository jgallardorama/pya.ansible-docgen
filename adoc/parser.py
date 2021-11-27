import yaml
from adoc.docmodel import RoleReference


def parse_requirement_file(content):
    lstRoles = []
    entries = yaml.load(content)
    if isinstance(entries, (list,)):
        for role_entry in entries:
            if isinstance(role_entry, (dict,)):
                scm = role_entry.get("scm", None)
                name = role_entry.get("name", None)
                version = role_entry.get("version", None)
                src = role_entry.get("src", None)
                if src is not None:
                    # rise error
                    artifactReference = RoleReference(src, version, name, scm)
                    lstRoles.append(artifactReference)

    return lstRoles


def parse_meta_file(content):
    metadata = yaml.load(content)
    if isinstance(metadata, (dict,)):
        galaxy_info = metadata.get("galaxy_info", None)
        role_name = metadata.get("role_name", None)
        author = metadata.get("author", None)
        description = metadata.get("description", None)
        company = metadata.get("company", None)
        license = metadata.get("license", None)
        min_ansible_version = metadata.get("min_ansible_version", None)
        galaxy_tags = metadata.get("galaxy_tags", None)
        platforms = metadata.get("platforms", None)
