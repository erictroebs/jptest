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

    def __init__(self, name: str = None, max_score: Union[float, int] = None, execute: EXECUTE_TYPE = None):
        super().__init__(self.NOTEBOOK, execute)

        self._jtb: JPTestBook = JPTestBook(self.client)
        self._name: str = name
        self._max_score: float = float(max_score)

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
                        if len(value) == 2:
                            val, score = value
                            pos_comment = None
                            neg_comment = None
                        elif len(value) == 3:
                            val, score, neg_comment = value
                            pos_comment = None
                        elif len(value) == 4:
                            val, score, neg_comment, pos_comment = value
                        else:
                            raise ValueError('invalid yield from test')

                        if (isinstance(val, bool) and val) or (isinstance(val, list) and all(val)):
                            test_score += score
                            if pos_comment is not None:
                                test_comments.append(pos_comment)
                        elif neg_comment is not None:
                            test_comments.append(neg_comment)

            return test_score, test_comments

        wrapper.patchings = [self]

        self.TESTS.append((self._name, func.__name__, self._max_score, wrapper))
        return wrapper
