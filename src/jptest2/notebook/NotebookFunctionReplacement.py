from typing import Callable

from . import Notebook
from . import NotebookReference


class NotebookFunctionReplacement:
    def __init__(self, nb: Notebook, fun_name: str, replacement: Callable):
        self._nb: Notebook = nb
        self._fun_name = fun_name
        self._replacement: Callable = replacement

    async def __aenter__(self) -> "NotebookFunctionReplacement":
        """
        replace function with replacement

        :return: self
        """
        self._backup: NotebookReference = await self._nb.get(self._fun_name)
        injected = await (await self._nb.inject_fun(self._replacement)).copy()

        await self._nb.execute_code(f'''
            {self._fun_name} = {injected.name}
        ''')

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        replace replacement with backup

        :param exc_type:
        :param exc_val:
        :param exc_tb:
        :return:
        """
        await self._nb.execute_code(f'''
            {self._fun_name} = {self._backup.name}
        ''')
