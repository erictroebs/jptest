import asyncio

import pytest

from jptest2 import PythonNotebook


@pytest.mark.asyncio
async def test_receive():
    async with PythonNotebook('references.ipynb') as nb:
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
    # receive
    async with PythonNotebook('references.ipynb') as nb:
        await nb.execute_cells('create', 'objects')

        nb_fun = nb.ref('nb_swap')
        nb_a, nb_b, nb_c = nb.refs('a', 'b', 'c')

        lo_a = await nb_a.receive()
        lo_b = await nb_b.receive()
        lo_c = await nb_c.receive()

        # args: call with PythonNotebook parameters
        result = await nb_fun(nb_a, nb_c).receive()
        assert result == (lo_c, lo_a)

        # args: call with local parameters
        result = await nb_fun(lo_a, lo_c).receive()
        assert result == (lo_c, lo_a)

        # args: call with mixed parameters
        result = await nb_fun(nb_a, lo_c).receive()
        assert result == (lo_c, lo_a)

        # kwargs: call with PythonNotebook parameter
        result = await nb_fun(nb_a, nb_c, replace_second=nb_b).receive()
        assert result == (lo_b, lo_a)

        # kwargs: call with local parameter
        result = await nb_fun(nb_a, nb_c, replace_second=lo_b).receive()
        assert result == (lo_b, lo_a)

    # execute
    async with PythonNotebook('references.ipynb') as nb:
        await nb.execute_cells('create', 'objects')

        nb_fun = nb.ref('nb_swap')
        nb_a, nb_b, nb_c = nb.refs('a', 'b', 'c')
        lo_a, lo_b, lo_c = 1, 2, 3

        # args: call with PythonNotebook parameters
        await nb_fun(nb_a, nb_c).execute()

        # args: call with local parameters
        await nb_fun(lo_a, lo_c).execute()

        # args: call with mixed parameters
        await nb_fun(nb_a, lo_c).execute()

        # kwargs: call with PythonNotebook parameter
        await nb_fun(nb_a, nb_c, replace_second=nb_b).execute()

        # kwargs: call with local parameter
        await nb_fun(nb_a, nb_c, replace_second=lo_b).execute()


@pytest.mark.asyncio
async def test_item_and_attr():
    async with PythonNotebook('references.ipynb') as nb:
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
    async with PythonNotebook('references.ipynb') as nb:
        await nb.execute_cells('objects')

        nb_list_len = await nb.ref('nb_list').len()
        assert nb_list_len == 4


@pytest.mark.asyncio
async def test_copy():
    async with PythonNotebook('references.ipynb') as nb:
        await nb.execute_cells('objects')

        # simple name
        nb_list = await nb.ref('nb_list').copy()
        await nb.execute_code('nb_list = 3.142')

        r1 = await nb_list.receive()
        assert r1 == [1, 'a', None, 'b']

        r2 = await nb.ref('nb_list').receive()
        assert r2 == 3.142

        # property
        nb_obj = await nb.ref('nb_obj').key.copy()
        await nb.execute_code('nb_obj.key = "changed"')

        r3 = await nb_obj.receive()
        assert r3 == 'val'

        r4 = await nb.ref('nb_obj').key.receive()
        assert r4 == 'changed'


@pytest.mark.asyncio
async def test_transfer_between_notebooks():
    async with \
            PythonNotebook('references.ipynb') as nb1, \
            PythonNotebook('references.ipynb') as nb2:
        await asyncio.gather(
            nb1.execute_cells('create', 'primitives'),
            nb2.execute_cells('objects')
        )

        nb1_fun = nb1.ref('nb_swap')

        # pick a var from `nb2` that is _not_ available in `nb1`
        nb1_a, nb2_obj = nb1.ref('a'), nb2.ref('nb_obj')

        result = await nb1_fun(nb1_a, nb2_obj).receive()
        assert result == (await nb2_obj.receive(), await nb1_a.receive())

        # pick a var from `nb2` that is available in `nb1`
        await nb2.execute_code('nb_int = 3072')

        nb1_a, nb2_int = nb1.ref('a'), nb2.ref('nb_int')

        result = await nb1_fun(nb1_a, nb2_int).receive()
        assert result == (await nb2_int.receive(), await nb1_a.receive())
