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
existing output that you maintain by hand. The processor stages regular file
and directory output next to the destination. It replaces the destination only
after all inputs and filters succeed. A successful `dir:PATH` run replaces
the entire tree, including removing it if no resources were selected.
Keep directory inputs and outputs separate. Devices and pipes receive output
directly. When the input is a pipeline, the processor sees the bytes it
receives. If an upstream command can fail after producing valid YAML, render
to a temporary file and check that command's exit status before processing it.

With `dir:PATH:by_namespace=false`, two resources of the same API group,
kind, and name in different namespaces map to the same file. The later
resource overwrites the earlier one. Keep namespace grouping when those
resources must remain distinct.

Use `-f remove_namespace` to remove `metadata.namespace`. The legacy
`--remove-namespace` and `--remove-tiller-labels` options in `--help` are
accepted but have no effect.

The values in `drop` predicates are parsed as YAML, so
`-f 'drop:apps/Deployment:spec/replicas=2'` matches the integer `2`. Use
YAML quotes inside the filter argument to match a string such as `"2"`.
`remove` paths address mapping keys. Traversing a scalar or a sequence
raises an error.


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
