class Cleaner:
    def __init__(self):
        self.remove_namespace = False

    def process(self, obj):
        if self.remove_namespace:
            del obj['metadata']['namespace']
        return obj
