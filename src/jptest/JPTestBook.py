from typing import Tuple
from uuid import uuid4

from testbook.client import TestbookNotebookClient

from .JPTestParams import JPTestParams


class JPTestBook:
    """
    main class for notebook interaction
    """
    def __init__(self, client: TestbookNotebookClient, **kwargs):
        self._client = client

        for key, value in kwargs.items():
            setattr(self, key, value)

    @staticmethod
    def random_id(name: str) -> str:
        random_id = str(uuid4()).replace('-', '_')
        return f'_{name}_{random_id}'

    def get(self, *name: str):
        """
        like `ref`, but copy to a name with a random suffix before

        :param name: object or function name(s)
        :return: reference or a tuple of references depending on parameters
        """
        if len(name) == 1:
            name_with_id = self.random_id(name[0])
            return self.inject(f'{name_with_id} = {name[0]}', name_with_id)
        else:
            return tuple(self.get(n) for n in name)

    def ref(self, *name):
        """
        get a reference to an object or a function

        :param name: object or function name(s)
        :return: reference or a tuple of references depending on parameters
        """
        if len(name) == 1:
            return self._client.ref(name[0])
        else:
            return tuple(self.get(n) for n in name)

    def inject(self, code: str, *name: str):
        """
        inject code into notebook and return a reference

        :param code: code to inject
        :param name: object or function name(s)
        :return: reference or a tuple of references depending on parameters
        """
        self._client.inject(code)
        return self.ref(*name)

    def track(self, fun_name: str, *parameters: Tuple[str, int]) -> JPTestParams:
        """
        wrap a function to track calls

        :param fun_name: function name
        :param parameters: list of parameters to track
        :return: instance of JPTestParams
        """
        return JPTestParams(self, fun_name, *parameters)
