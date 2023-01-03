import pytest

from jptest2 import PythonNotebook


@pytest.mark.asyncio
async def test_track_function():
    async with PythonNotebook('functions.ipynb') as nb:
        # execute function definition
        await nb.execute_cells('definition')

        # track function `nb_fun`
        async with nb.track_fun('nb_fun', all_parameters=True, return_values=True) as track:
            await nb.execute_cells('more-calls')

        calls = await track.receive()
        assert len(calls) == 8

        assert calls[0].parameters == [('a', 148), ('b', 116)]
        assert calls[1].parameters == [('a', '179'), ('b', '155')]
        assert calls[2].parameters == [('a', 175.25), ('b', 143.5)]
        assert calls[3].parameters == [('a', True), ('b', False)]
        assert calls[4].parameters == [('a', [5, 3, 1]), ('b', [2, 4, 6])]
        assert calls[5].parameters == [('a', None), ('b', 2048)]
        assert calls[6].parameters == [('a', 5), ('b', 2)]
        assert calls[7].parameters == [('a', 1), ('b', 2)]

        assert calls[0].return_value == 148
        assert calls[1].return_value == '179'
        assert calls[2].return_value == 175.25
        assert calls[3].return_value is True
        assert calls[4].return_value == [5, 3, 1]
        assert calls[5].return_value is None
        assert calls[6].return_value == 5
        assert calls[7].return_value == 1

        # track function `nb_unlimited`
        async with nb.track_fun('nb_unlimited', all_parameters=True, return_values=True) as track:
            await nb.execute_cells('more-calls')

        calls = await track.receive()
        assert len(calls) == 2

        assert calls[0].parameters == [('args', [5, 2])]
        assert calls[1].parameters == [('kwargs', {'a': 1, 'b': 2})]

        assert calls[0].return_value == 5
        assert calls[1].return_value == 1

        # track function `nb1`
        async with nb.track_fun('nb1', all_parameters=True, return_values=True) as track:
            await nb.execute_cells('more-calls')

        calls = await track.receive()
        assert len(calls) == 1

        assert calls[0].parameters == [('b', 1), ('a', 2)]
        assert calls[0].return_value == 2

        # track function `nb2`
        async with nb.track_fun('nb2', all_parameters=True, return_values=True) as track:
            await nb.execute_cells('more-calls')

        calls = await track.receive()
        assert len(calls) == 1

        assert calls[0].parameters == [('a', 3), ('b', 2)]
        assert calls[0].return_value == 2

        # track function `nb3`
        async with nb.track_fun('nb3', all_parameters=True, return_values=True) as track:
            await nb.execute_cells('more-calls')

        calls = await track.receive()
        assert len(calls) == 1

        assert calls[0].parameters == [('a', 1), ('args', [2])]
        assert calls[0].return_value is None

        # track function `nb4`
        async with nb.track_fun('nb4', all_parameters=True, return_values=True) as track:
            await nb.execute_cells('more-calls')

        calls = await track.receive()
        assert len(calls) == 1

        assert calls[0].parameters == [('a', 1), ('b', 2), ('args', [3, 4, 5])]
        assert calls[0].return_value is None

        # track function `nb5`
        async with nb.track_fun('nb5', all_parameters=True, return_values=True) as track:
            await nb.execute_cells('more-calls')

        calls = await track.receive()
        assert len(calls) == 1

        assert calls[0].parameters == [('a', 1), ('kwargs', {'b': 2, 'c': 3})]
        assert calls[0].return_value == {'b': 2, 'c': 3}

        # track function `nb6`
        async with nb.track_fun('nb6', all_parameters=True, return_values=True) as track:
            await nb.execute_cells('more-calls')

        calls = await track.receive()
        assert len(calls) == 1

        assert calls[0].parameters == [('a', 1), ('kwargs', {'c': 3}), ('b', 3)]
        assert calls[0].return_value == 3

        # track function `nb7`
        async with nb.track_fun('nb7', all_parameters=True, return_values=True) as track:
            await nb.execute_cells('more-calls')

        calls = await track.receive()
        assert len(calls) == 1

        assert calls[0].parameters == [('a', 1), ('b', 2)]
        assert calls[0].return_value == 1


