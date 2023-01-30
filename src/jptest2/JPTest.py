import asyncio
from os import PathLike
from types import FunctionType
from typing import Protocol, Union, AsyncIterable, List, Awaitable, AsyncGenerator, Tuple, Callable, Iterable, Optional

import aiofiles

from .notebook import Notebook


class JPTestFunction(Protocol):
    def __call__(self, *args, **kwargs) -> Union[Awaitable, AsyncIterable]:
        ...


EXECUTE_TYPE = Union[Tuple[str],
                     Tuple[str, str],
                     str,
                     Callable,
                     PathLike,
                     List['EXECUTE_TYPE']]


class JPTest:
    """
    decorator to use with test functions
    """
    TESTS: List['JPTest'] = []
    DEFAULT_TIMEOUT = 120

    def __init__(self, name: str = None, max_score: Union[float, int] = 0, timeout: int = None,
                 execute: EXECUTE_TYPE = None, prepare_second: bool = False,
                 kernel: Optional[str] = 'python3'):
        """
        :param name: name used in the output
        :param max_score: maximum score (can be exceeded, used to calculate total score)
        :param timeout: execution timeout in seconds (default: 2 minutes)
        :param execute: cells, code and functions to execute prior to the test
        :param prepare_second: create two notebooks and use `execute` with both in parallel
        """

        self.name: str = name
        self.max_score: float = float(max_score)
        self.timeout: int = timeout or JPTest.DEFAULT_TIMEOUT
        self.prepare_second: bool = prepare_second
        self.kernel = kernel

        self._fun: JPTestFunction
        self._execute = execute if execute is not None else []

    def __call__(self, fun: JPTestFunction):
        self._fun = fun
        self.TESTS.append(self)

    @property
    def test_name(self) -> str:
        return self._fun.__name__

    def _start(self, notebook: Union[str, PathLike]):
        if self.kernel == 'python3':
            from .notebook.kernels import PythonNotebook
            return PythonNotebook(notebook, timeout=self.timeout)
        if self.kernel == 'duckdb':
            from .notebook.kernels import DuckDBNotebook
            return DuckDBNotebook(notebook)
        if self.kernel == 'sqlite':
            from .notebook.kernels import SQLiteNotebook
            return SQLiteNotebook(notebook)

        raise AssertionError(f'kernel {self.kernel} not supported')

    @staticmethod
    async def _execute_recursively(nb: Notebook, item: EXECUTE_TYPE):
        """
        :param nb: Notebook object to use
        :param item: item to execute
        :return:
        """

        # tuples
        if isinstance(item, tuple):
            if len(item) == 1:
                await nb.execute_cells(item[0])
            elif len(item) == 2:
                await nb.execute_cells(from_tag=item[0], to_tag=item[1])
            else:
                raise ValueError(f'unsupported tuple length {len(item)}')

        # string
        elif isinstance(item, str):
            await nb.execute_code(item)

        # function
        elif isinstance(item, FunctionType):
            await nb.execute_fun(item)

        # pathlike
        elif isinstance(item, PathLike):
            async with aiofiles.open(item, 'r') as file:
                file_contents = await file.read()

            await nb.execute_code(file_contents)

        # list
        elif isinstance(item, list):
            for i in item:
                await JPTest._execute_recursively(nb, i)

        # other
        else:
            raise ValueError(f'unsupported parameter type {type(item)}')

    async def _execute_fun(self, fun):
        test_score = 0.0
        test_comments = []

        if isinstance(fun, AsyncGenerator):
            async for value in fun:
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
                    raise ValueError(f'invalid yield from test {self.name}')

                if (not isinstance(val, Iterable) and val) or (isinstance(val, Iterable) and all(val)):
                    test_score += score
                    if pos_comment is not None:
                        test_comments.append(pos_comment)
                else:
                    if neg_comment is not None:
                        test_comments.append(neg_comment)

        else:
            await fun

        return test_score, test_comments

    async def execute(self, notebook: Union[str, PathLike]):
        try:
            if not self.prepare_second:
                async with self._start(notebook) as nb:
                    if self._execute is not None:
                        await self._execute_recursively(nb, self._execute)

                    fun = self._fun(nb)
                    return *(await self._execute_fun(fun)), None

            else:
                async with \
                        self._start(notebook) as left, \
                        self._start(notebook) as right:
                    if self._execute is not None:
                        await asyncio.gather(*[
                            self._execute_recursively(left, self._execute),
                            self._execute_recursively(right, self._execute)
                        ])

                    fun = self._fun(left, right)
                    return *(await self._execute_fun(fun)), None

        except Exception as e:
            return 0, [str(e)], e
