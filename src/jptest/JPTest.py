import functools
from types import GeneratorType
from typing import List, Union, Tuple, Callable

from testbook import testbook

from .JPFixture import JPPreTest, JPPostTest, JPTestBook
from .JPTestBook import EXECUTE_TYPE


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
                    tracked_parameters = self.tb.execute(self.execute)

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
