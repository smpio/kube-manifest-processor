# kube-manifest-processor

Cleans and structures your Kubernetes manifests


## Usage

See `kube-manifest-processor --help`.


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
