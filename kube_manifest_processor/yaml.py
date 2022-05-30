import io

import ruamel.yaml

# see https://github.com/kubernetes/kubernetes/issues/34146#issuecomment-680825790


def my_represent_none(self, data):
    return self.represent_scalar('tag:yaml.org,2002:null', 'null')


class YAML(ruamel.yaml.YAML):
    def __init__(self):
        super().__init__()
        self.representer.add_representer(type(None), my_represent_none)


def load(stream):
    return YAML().load(stream)


def load_all(stream):
    return YAML().load_all(stream)


def dump(obj, fp):
    YAML().dump(obj, fp)


def dumps(obj, bytes=False):
    if bytes:
        out = io.BytesIO()
    else:
        out = io.StringIO()
    dump(obj, out)
    return out.getvalue()
