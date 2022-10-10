import pytest

from jptest2.notebook import Notebook


@pytest.mark.asyncio
async def test_ref():
    async with Notebook('references.ipynb') as nb:
        # create in notebook
        await nb.execute_cells('create')

        # get references
        a, b, c = nb.refs('a', 'b', 'c')
        nb_swap = nb.ref('nb_swap')

        # compare references
        assert await a.receive() == 'a'
        assert await b.receive() == 'b'
        assert await c.receive() == {
            'a': 1,
            'b': 2
        }
        assert await nb_swap(a, b).receive() == ('b', 'a')

        # change in notebook
        await nb.execute_cells('change')

        # compare references
        assert await a.receive() == 1
        assert await b.receive() == 'b'
        assert await c.receive() == {
            'a': 11,
            'b': 2
        }
        assert await nb_swap(a, b).receive() == 1


@pytest.mark.asyncio
async def test_get():
    async with Notebook('references.ipynb') as nb:
        # create in notebook
        await nb.execute_cells('create')

        # get references
        a, b, c = await nb.gets('a', 'b', 'c')
        nb_swap = await nb.get('nb_swap')

        # compare references
        assert await a.receive() == 'a'
        assert await b.receive() == 'b'
        assert await c.receive() == {
            'a': 1,
            'b': 2
        }
        assert await nb_swap(a, b).receive() == ('b', 'a')

        # change in notebook
        await nb.execute_cells('change')

        # compare references
        assert await a.receive() == 'a'
        assert await b.receive() == 'b'
        assert await c.receive() == {
            'a': 11,
            'b': 2
        }
        assert await nb_swap(a, b).receive() == ('b', 'a')
