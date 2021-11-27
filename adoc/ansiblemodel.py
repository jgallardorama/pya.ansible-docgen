from yaml import dump


class AnsibleCodeObject:
    def __init__(self, *args):
        pass

        self.is_play = False
        self.is_task = False
        self.is_block = False
        self.is_role_ref = False


class AnsibleCodePlaybook(AnsibleCodeObject):
    def __init__(self, *args):
        super(AnsibleCodePlaybook, self).__init__(*args)
        self.name = None
        self.hosts = None
        self.tasks = []
        self.pre_tasks = []
        self.post_tasks = []
        self.roles = []
        self.import_playbook = None

        self.is_play = True


class AnsibleCodeTask(AnsibleCodeObject):
    def __init__(self, name: str, module: str, yaml_source, *args):
        super(AnsibleCodeTask, self).__init__(*args)
        self.name = name
        self.module = module
        self.yaml_source = yaml_source
        self.yaml_txt = dump(yaml_source, default_flow_style=False)
        self.is_reference = False
        self.is_block = False

        self.is_task = True


class AnsibleCodeBlock(AnsibleCodeTask):
    def __init__(self, name: str, module: str, yaml_source, *args):
        super(AnsibleCodeBlock, self).__init__(
            name, module, yaml_source, *args)

        self.is_block = True
        self.tasks = []


class AnsibleCodeRoleReference(AnsibleCodeObject):
    def __init__(self, *args):
        super(AnsibleCodeRoleReference, self).__init__(*args)
        self.is_role_ref = True
