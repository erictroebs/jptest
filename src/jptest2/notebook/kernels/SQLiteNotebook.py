import re
from os import PathLike
from typing import Union, Optional

import aiosqlite

from .. import Notebook
from ..NotebookCell import NotebookCell


class SQLiteNotebook(Notebook):
    def __init__(self, notebook: Union[str, PathLike], execute: bool = False):
        super().__init__(notebook, self.__execute_cell, execute)
        self.db: Optional

    async def __aenter__(self) -> "Notebook":
        self.db = aiosqlite.connect(':memory:')

        await self.db.__aenter__()
        await super().__aenter__()

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await super().__aexit__(exc_type, exc_val, exc_tb)
        await self.db.__aexit__(exc_type, exc_val, exc_tb)

    async def __execute_cell(self, cell: NotebookCell):
        statements = list(filter(lambda x: x, re.split(r';$', cell.source, flags=re.MULTILINE)))
        last_index = len(statements) - 1

        for i, statement in enumerate(statements):
            async with self.db.execute(statement) as cursor:
                if i == last_index:
                    return await cursor.fetchall()
