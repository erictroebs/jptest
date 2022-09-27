import pytest

from jptest2.notebook import Notebook


@pytest.mark.asyncio
async def test_receive():
    async with Notebook('references.ipynb') as nb:
        await nb.execute_cells('primitives', 'objects')

        nb_int = await nb.ref('nb_int').receive()
        assert nb_int == 1024

        nb_float = await nb.ref('nb_float').receive()
        assert nb_float == 5.25

        nb_str = await nb.ref('nb_str').receive()
        assert nb_str == 'text'

        nb_bool = await nb.ref('nb_bool').receive()
        assert nb_bool is True

        nb_obj = await nb.ref('nb_obj').receive()
        assert nb_obj.key == 'val'

        nb_list = await nb.ref('nb_list').receive()
        assert nb_list == [1, 'a', None, 'b']

        nb_tuple = await nb.ref('nb_tuple').receive()
        assert nb_tuple == (2, 'b')

        nb_set = await nb.ref('nb_set').receive()
        assert nb_set == {5, 3, 1}

        nb_dict = await nb.ref('nb_dict').receive()
        assert nb_dict == {
            'a': nb_obj,
            'b': 2
        }


@pytest.mark.asyncio
async def test_reference_call():
    async with Notebook('references.ipynb') as nb:
        await nb.execute_cells('create', 'objects')

        nb_fun = nb.ref('nb_swap')
        nb_a, nb_b, nb_c = nb.refs('a', 'b', 'c')

        lo_a = await nb_a.receive()
        lo_b = await nb_b.receive()
        lo_c = await nb_c.receive()

        # args: call with notebook parameters
        result = await (await nb_fun(nb_a, nb_c)).receive()
        assert result == (lo_c, lo_a)

        # args: call with local parameters
        result = await (await nb_fun(lo_a, lo_c)).receive()
        assert result == (lo_c, lo_a)

        # args: call with mixed parameters
        result = await (await nb_fun(nb_a, lo_c)).receive()
        assert result == (lo_c, lo_a)

        # kwargs: call with notebook parameter
        result = await (await nb_fun(nb_a, nb_c, replace_second=nb_b)).receive()
        assert result == (lo_b, lo_a)

        # kwargs: call with local parameter
        result = await (await nb_fun(nb_a, nb_c, replace_second=lo_b)).receive()
        assert result == (lo_b, lo_a)


@pytest.mark.asyncio
async def test_item_and_attr():
    async with Notebook('references.ipynb') as nb:
        await nb.execute_cells('objects')

        # item
        nb_dict_b = await nb.ref('nb_dict')['b'].receive()
        assert nb_dict_b == 2

        # attr
        nb_obj_key = await nb.ref('nb_obj').key.receive()
        assert nb_obj_key == 'val'

        # mixed
        nb_mixed = await nb.ref('nb_dict')['a'].key.receive()
        assert nb_mixed == 'val'


@pytest.mark.asyncio
async def test_len():
    async with Notebook('references.ipynb') as nb:
        await nb.execute_cells('objects')

        nb_list_len = await nb.ref('nb_list').len()
        assert nb_list_len == 4
