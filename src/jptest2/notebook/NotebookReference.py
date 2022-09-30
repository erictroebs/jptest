import base64
import pickle
from typing import Any

from . import Notebook
from .util import randomize_name


class NotebookReference:
    """
    represents references to object in notebook
    """

    def __init__(self, nb: Notebook, name: str):
        self._nb: Notebook = nb
        self._name: str = name

    @property
    def name(self) -> str:
        return self._name

    async def copy(self) -> "NotebookReference":
        """
        copy object to a random name and return a new reference

        :return: NotebookReference
        """
        random_name = randomize_name(self.name)
        await self._nb.execute_code(f'{random_name} = {self.name}')

        return NotebookReference(self._nb, random_name)

    @staticmethod
    def _encode(var):
        if isinstance(var, NotebookReference):
            return var.name
        else:
            val = pickle.dumps(var)
            return f'pickle.loads({val})'

    async def __call__(self, *args, **kwargs) -> "NotebookReference":
        """
        call function in notebook context

        :param args:
        :param kwargs:
        :return: NotebookReference to result
        """
        # encode parameters
        call_args = []

        for v in args:
            call_args.append(self._encode(v))
        for k, v in kwargs.items():
            e = self._encode(v)
            call_args.append(f'{k}={e}')

        call_str = ',\n                '.join(call_args)

        # execute
        result_name = randomize_name('result')

        await self._nb.execute_code(f'''
            import pickle
            {result_name} = {self.name}(
                {call_str}
            )
        ''')

        # return result
        return await self._nb.get(result_name)

    async def receive(self) -> Any:
        """
        serialize, transfer and deserialize referenced object from notebook context

        :return: value
        """
        result, o, e, p = (await self._nb.execute_code(f'''
            import pickle, base64
            base64.b64encode(pickle.dumps({self.name})).decode('ascii')
        ''')).output()

        for mime, value in result:
            if mime != 'text/plain':
                continue

            result_value = pickle.loads(base64.b64decode(value.encode('ascii')))
            return result_value

    def __getitem__(self, key) -> "NotebookReference":
        val = pickle.dumps(key)
        return NotebookReference(self._nb, f'{self.name}[pickle.loads({val})]')

    def __getattr__(self, key) -> "NotebookReference":
        return NotebookReference(self._nb, f'{self.name}.{key}')

    async def len(self) -> int:
        """
        receive length of referenced object

        :return: `len(obj)`
        """
        return await NotebookReference(self._nb, f'len({self.name})').receive()
