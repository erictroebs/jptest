import asyncio
from os import PathLike
from typing import Union, List

from .JPTest import JPTest, EXECUTE_TYPE


class JPTestGet(JPTest):
    """
    decorator to use with test functions
    """

    def __init__(self, name: str = None, max_score: Union[float, int] = None, timeout: int = 120,
                 execute: EXECUTE_TYPE = None, get: Union[str, List[str]] = None):
        super().__init__(name, max_score, timeout, execute)
        self._get: List[str] = get if isinstance(get, list) else [get]

    async def execute(self, notebook: Union[str, PathLike]):
        async with self._start(notebook) as nb:
            try:
                if self._execute is not None:
                    await self._execute_recursively(nb, self._execute)

                references = (nb.ref(name) for name in self._get)
                values = await asyncio.gather(*[ref.receive() for ref in references])

                fun = self._fun(*values)
                return *(await self._execute_fun(fun)), None
            except Exception as e:
                return 0, [str(e)], e
