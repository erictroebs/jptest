import pytest

from jptest2.notebook import Notebook


@pytest.mark.asyncio
async def test_replace_function():
    def local_fun(_, b):
        return b

    async with Notebook('functions.ipynb') as nb:
        # execute cell with function definition
        await nb.execute_cells('definition')

        # replace function
        async with nb.replace_fun('nb_fun', local_fun):
            # compare results
            (result, *_), *_ = await nb.execute_cells('execution')
            assert any([val == '10' for _, val in result])

            await nb.execute_cells('store')
            result = await nb.ref('result').receive()
            assert result == 110

        # get results again after backup was restored
        (result, *_), *_ = await nb.execute_cells('execution')
        assert any([val == '5' for _, val in result])

        await nb.execute_cells('store')
        result = await nb.ref('result').receive()
        assert result == 105
