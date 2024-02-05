from abc import ABC, abstractmethod

class ObjectImporter(ABC):
    def __init__(self, bro_id):
        self.bro_id = bro_id
    
class GMNObjectImporter(ObjectImporter):
    pass

class GMWObjectImporter(ObjectImporter):
    pass

class GLDObjectImporter(ObjectImporter):
    pass

class FRDObjectImporter(ObjectImporter):
    pass
