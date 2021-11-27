# Introduction

## git Project
    
Name: project/path + project-name/

contains:
    playbooks: ansible/
    internal_roles: ansible/roles
    roles: meta/

## Artifacts

### Playbooks

Name: artifact/playbook/ path + Name of repo / version

Look for `ansible\main.yml`
Get logic
    ansible - playbook
    - hosts
    - tasks
    - roles

Scan Internal Roles
Any folder in ansible\roles\

Dependencies:
    Other playbooks
    Roles defined on roles/requirements.yml

    - [ansible-roles] -> reference
    - i.o.c. -> external reference

### Internal Roles

Name: artifact/playbook/ path + Name of repo / version / internal-role-name
Dependencies

### Roles

Name: artifact/role/path + repo-name / version
- Parse meta/main.yml
  - Info
  - Dependencies

