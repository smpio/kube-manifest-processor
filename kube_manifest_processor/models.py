from dataclasses import dataclass


def decorate_object(obj):
    group_version = obj['apiVersion']
    if group_version == 'v1':
        obj._gvk = GroupVersionKind('', 'v1', obj['kind'])
    else:
        group, version = group_version.split('/', maxsplit=1)
        obj._gvk = GroupVersionKind(group, version, obj['kind'])
    return obj


@dataclass(frozen=True)
class GroupVersionKind:
    group: str
    version: str
    kind: str
