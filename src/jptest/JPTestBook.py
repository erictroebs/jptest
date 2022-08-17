from contextlib import ExitStack
from types import FunctionType
from typing import List, Dict, Union, Callable, Any
from typing import Tuple
from uuid import uuid4

from testbook.client import TestbookNotebookClient

from .JPTestCell import JPTestCell
from .JPTestParams import JPTestParams

TRACK_TYPE = Dict[str,
                  Union[Tuple[str, int],
                        List[Tuple[str, int]]]]
EXECUTE_TYPE = Union[Tuple[str],
                     Tuple[str, str],
                     str,
                     Callable[['JPTestBook'], Any],
                     List['EXECUTE_TYPE'],
                     Dict[str, Union['EXECUTE_TYPE', TRACK_TYPE]]]


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

    def cells(self, *item: str) -> List[JPTestCell]:
        cells = JPTestCell.from_client(self._client)

        # no items: all cells
        if len(item) == 0:
            return cells

        # one item: every cell with this tag
        elif len(item) == 1:
            return [cell for cell in cells if item[0] in cell.tags]

        # two items: every cell from the first occurrence of the first tag to
        # the first occurrence of the second tag
        if len(item) == 2:
            result = []

            start = False
            for cell in cells:
                if item[1] in cell.tags:
                    break

                if item[0] in cell.tags:
                    start = True
                if start:
                    result.append(cell)

            return result

        else:
            raise ValueError('unsupported tuple length')

    def execute(self, item: EXECUTE_TYPE) -> List[JPTestParams]:
        """
        :param item: item to execute
        :return: a list of JPTestParams if any track directives were used
        """
        extracted: List[JPTestParams] = []

        # dictionaries
        if isinstance(item, dict):
            with ExitStack() as stack:
                # create function wrappers
                if 'track' in item:
                    for key in item['track']:
                        if isinstance(item['track'][key], list):
                            cm = self.track(key, *item['track'][key])
                        else:
                            cm = self.track(key, item['track'][key])

                        stack.enter_context(cm)
                        extracted.append(cm)

                # execute cells
                for ep in self.execute(item['execute']):
                    extracted.append(ep)

        # tuples
        elif isinstance(item, tuple):
            for cell in self.cells(*item):
                cell.execute()

        # string
        elif isinstance(item, str):
            self._client.inject(item)

        # function
        elif isinstance(item, FunctionType):
            item(self)

        # list
        elif isinstance(item, list):
            for i in item:
                for ep in self.execute(i):
                    extracted.append(ep)

        else:
            raise ValueError(f'unsupported parameter type {type(item)}')

        return extracted
