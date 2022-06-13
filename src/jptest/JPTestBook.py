from typing import Tuple
from uuid import uuid4

from testbook.client import TestbookNotebookClient

from .JPTestParams import JPTestParams


class JPTestBook:
    def __init__(self, client: TestbookNotebookClient, **kwargs):
        self._client = client

        for key, value in kwargs.items():
            setattr(self, key, value)

    @staticmethod
    def random_id(name: str) -> str:
        random_id = str(uuid4()).replace('-', '_')
        return f'_{name}_{random_id}'

    def get(self, *name: str):
        if len(name) == 1:
            name_with_id = self.random_id(name[0])
            return self.inject(f'{name_with_id} = {name[0]}', name_with_id)
        else:
            return tuple(self.get(n) for n in name)

    def ref(self, *name):
        if len(name) == 1:
            return self._client.ref(name[0])
        else:
            return tuple(self.get(n) for n in name)

    def inject(self, code: str, *name: str):
        self._client.inject(code)
        return self.ref(*name)

    def track(self, fun_name: str, *parameters: Tuple[str, int]) -> JPTestParams:
        return JPTestParams(self, fun_name, *parameters)
