import functools
from contextlib import ExitStack
from types import FunctionType, GeneratorType
from typing import List, Dict, Union, Tuple, Callable, Any

from testbook import testbook

from .JPFixture import JPPreTest, JPPostTest
from .JPTestBook import JPTestBook
from .JPTestParams import JPTestParams

TRACK_TYPE = Dict[str,
                  Union[Tuple[str, int],
                        List[Tuple[str, int]]]]
EXECUTE_TYPE = Union[Tuple[str],
                     Tuple[str, str],
                     str,
                     Callable[[JPTestBook], Any],
                     List['EXECUTE_TYPE'],
                     Dict[str, Union['EXECUTE_TYPE', TRACK_TYPE]]]


class JPTest(testbook):
    """
    decorator to use with test functions
    """
    NOTEBOOK: str = None
    TESTS: List[Tuple['JPTest', Callable, Callable]] = []

    def __init__(self, name: str = None, max_score: Union[float, int] = None,
                 execute: EXECUTE_TYPE = None, timeout: int = 120,
                 **kwargs):
        """
        :param name: name used in the output
        :param max_score: maximum score (can be exceeded, used to calculate total score)
        :param execute: cells or code to execute prior to the test
        :param timeout: execution timeout in seconds (default: 2 minutes)
        :param kwargs: any named parameters are copied to the JPTestBook object
        """
        super().__init__(self.NOTEBOOK, execute, timeout=timeout)

        self.tb: JPTestBook = JPTestBook(self.client, **kwargs)
        self.name: str = name
        self.max_score: float = None if max_score is None else float(max_score)

    def _prepare_recursive(self, item: EXECUTE_TYPE) -> List[JPTestParams]:
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
                            cm = self.tb.track(key, *item['track'][key])
                        else:
                            cm = self.tb.track(key, item['track'][key])

                        stack.enter_context(cm)
                        extracted.append(cm)

                # execute cells
                for ep in self._prepare_recursive(item['execute']):
                    extracted.append(ep)

        # tuples
        elif isinstance(item, tuple):
            # two items: execute every cell from the first occurrence of the first tag
            # to the first occurrence of the second tag
            if len(item) == 2:
                self.client.execute_cell(slice(item[0], item[1]))

            # one item: execute every cell with this tag
            elif len(item) == 1:
                for idx, cell in enumerate(self.client.cells):
                    if 'tags' in cell['metadata'] and item[0] in cell['metadata']['tags']:
                        self.client.execute_cell(idx)

            else:
                raise ValueError('unsupported tuple length')

        # string
        elif isinstance(item, str):
            self.client.inject(item)

        # function
        elif isinstance(item, FunctionType):
            item(self.tb)

        # list
        elif isinstance(item, list):
            for i in item:
                for ep in self._prepare_recursive(i):
                    extracted.append(ep)

        else:
            raise ValueError(f'unsupported parameter type {type(item)}')

        return extracted

    def __call__(self, fun: Callable):
        @functools.wraps(fun)
        def wrapper():
            test_score = 0.0
            test_comments = []

            with self.client.setup_kernel():
                # pre test functions
                for pre_test in JPPreTest.FN:
                    pre_test(self.tb)

                # execution
                if self.execute is None:
                    tracked_parameters = []
                else:
                    tracked_parameters = self._prepare_recursive(self.execute)

                ret_val = fun(self.tb, *tracked_parameters)
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

                # post test functions
                for post_test in JPPostTest.FN:
                    post_test(self.tb)

            return max(0.0, test_score), test_comments

        wrapper.patchings = [self]

        self.TESTS.append((self, fun, wrapper))
        return wrapper
