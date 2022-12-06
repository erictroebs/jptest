import asyncio
import re
from concurrent.futures import ThreadPoolExecutor
from os import PathLike
from typing import Union, List

import duckdb

from .. import Notebook
from ..NotebookCell import NotebookCell


class DuckDBNotebook(Notebook):
    def __init__(self, notebook: Union[str, PathLike], execute: bool = False, executor: ThreadPoolExecutor = None):
        super().__init__(notebook, self.__execute_cell, execute)

        self.db: duckdb.DuckDBPyConnection
        self.executor: ThreadPoolExecutor

        if executor is None:
            self.executor = ThreadPoolExecutor(max_workers=1)
        else:
            self.executor = executor

    async def __aenter__(self) -> "Notebook":
        self.db: duckdb.DuckDBPyConnection = duckdb.connect(':memory:')

        self.db.__enter__()
        await super().__aenter__()

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await super().__aexit__(exc_type, exc_val, exc_tb)
        self.db.__exit__(exc_type, exc_val, exc_tb)

    def _execute_and_fetch(self, statement: str, fetch: bool) -> List:
        with self.db.cursor() as cursor:
            cursor.execute(statement)

            if fetch:
                return cursor.fetchall()

    async def __execute_cell(self, cell: NotebookCell):
        statements = list(filter(lambda x: x.strip(), re.split(r';$', cell.source, flags=re.MULTILINE)))
        last_index = len(statements) - 1

        for i, statement in enumerate(statements):
            if i == last_index:
                return await asyncio.get_event_loop().run_in_executor(
                    self.executor,
                    self._execute_and_fetch, statement, True
                )
            else:
                await asyncio.get_event_loop().run_in_executor(
                    self.executor,
                    self._execute_and_fetch, statement, False
                )