@pytest.mark.asyncio
async def test_multiple():
    async with PythonNotebook('functions.ipynb') as nb:
        # execute function definition
        await nb.execute_cells('definition')

        # track functions `nb1` and `nb2`
        async with \
                nb.track_fun('nb1', all_parameters=True, return_values=True) as t1, \
                nb.track_fun('nb2', all_parameters=True, return_values=True) as t2:
            await nb.execute_cells('more-calls')

        # compare output
        calls1 = await t1.receive()
        calls2 = await t2.receive()

        assert len(calls1) == 1
        assert calls1[0].parameters == [('b', 1), ('a', 2)]
        assert calls1[0].return_value == 2

        assert len(calls2) == 1
        assert calls2[0].parameters == [('a', 3), ('b', 2)]
        assert calls2[0].return_value == 2


@pytest.mark.asyncio
async def test_filter():
    async with PythonNotebook('functions.ipynb') as nb:
        # execute function definition
        await nb.execute_cells('definition')

        # track function `nb_fun` with parameter `b`
        async with nb.track_fun('nb_fun', 'b') as track:
            await nb.execute_cells('more-calls')

        calls = await track.receive()
        assert len(calls) == 8

        assert calls[0].parameters == [('b', 116)]
        assert calls[1].parameters == [('b', '155')]
        assert calls[2].parameters == [('b', 143.5)]
        assert calls[3].parameters == [('b', False)]
        assert calls[4].parameters == [('b', [2, 4, 6])]
        assert calls[5].parameters == [('b', 2048)]
        assert calls[6].parameters == [('b', 2)]
        assert calls[7].parameters == [('b', 2)]

        # track function `nb_fun` without any parameters
        async with nb.track_fun('nb_fun') as track:
            await nb.execute_cells('more-calls')

        calls = await track.receive()
        assert len(calls) == 8

        assert calls[0].parameters == []
        assert calls[1].parameters == []
        assert calls[2].parameters == []
        assert calls[3].parameters == []
        assert calls[4].parameters == []
        assert calls[5].parameters == []
        assert calls[6].parameters == []
        assert calls[7].parameters == []


@pytest.mark.asyncio
async def test_return_values_false():
    async with PythonNotebook('functions.ipynb') as nb:
        # execute function definition
        await nb.execute_cells('definition')

        # track function `nb_fun`
        async with nb.track_fun('nb_fun', return_values=False) as track:
            await nb.execute_cells('more-calls')

        calls = await track.receive()
        assert len(calls) == 8

        assert calls[0].return_value is None
        assert calls[1].return_value is None
        assert calls[2].return_value is None
        assert calls[3].return_value is None
        assert calls[4].return_value is None
        assert calls[5].return_value is None
        assert calls[6].return_value is None
        assert calls[7].return_value is None


@pytest.mark.asyncio
async def test_clear():
    async with PythonNotebook('functions.ipynb') as nb:
        # execute function definition
        await nb.execute_cells('definition')

        # track function `nb_fun`
        async with nb.track_fun('nb_fun', return_values=False) as track:
            await nb.execute_cells('more-calls')
            calls = await track.receive()
            assert len(calls) == 8

            await track.clear()
            calls = await track.receive()
            assert len(calls) == 0

            await nb.execute_cells('more-calls')
            calls = await track.receive()
            assert len(calls) == 8


@pytest.mark.asyncio
async def test_first_and_last_call():
    async with PythonNotebook('functions.ipynb') as nb:
        # execute function definition
        await nb.execute_cells('definition')

        # track function
        async with nb.track_fun('nb1', all_parameters=True, return_values=True) as track:
            await nb.ref('nb1')(1, 2).receive()
            await nb.ref('nb1')(5, 4).receive()
            await nb.ref('nb1')(11, 12).receive()

        # get first call
        first_call = await track.receive_first()
        assert first_call.parameters == [('a', 1), ('b', 2)]
        assert first_call.return_value == 1

        # get last call
        last_call = await track.receive_last()
        assert last_call.parameters == [('a', 11), ('b', 12)]
        assert last_call.return_value == 11

        # clear
        await track.clear()

        # get first call
        first_call = await track.receive_first()
        assert first_call is None

        # get last call
        last_call = await track.receive_last()
        assert last_call is None


@pytest.mark.asyncio
async def test_ctx_exit():
    async with PythonNotebook('functions.ipynb') as nb:
        # execute function definition
        await nb.execute_cells('definition')

        # track function
        async with nb.track_fun('nb1', all_parameters=True, return_values=True) as track:
            await nb.ref('nb1')(1, 2).receive()
            await nb.ref('nb1')(3, 4).receive()

        await nb.ref('nb1')(5, 6).receive()

        # get result and compare
        calls = await track.receive()
        assert len(calls) == 2

        assert calls[0].parameters == [('a', 1), ('b', 2)]
        assert calls[0].return_value == 1

        assert calls[1].parameters == [('a', 3), ('b', 4)]
        assert calls[1].return_value == 3
