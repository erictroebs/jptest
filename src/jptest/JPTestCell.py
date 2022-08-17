from typing import List

from testbook.client import TestbookNotebookClient


class JPTestCell:
    @staticmethod
    def from_client(client: TestbookNotebookClient) -> List['JPTestCell']:
        return [JPTestCell(client, idx) for idx in range(len(client.cells))]

    def __init__(self, client: TestbookNotebookClient, idx: int):
        self._client: TestbookNotebookClient = client
        self._idx: int = idx

    @property
    def tags(self) -> List[str]:
        cell = self._client.cells[self._idx]

        if 'tags' not in cell['metadata']:
            return []
        else:
            return cell['metadata']['tags']

    def execute(self):
        self._client.execute_cell(self._idx)
