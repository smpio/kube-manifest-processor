from ruamel.yaml import YAML


def my_represent_none(self, data):
    return self.represent_scalar('tag:yaml.org,2002:null', 'null')


yaml = YAML()
yaml.default_flow_style = False
yaml.preserve_quotes = True
yaml.representer.add_representer(type(None), my_represent_none)
