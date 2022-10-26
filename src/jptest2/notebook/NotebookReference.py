import asyncio
import base64
import pickle
from typing import Any, Union

from . import Notebook, NotebookCell
from .util import randomize_name


class NotebookReference:
    """
    represents references to object in notebook
    """

    def __init__(self, parent, name: str = None):
        self._parent: Union[Notebook, NotebookReference] = parent
        self._name: str = name

    @property
    def _nb(self) -> Notebook:
        if isinstance(self._parent, NotebookReference):
            return self._parent._nb
        else:
            return self._parent

    @property
    def name(self) -> str:
        if self._name is None:
            return self._parent.name
        else:
            return self._name

    async def _resolve(self) -> str:
        return self._name

    async def copy(self) -> "NotebookReference":
        """
        copy object to a random name and return a new reference

        :return: NotebookReference
        """
        random_name = randomize_name(self.name)
        await self._nb.execute_code(f'{random_name} = {await self._resolve()}')

        return NotebookReference(self._nb, random_name)

    def __getitem__(self, key) -> "NotebookItemReference":
        return NotebookItemReference(self, key)

    def __getattr__(self, key) -> "NotebookAttributeReference":
        return NotebookAttributeReference(self, key)

    def __call__(self, *args, **kwargs) -> "NotebookCallReference":
        """
        call function in notebook context

        :param args:
        :param kwargs:
        :return: NotebookReference to result
        """
        return NotebookCallReference(self, *args, **kwargs)

    async def len(self) -> int:
        """
        receive length of referenced object

        :return: `len(obj)`
        """
        return await self._nb.ref(f'len({await self._resolve()})').receive()

    async def execute(self) -> NotebookCell:
        return await self._nb.execute_code(f'''
            import pickle
            {await self._resolve()}
        ''')

    @staticmethod
    async def execute_many(*references: "NotebookReference"):
        return await asyncio.gather(*[ref.execute() for ref in references])

    async def receive(self) -> Any:
        """
        serialize, transfer and deserialize referenced object from notebook context

        :return: value
        """
        result, o, e, p = (await self._nb.execute_code(f'''
            import pickle, base64
            base64.b64encode(pickle.dumps({await self._resolve()})).decode('ascii')
        ''')).output()

        for mime, value in result:
            if mime != 'text/plain':
                continue

            result_value = pickle.loads(base64.b64decode(value.encode('ascii')))
            return result_value

    @staticmethod
    async def receive_many(*references: "NotebookReference"):
        return await asyncio.gather(*[ref.receive() for ref in references])


class NotebookItemReference(NotebookReference):
    def __init__(self, parent, key: Any):
        super().__init__(parent)
        self._key: Any = key

    async def _encode(self):
        return pickle.dumps(self._key)

    async def _resolve(self) -> str:
        val, key = await asyncio.gather(
            self._parent._resolve(),
            self._encode()
        )

        return f'{val}[pickle.loads({key})]'


class NotebookAttributeReference(NotebookReference):
    def __init__(self, parent, key: str):
        super().__init__(parent)
        self._key: str = key

    async def _resolve(self) -> str:
        val = await self._parent._resolve()
        return f'{val}.{self._key}'


class NotebookCallReference(NotebookReference):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent)
        self._args = args
        self._kwargs = kwargs

    async def _encode_arg(self, arg) -> str:
        if isinstance(arg, NotebookReference):
            if arg._nb == self._nb:
                return await arg._resolve()
            else:
                arg = await arg.receive()

        val = pickle.dumps(arg)
        return f'pickle.loads({val})'

    async def _encode_kwarg(self, key: str, arg) -> str:
        val = await self._encode_arg(arg)
        return f'{key}={val}'

    async def _resolve(self) -> str:
        # collect parameters
        call_args = []

        for v in self._args:
            call_args.append(self._encode_arg(v))
        for k, v in self._kwargs.items():
            call_args.append(self._encode_kwarg(k, v))

        # create parameter string and return reference
        parent, *call_args = await asyncio.gather(self._parent._resolve(), *call_args)

        call_str = ',\n                '.join(call_args)
        return f'{parent}({call_str})'
