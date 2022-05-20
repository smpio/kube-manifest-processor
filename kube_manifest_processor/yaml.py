import ruamel.yaml

# see https://github.com/kubernetes/kubernetes/issues/34146#issuecomment-680825790


def my_represent_none(self, data):
    return self.represent_scalar('tag:yaml.org,2002:null', 'null')


class YAML(ruamel.yaml.YAML):
    def __init__(self):
        super().__init__()
        self.default_flow_style = False
        self.preserve_quotes = True
        self.representer.add_representer(type(None), my_represent_none)
