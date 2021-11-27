import yaml
import adoc.ansiblemodel
from typing import List
import logging


def parse_block(yaml_source):
    yaml_source_copy = dict(yaml_source)
    yaml_source_copy.pop('block')
    name = yaml_source.get("name", None)
    result = adoc.ansiblemodel.AnsibleCodeBlock(
        name, "block", yaml_source_copy)
    result.tasks = parse_task_list(yaml_source, "block")

    return result


def is_task_clause(clause: str):
    list_clauses = [
        "action",
        "any_errors_fatal",
        "args",
        "async",
        "become",
        "become_flags",
        "become_method",
        "become_user",
        "changed_when",
        "check_mode",
        "collections",
        "connection",
        "debugger",
        "delay",
        "delegate_facts",
        "delegate_to",
        "diff",
        "environment",
        "failed_when",
        "ignore_errors",
        "ignore_unreachable",
        "local_action",
        "loop",
        "loop_control",
        "module_defaults",
        "name",
        "no_log",
        "notify",
        "poll",
        "port",
        "register",
        "remote_user",
        "retries",
        "run_once",
        "tags",
        "until",
        "vars",
        "when",
        "with_<lookup>",
    ]
    return clause in list_clauses


def parse_task_module(yaml_source):
    for key, value in yaml_source.items():
        if not is_task_clause(key):
            return key

    return "NO_FOUND"


def parse_task(yaml_source):
    name = yaml_source.get("name", None)
    module = parse_task_module(yaml_source)
    result = adoc.ansiblemodel.AnsibleCodeTask(name, module, yaml_source)
    return result


def parse_task_or_block(yaml_source):
    if not isinstance(yaml_source, (dict,)):
        raise AssertionError()

    yaml_block = yaml_source.get("block", None)
    if yaml_block is not None:
        result = parse_block(yaml_source)
    else:
        result = parse_task(yaml_source)

    return result


def parse_role_section(yaml_source, section_name):
    result = []

    return result


def parse_task_list(yaml_source, section_name):
    result = []

    yaml_tasks = yaml_source.get(section_name, None)
    if yaml_tasks is not None:
        for yaml_task in yaml_tasks:
            item = parse_task_or_block(yaml_task)
            result.append(item)

    return result


def parse_play(yaml_source):
    playbook = adoc.ansiblemodel.AnsibleCodePlaybook()

    playbook.name = yaml_source.get("name", None)

    import_playbook = yaml_source.get("import_playbook", None)
    if import_playbook is not None:
        playbook.import_playbook = import_playbook
    else:
        playbook.hosts = yaml_source.get("hosts", None)
        playbook.tasks = parse_task_list(yaml_source, "tasks")
        playbook.pre_tasts = parse_task_list(yaml_source, "pre_tasks")
        playbook.post_tasts = parse_task_list(yaml_source, "pre_posts")
        playbook.roles = parse_role_section(yaml_source, "roles")

    return playbook


def is_def(yaml_source):
    return isinstance(yaml_source, (dict,))


def is_play(yaml_source):
    result: bool = False
    if isinstance(yaml_source, (dict,)):
        result = (yaml_source.get("hosts", None) is not None) or (
            yaml_source.get("import_playbook", None) is not None)

    return result


def parse_variable_file(content):
    try:
        yaml_source = yaml.load(content)
    except:
        logging.exception("parse_variable_file")

    return yaml_source


def parse_ansible_code_file(content):

    result: List[adoc.ansiblemodel.AnsibleCodeObject] = []
    try:
        yaml_source = yaml.load(content)

        if yaml_source is not None:
            if is_def(yaml_source):
                pass
            else:
                for yaml_item in yaml_source:
                    if is_play(yaml_item):
                        ansible_item = parse_play(yaml_item)
                    else:
                        ansible_item = parse_task_or_block(yaml_item)

                    result.append(ansible_item)
    except:
        logging.exception("parse_ansible_code_file")

    return result
