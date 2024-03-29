import io

import ruamel.yaml
import ruamel.yaml.scalarstring

# see https://github.com/kubernetes/kubernetes/issues/34146#issuecomment-680825790

BOOL_SCALARS = set('y|Y|yes|Yes|YES|n|N|no|No|NO|true|True|TRUE|false|False|FALSE|on|On|ON|off|Off|OFF'.split('|'))


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
                if self.event.tag == 'tag:yaml.org,2002:str' and self.event.value in BOOL_SCALARS:
                    # we are working in YAML 1.2, but Kubernetes still interprets yes/no as bools
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
