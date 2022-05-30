import io

import ruamel.yaml
import ruamel.yaml.scalarstring

# see https://github.com/kubernetes/kubernetes/issues/34146#issuecomment-680825790


def my_represent_none(self, data):
    return self.represent_scalar('tag:yaml.org,2002:null', 'null')


class YAML(ruamel.yaml.YAML):
    def __init__(self):
        super().__init__()
        self.default_style = None
        self.default_flow_style = False

        self.representer.add_representer(type(None), my_represent_none)

        class Emitter(self.Emitter):
            def choose_scalar_style(self):
                style = super().choose_scalar_style()
                if style == "'" and '"' not in self.event.value:
                    style = '"'
                return style

        self.Emitter = Emitter


def load(stream):
    return YAML().load(stream)


def load_all(stream):
    return YAML().load_all(stream)


def dump(obj, fp):
    """WARNING: can mutate obj"""

    ruamel.yaml.scalarstring.walk_tree(obj)
    YAML().dump(obj, fp)


def dumps(obj, bytes=False):
    """WARNING: can mutate obj"""

    if bytes:
        out = io.BytesIO()
    else:
        out = io.StringIO()
    dump(obj, out)
    return out.getvalue()
