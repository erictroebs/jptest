import base64

import pytest
from nbclient.exceptions import CellExecutionError

from jptest2.notebook import Notebook


def read_image(path: str) -> str:
    with open(path, 'rb') as file:
        data = file.read()
        data = base64.b64encode(data).decode('ascii')

        return data


@pytest.mark.asyncio
async def test_execute_code():
    async with Notebook('execute_code.ipynb') as nb:
        # execute result
        exec, out, err, dsp = await nb.execute_code('''
            1 + 1
            5 + 15
        ''')

        assert exec == [('text/plain', '20')]
        assert out is None
        assert err is None
        assert dsp == []

        # stdout
        exec, out, err, dsp = await nb.execute_code('''
            print(2)
            print(5)
        ''')

        assert exec == []
        assert out == '2\n5\n'
        assert err is None
        assert dsp == []

        # stderr
        exec, out, err, dsp = await nb.execute_code('''
            import sys
            print(3, file=sys.stderr)
            print(6, file=sys.stderr)
        ''')

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
        exec, out, err, dsp = await nb.execute_code('''
            from IPython.display import display, Image
            display(Image('stripes.png'))
        ''')

        assert exec == []
        assert out is None
        assert err is None
        assert dsp == [
            ('image/png', f'{read_image("stripes.png")}\n'),
            ('text/plain', '<IPython.core.display.Image object>')
        ]

        # display_data in execute_result
        exec, out, err, dsp = await nb.execute_code('''
            from IPython.display import display, Image
            Image('stripes.png')
        ''')

        assert exec == [
            ('image/png', f'{read_image("stripes.png")}\n'),
            ('text/plain', '<IPython.core.display.Image object>')
        ]
        assert out is None
        assert err is None
        assert dsp == []


@pytest.mark.asyncio
async def test_execute_all_cells():
    async with Notebook('execute_code.ipynb') as nb:
        result = await nb.execute_cells()
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
            [('text/plain', '110')],
            None,
            None,
            []
        ), (
            [('text/plain', '1110')],
            None,
            None,
            []
        )]


@pytest.mark.asyncio
async def test_execute_cells():
    async with Notebook('execute_code.ipynb') as nb:
        # only cells with tag 'task-1'
        result = await nb.execute_cells('task-1')
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
        result = await nb.execute_cells('task-2', 'task-3')
        assert result == [(
            [('text/plain', '106')],
            None,
            None,
            []
        ), (
            [('text/plain', '1106')],
            None,
            None,
            []
        )]
