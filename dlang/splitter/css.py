import re

class Split():
    def __init__(self, content: str):
        self.splitted_content = list(map(lambda sc: (sc.count("{") > 0 and sc + "}") or None, content.split("}")))