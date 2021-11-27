class DFile(object):
    def __init__(self, id, content):
        self.id = id
        self.content = content

    def write(self):
        with open(self.id, "w") as fh:
            fh.write(self.content)
