import urllib.parse
from ruamel.yaml.comments import CommentedMap

import requests


class ApiServerReader:
    def __init__(self, url):
        url_parts = urllib.parse.urlparse(url)
        qsl = urllib.parse.parse_qsl(url_parts.query)
        q = dict(qsl)
        self.namespace = q.get('namespace')
        if self.namespace:
            qsl = [(k, v) for k, v in qsl if k != 'namespace']
            url_parts = url_parts._replace(query=urllib.parse.urlencode(qsl))
            url = urllib.parse.urlunparse(url_parts)
        self.session = requests.Session()
        self.session.headers = {
            'Accept': 'application/json',
        }
        self.base_url = url

    def __iter__(self):
        for resource in self.discover():
            if self.namespace and not resource['namespaced']:
                continue
            for obj in self.get_resource(resource):
                obj['apiVersion'] = resource['apiVersion']
                obj['kind'] = resource['kind']
                obj.move_to_end('kind', last=False)
                obj.move_to_end('apiVersion', last=False)
                yield obj

    def discover(self):
        api_group_list = self.get('/apis/')
        api_groups = api_group_list['groups']

        # remove deprecated group
        api_groups = [g for g in api_groups if g['preferredVersion']['groupVersion'] != 'extensions/v1beta1']

        # add core "v1" API group
        core_api_group_version = {
            'groupVersion': 'v1',
            'version': 'v1',
        }
        core_api_group = {
            'name': '',
            'preferredVersion': core_api_group_version,
            'versions': [core_api_group_version],
        }
        api_groups = [core_api_group] + api_groups

        # discover all versions (some resources can be old version only)
        for g in api_groups:
            for v in g['versions']:
                if g['preferredVersion']['version'] == v['version']:
                    g['preferredVersion'] = v
                resources = self.get_group_version(v['groupVersion'])['resources']
                resources = [r for r in resources if '/' not in r['name']]  # ignore subresources
                resources = [r for r in resources if 'list' in r['verbs']]  # ignore non-listable
                v['resources'] = resources

        # first we assume that resources of latest version are best
        for g in api_groups:
            g['bestResources'] = {}
            for v in g['versions']:
                for r in v['resources']:
                    r['apiVersion'] = v['groupVersion']
                    g['bestResources'][r['kind']] = r

        # if there is preferred version of resource, use it
        for g in api_groups:
            for r in g['preferredVersion']['resources']:
                g['bestResources'][r['kind']] = r

        for g in api_groups:
            for resource in g['bestResources'].values():
                yield resource

    def get(self, uri, params=None):
        url = urllib.parse.urljoin(self.base_url, uri)
        resp = self.session.get(url, params=params)
        resp.raise_for_status()
        return resp.json(object_pairs_hook=CommentedMap)

    def get_list(self, uri):
        params = {}
        while True:
            data = self.get(uri, params)
            yield from data['items']
            continue_token = data.get('metadata', {}).get('continue')
            if not continue_token:
                break
            params = {
                'continue': continue_token,
            }

    def get_group_version(self, api_group_version):
        return self.get(get_api_uri(api_group_version))

    def get_resource(self, resource):
        uri = get_api_uri(resource['apiVersion'])
        if resource['namespaced'] and self.namespace:
            uri += '/namespaces/' + self.namespace
        uri += '/' + resource['name']
        return self.get_list(uri)


def get_api_uri(api_group_version):
    if api_group_version == 'v1':
        return '/api/v1'
    else:
        return '/apis/' + api_group_version
