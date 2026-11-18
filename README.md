# kube-manifest-processor

Cleans and structures your Kubernetes manifests


## Usage

Pass one or more manifest inputs followed by an output. A plain output path
writes a multi-document YAML file. Use `dir:PATH` to write each resource under
`<namespace>/<api-group>/<Kind>/<name>.yaml`. Resources without a namespace
use `_`, and resources in the core API group use `_core`.

For example, filter a local bundle into a fresh staging directory:

```sh
staging_dir="$(mktemp -d)" || exit 1
kube-manifest-processor \
  -f 'drop:/Namespace' \
  -f 'remove:*/*:path=metadata/labels/app.kubernetes.io\/managed-by' \
  -- bundle.yaml "dir:$staging_dir/manifests"
```

Inspect the generated manifests after a successful run before replacing any
existing output. The processor opens the output before reading inputs or
validating filters. File output truncates the destination, and `dir:PATH`
recursively removes an existing destination directory, even if processing
subsequently fails. Keep inputs outside the output and put the staged output
outside any directory passed as an input.

With `dir:PATH:by_namespace=false`, two resources of the same API group,
kind, and name in different namespaces map to the same file. The later
resource overwrites the earlier one. Keep namespace grouping when those
resources must remain distinct.

Use `-f remove_namespace` to remove `metadata.namespace`. The legacy
`--remove-namespace` and `--remove-tiller-labels` options in `--help` are
accepted but have no effect.


## Choosing YAML formatter

### PyYAML
* doesn't respect original mapping keys order

### ruamel.yaml
All issues overcomed.

### golang `sigs.k8s.io/yaml`
Used by Kubernetes.
* doesn't respect original mapping keys order (does not support MapSlice)

### golang `gopkg.in/yaml.v2`
Used by `sigs.k8s.io/yaml`. Just works. But calling golang code from Python is painful for such a small project.
