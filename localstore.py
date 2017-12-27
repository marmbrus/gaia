import json

class LocalStore:
    def __init__(self, filePath):
        self.filePath = filePath
    
    def write(self, data):
        with open(self.filePath, "a") as f:
            for line in data:
                f.write(json.dumps(line))
                f.write("\n")