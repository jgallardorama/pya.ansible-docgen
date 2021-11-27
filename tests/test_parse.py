import adoc.parser
import os
import re


def test_parse_requirement_fail():
    path = os.path.join(os.path.dirname(__file__), "samples/requirements_fail.yml")
    file = open(path, "r")
    content = file.read()
    adoc.parser.parse_requirement_file(content)


def test_parse_requirement_s1():
    path = os.path.join(os.path.dirname(__file__), "samples/requirements_s1.yml")
    file = open(path, "r")
    content = file.read()
    adoc.parser.parse_requirement_file(content)


def test_parse_requirement_s2():
    path = os.path.join(os.path.dirname(__file__), "samples/requirements_s2.yml")
    file = open(path, "r")
    content = file.read()
    references = adoc.parser.parse_requirement_file(content)
    assert len(references) > 0


def test_parse_playbook_s1():
    path = os.path.join(os.path.dirname(__file__), "samples/playbook_s1.yml")
    file = open(path, "r")
    content = file.read()
    references = adoc.parser.parse_ansible_code_file(content)
    assert len(references) > 0


def test_match_string():
    my_list = ["ansible/hola", "ansible/main.yml", "ansible/test.yml"]
    match_list = list(filter(lambda x: re.match(r"ansible\/\w+\.yml", x), my_list))
    assert len(match_list) >= 2
