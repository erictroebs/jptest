from jptest import *


# Aufgabe 1
@JPTest('Aufgabe 1', max_score=2, execute=('task-1',))
def aufgabe1(tb: JPTestBook):
    isgenerator = tb.inject('''
        from types import GeneratorType
        isgenerator = callable(even) and isinstance(even(1024), GeneratorType)
    ''', 'isgenerator')
    yield isgenerator, 1

    result = tb.inject('result = list(even(15))', 'result')
    yield result == list(range(0, 15, 2)), 0.5

    result = tb.inject('result = list(even(1025))', 'result')
    yield result == list(range(0, 1025, 2)), 0.5


# Aufgabe 2
@JPTest('Aufgabe 2', max_score=1, execute=[
    '''
    def even(i):
        return range(1, i, 3)
    ''',
    ('task-2',)
])
def aufgabe2(tb: JPTestBook):
    result = tb.get('even_list')
    yield result == list(range(1, 256, 3)), 1
