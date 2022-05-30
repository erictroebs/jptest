import functools
from contextlib import ExitStack
from types import FunctionType, GeneratorType
from typing import List, Dict, Union, Tuple

from testbook import testbook

from .JPTestBook import JPTestBook
from .JPTestParams import JPTestParams

TRACK_TYPE = Dict[str,
                  Union[Tuple[str, int],
                        List[Tuple[str, int]]]]
EXECUTE_TYPE = Union[Tuple[str],
                     Tuple[str, str],
                     str,
                     FunctionType,
                     List['EXECUTE_TYPE'],
                     Dict[str, Union['EXECUTE_TYPE', TRACK_TYPE]]]


class JPTest(testbook):
    NOTEBOOK = None
    TESTS = []

    def __init__(self, name: str = None, max_score: float = None, execute: EXECUTE_TYPE = None):
        super().__init__(self.NOTEBOOK, execute)

        self._jtb = JPTestBook(self.client)
        self._name = name
        self._max_score = max_score

    def _prepare_recursive(self, item: EXECUTE_TYPE) -> List[JPTestParams]:
        extracted: List[JPTestParams] = []

        if isinstance(item, dict):
            with ExitStack() as stack:
                # create function wrappers
                if 'track' in item:
                    for key in item['track']:
                        if isinstance(item['track'][key], list):
                            cm = self._jtb.track(key, *item['track'][key])
                        else:
                            cm = self._jtb.track(key, item['track'][key])

                        stack.enter_context(cm)
                        extracted.append(cm)

                # execute cells
                for ep in self._prepare_recursive(item['execute']):
                    extracted.append(ep)

        elif isinstance(item, tuple):
            if len(item) == 2:
                self.client.execute_cell(slice(item[0], item[1]))
            elif len(item) == 1:
                self.client.execute_cell(item[0])
            else:
                raise ValueError('unsupported tuple length')

        elif isinstance(item, str):
            self.client.inject(item)

        elif isinstance(item, FunctionType):
            item(self.client)

        elif isinstance(item, list):
            for i in item:
                for ep in self._prepare_recursive(i):
                    extracted.append(ep)

        else:
            raise ValueError(f'unsupported parameter type {type(item)}')

        return extracted

    def __call__(self, func):
        @functools.wraps(func)
        def wrapper():
            test_score = 0.0
            test_comments = []

            with self.client.setup_kernel():
                if self.execute is None:
                    tracked_parameters = []
                else:
                    tracked_parameters = self._prepare_recursive(self.execute)

                ret_val = func(self._jtb, *tracked_parameters)
                if isinstance(ret_val, GeneratorType):
                    for value in ret_val:
                        if len(value) == 3:
                            val, score, reason = value
                        else:
                            val, score = value
                            reason = None

                        if isinstance(val, bool) and val:
                            test_score += score
                        elif isinstance(val, list) and all(list):
                            test_score += score
                        elif reason is not None:
                            test_comments.append(reason)

            return test_score, test_comments

        wrapper.patchings = [self]

        self.TESTS.append((self._name, func.__name__, self._max_score, wrapper))
        return wrapper
