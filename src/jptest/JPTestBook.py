from typing import Tuple
from uuid import uuid4

from testbook.client import TestbookNotebookClient

from .JPTestParams import JPTestParams


class JPTestBook:
    def __init__(self, client: TestbookNotebookClient):
        self._client = client

    @staticmethod
    def random_id(name: str) -> str:
        random_id = str(uuid4()).replace('-', '_')
        return f'_{name}_{random_id}'

    def get(self, name: str):
        name_with_id = self.random_id(name)
        return self.inject(f'{name_with_id} = {name}', name_with_id)

    def ref(self, name):
        return self._client.ref(name)

    def inject(self, code: str, *name: str):
        self._client.inject(code)

        if len(name) == 1:
            return self.ref(name[0])
        if len(name) > 1:
            return tuple(self.ref(n) for n in name)

    def track(self, fun_name: str, *parameters: Tuple[str, int]) -> JPTestParams:
        return JPTestParams(self, fun_name, *parameters)
