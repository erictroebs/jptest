from typing import List


class NotebookError(Exception):
    def __init__(self, name: str, value: str, traceback: List[str]):
        self.name = name
        self.value = value
        self.traceback = traceback
