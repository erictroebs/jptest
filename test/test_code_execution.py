import base64

import pytest
from nbclient.exceptions import CellExecutionError

from jptest2 import PythonNotebook


def read_image(path: str) -> str:
    with open(path, 'rb') as file:
        data = file.read()
        data = base64.b64encode(data).decode('ascii')

        return data


@pytest.mark.asyncio
async def test_execute_code():
    async with PythonNotebook('execute_code.ipynb') as nb:
        # execute result
        exec, out, err, dsp = (await nb.execute_code('''
            1 + 1
            5 + 15
        ''')).output()

        assert exec == [('text/plain', '20')]
        assert out is None
        assert err is None
        assert dsp == []

        # stdout
        exec, out, err, dsp = (await nb.execute_code('''
            print(2)
            print(5)
        ''')).output()

        assert exec == []
        assert out == '2\n5\n'
        assert err is None
        assert dsp == []

        # stderr
        exec, out, err, dsp = (await nb.execute_code('''
            import sys
            print(3, file=sys.stderr)
            print(6, file=sys.stderr)
        ''')).output()

        assert exec == []
        assert out is None
        assert err == '3\n6\n'
        assert dsp == []

        # exception
        with pytest.raises(CellExecutionError):
            await nb.execute_code('''
                assert 1 == 2
            ''')

        # display data
        exec, out, err, dsp = (await nb.execute_code('''
            from IPython.display import display, Image
            display(Image('stripes.png'))
        ''')).output()

        assert exec == []
        assert out is None
        assert err is None
        assert dsp == [
            ('image/png', f'{read_image("stripes.png")}\n'),
            ('text/plain', '<IPython.core.display.Image object>')
        ]

        # display_data in execute_result
        exec, out, err, dsp = (await nb.execute_code('''
            from IPython.display import display, Image
            Image('stripes.png')
        ''')).output()

        assert exec == [
            ('image/png', f'{read_image("stripes.png")}\n'),
            ('text/plain', '<IPython.core.display.Image object>')
        ]
        assert out is None
        assert err is None
        assert dsp == []


@pytest.mark.asyncio
async def test_store():
    async with \
            PythonNotebook('execute_code.ipynb') as nb, \
            PythonNotebook('execute_code.ipynb') as nb2:
        # store
        val = {
            'a': 1,
            'b': [2, 'c']
        }
        ref = await nb.store(val, 'new_value')
        assert ref.name == 'new_value' and await ref.receive() == val

        # stores
        val1 = [1, 2, 3]
        val2 = {'ex': 'ample'}

        ref1, ref2 = await nb.stores(v1=val1, v2=val2)
        assert await ref1.receive() == val1
        assert await ref2.receive() == val2

        # store reference
        ref3 = await nb.store(ref1)
        assert await ref3.receive() == val1

        ref4 = await nb.store(ref2, 'custom_name')
        assert ref4.name == 'custom_name' and await ref4.receive() == val2

        # store reference from second notebook
        val3 = [5, 4, 3, 2, 1]
        ref5 = await nb2.store(val3)

        ref6 = await nb.store(ref5)
        assert await ref6.receive() == val3


@pytest.mark.asyncio
async def test_execute_all_cells():
    async with PythonNotebook('execute_code.ipynb') as nb:
        cells = await nb.execute_cells()
        assert len(cells) == 10

        result = [c.output() for c in cells]
        assert result == [(
            [],
            None,
            None,
            []
        ), (
            [('text/plain', '6')],
            None,
            None,
            []
        ), (
            [('image/png', f'{read_image("stripes.png")}\n'), ('text/plain', '<IPython.core.display.Image object>')],
            None,
            None,
            []
        ), (
            [('text/plain', '106')],
            None,
            None,
            []
        ), (
            [('text/plain', '111')],
            None,
            None,
            []
        ), (
            [('text/plain', '115')],
            None,
            None,
            []
        ), (
            [('text/plain', '1115')],
            None,
            None,
            []
        ), (
            [('text/plain', '200')],
            None,
            None,
            []
        ), (
            [('text/plain', '201')],
            None,
            None,
            []
        ), (
            [('text/plain', '300')],
            None,
            None,
            []
        )]


@pytest.mark.asyncio
async def test_execute_cells_by_tag():
    async with PythonNotebook('execute_code.ipynb') as nb:
        # only cells with tag 'task-1'
        cells = await nb.execute_cells('task-1')
        assert len(cells) == 2

        result = [c.output() for c in cells]

        assert result == [(
            [('text/plain', '6')],
            None,
            None,
            []
        ), (
            [('text/plain', '10')],
            None,
            None,
            []
        )]

        # only cells with tag `task-2` and `task-3`
        cells = await nb.execute_cells('task-2', 'task-3')
        assert len(cells) == 3

        result = [c.output() for c in cells]

        assert result == [(
            [('text/plain', '106')],
            None,
            None,
            []
        ), (
            [('text/plain', '111')],
            None,
            None,
            []
        ), (
            [('text/plain', '1111')],
            None,
            None,
            []
        )]


@pytest.mark.asyncio
async def test_execute_cells_from_to():
    async with PythonNotebook('execute_code.ipynb') as nb:
        cells = await nb.execute_cells(from_tag='task-2', to_tag='task-4')
        assert len(cells) == 5

        result = [c.output() for c in cells]

        assert result == [(
            [('text/plain', '106')],
            None,
            None,
            []
        ), (
            [('text/plain', '111')],
            None,
            None,
            []
        ), (
            [('text/plain', '115')],
            None,
            None,
            []
        ), (
            [('text/plain', '1115')],
            None,
            None,
            []
        ), (
            [('text/plain', '200')],
            None,
            None,
            []
        )]


@pytest.mark.asyncio
async def test_execute_cells_mixed():
    async with PythonNotebook('execute_code.ipynb') as nb:
        cells = await nb.execute_cells('task-2', 'task-3', from_tag='task-2', to_tag='task-4')
        assert len(cells) == 3

        result = [c.output() for c in cells]

        assert result == [(
            [('text/plain', '106')],
            None,
            None,
            []
        ), (
            [('text/plain', '111')],
            None,
            None,
            []
        ), (
            [('text/plain', '1111')],
            None,
            None,
            []
        )]
