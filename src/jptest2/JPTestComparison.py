import asyncio
from os import PathLike
from typing import Union, List, Optional

from .JPTest import JPTest, EXECUTE_TYPE
from .notebook.kernels import PythonNotebook


class JPTestComparison(JPTest):
    """
    decorator to use with test functions
    """

    def __init__(self, name: str = None, max_score: Union[float, int] = None, timeout: int = 120,
                 prepare: EXECUTE_TYPE = None, execute_left: EXECUTE_TYPE = None, execute_right: EXECUTE_TYPE = None,
                 hold_left: Union[str, List[str]] = None, hold_right: Union[str, List[str]] = None):
        super().__init__(name, max_score, timeout, prepare)

        self._execute_left: EXECUTE_TYPE = execute_left if execute_left is not None else []
        self._execute_right: EXECUTE_TYPE = execute_right if execute_right is not None else []
        self._hold_left: Optional[Union[str, List[str]]] = hold_left
        self._hold_right: Optional[Union[str, List[str]]] = hold_right

    async def __prepare(self, nb: PythonNotebook, prepare: EXECUTE_TYPE, execute: EXECUTE_TYPE, hold: List[str]):
        await self._execute_recursively(nb, prepare)
        await self._execute_recursively(nb, execute)

        refs = nb.refs(*hold)
        vals = await asyncio.gather(*[ref.receive() for ref in refs])

        return vals

    async def execute(self, notebook: Union[str, PathLike]):
        async with \
                self._start(notebook) as left, \
                self._start(notebook) as right:
            # hold
            hold_left = self._hold_left if isinstance(self._hold_left, list) else [self._hold_left]
            hold_right = self._hold_right if isinstance(self._hold_right, list) else [self._hold_right]

            # prepare and hold
            try:
                result = await asyncio.gather(*[
                    self.__prepare(left, self._execute, self._execute_left, hold_left),
                    self.__prepare(right, self._execute, self._execute_right, hold_right)
                ])

                fun = self._fun(*result[0], *result[1])
                return *(await self._execute_fun(fun)), None
            except Exception as e:
                return 0, [str(e)], e
