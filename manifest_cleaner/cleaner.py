class Cleaner:
    def __init__(self):
        self.remove_namespace = False
        self.remove_tiller_labels = False

    def process(self, obj):
        metadata = obj['metadata']

        if self.remove_namespace:
            metadata.pop('namespace', None)

        if self.remove_tiller_labels:
            label_maps = [
                metadata.get('labels'),
                obj.get('spec', {}).get('template', {}).get('metadata', {}).get('labels'),
            ]

            for labels in label_maps:
                if labels:
                    labels.pop('chart', None)
                    labels.pop('release', None)
                    labels.pop('heritage', None)

        return obj
