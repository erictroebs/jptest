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

    def is_from(self, nb: Notebook):
        return nb == self._nb

    async def copy(self, name: str = None) -> "NotebookReference":
        """
        copy object to a new name and return a new reference

        :param name: the new name. random one is used if not provided
        :return: NotebookReference
        """
        if name is None:
            name = randomize_name(self.name)

        await self._nb.execute_code(f'{name} = {await self._resolve()}')
        return NotebookReference(self._nb, name)

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
        """
        execute the underlying statement in the notebook context

        :return: inserted notebook cell
        """
        return await self._nb.execute_code(f'''
            import pickle
            {await self._resolve()}
        ''')

    @staticmethod
    async def execute_many(*references: "NotebookReference"):
        return await asyncio.gather(*[ref.execute() for ref in references])

    async def receive(self, deserialize: bool = True) -> Any:
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

            value = base64.b64decode(value.encode('ascii'))

            if deserialize:
                value = pickle.loads(value)

            return value

    def __await__(self):
        return self.receive().__await__()

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
        # transfer references if not from same notebook
        if isinstance(arg, NotebookReference):
            if not arg.is_from(self._nb):
                arg = await self._nb.store(arg)
        # store local values in notebook
        else:
            arg = await self._nb.store(arg)

        return await arg._resolve()

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
