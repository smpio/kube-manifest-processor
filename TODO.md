* for some reason arguments should be separated by --
* check [kube-neat](https://github.com/itaysk/kubectl-neat)
* remove_prefix should remove prefix only from namespaced objects 

# sources
* api server (kube-dump replacement)
* url (for convinience)

# filters
* native clean (from kube.js)
* remove ServiceAccount tokens (kind == 'Secret' and type == 'kubernetes.io/service-account-token')
* remove default ServiceAccount (kind == 'ServiceAccount' and name == 'default')
* remove kind == 'ConfigMap' and name == 'kube-root-ca.crt'
