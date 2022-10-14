# JPTest2

JPTest is a unit testing framework for Jupyter Notebooks and aims for fast test writing in less lines of code. It
creates the possibility to score and automatically grade exams with separate notebook (`.ipynb`) and test (`.py`) files.

## Quick Start

JPTest relies on [Jupyter](https://jupyter.org/). If you need any other libraries for executing your notebook cells they
can be installed in your environment the usual way.

The preferred way to use JPTest is in a virtual environment:

```bash
python -m venv venv
source venv/bin/activate
```

Use `pip` to download and install JPTest:

```bash
pip install jptest2
```

Now imagine that your student has to implement a Fibonacci function called `fibonacci`, which accepts a single parameter
`n` and returns the n-th fibonacci number. Inside the notebook to submit, you prepared a cell with the tag `task-1`. A
simple test could look like the following example:

```python
from jptest2 import *

# Create test with name "Task 1" and a maximum score of 1.
# Execute *all* cells with tag "task-1" prior to executing the test function.
# Please note: Every test function must be async!
@JPTest('Task 1', max_score=1, execute=('task-1',))
async def test_task1(nb: Notebook):
    # Create a reference to the function `fibonacci` inside the notebook.
    fib_fun_in_nb = nb.ref('fibonacci')

    # Receive five results from the fibonacci function.
    result = await NotebookReference.receive_many(
        fib_fun_in_nb(1),
        fib_fun_in_nb(2),
        fib_fun_in_nb(3),
        fib_fun_in_nb(4),
        fib_fun_in_nb(5)
    )

    # Yield a tuple containing a condition, an award, a comment in case the
    # condition is false and a comment in case the condition is true.
    yield result == [1, 1, 2, 3, 5], 1, 'fib fun incorrect', 'fib fun correct'
```

Let us assume the notebook file is called `notebook.ipynb` and the test file is called `tests.py`. Call JPTest with the
following command:

```bash
python -m jptest2 notebook.ipynb tests.py
```

## Contexts and Processes

- Notebook and Test Context

## The Execute Parameter

One can control in detail what code is executed prior to a test. Therefore, the `execute` parameter accepts different
types, which can also be nested recursively:

**String.**
If the parameter is of type `str`, the value is considered as code and injected into the notebook.

**Tuple.**
If the parameter is of type `tuple`, the value is considered as tags. If there is one element in the tuple, every cell
with this tag is executed. If there are two elements in the tuple, every cell between the first appearance of the first
tag and the first appearence of the second tag (including) is executed.

**Function.**
If the parameter is a function (`Callable`), it will be executed in the notebook context using `execute_fun`.

**List.**
If the parameter is of type `list`, every element will be executed in the order of its appearence, following the rules
stated above. Even though it is not actually needed because of list operations in Python, nested statements are possible
with it.

## Execute Code

## References

## Annotations and Parameters

Previously you have already seen the annotation `@JPTest`. It has two additional optional parameters. `timeout`
specifies a timeout in seconds **per cell**. As you may have noticed, the notebook is passed as a parameter to the test
function **after** the `execute` parameter is executed. You can set `prepare_second` to `True` to get a second notebook
with the same settings as a second parameter.

```python
@JPTest('Task 1', max_score=1, execute=('task-1',), prepare_second=True)
async def test_task1(nb1: Notebook, nb2: Notebook):
    # `nb1` equals `nb2`, but they were created and prepared independently!
    pass
```

Furthermore, there is `@JPTestGet` if you are only interested in data stored within the notebook. To this annotation
you pass a name, a maximum score, a timeout and an execute command. It further accepts a list of names that are
variables inside the notebook. All of these are transferred to the test context and used as parameters for your test
function. You can not access the notebook using this annotation!

```python
@JPTestGet('Task 1', max_score=1, execute=('task-1',), get=['first_var', 'second_var'])
async def test_task1(first_value, second_value):
    # `first_value` and `second_value` are the received values.
    pass
```

The last annotation is `@JPTestComparison`. It allows using two notebooks prepared in different ways inside the test
function. We use this mainly to compare the student's results with those from a sample solution.

```python
def import_pandas():
    # noinspection PyUnresolvedReferences
    import pandas as pd

def sample_solution():
    correct_df = pd.read_csv('my_dataset.csv')

# Everything passed to `prepare` is executed in both notebooks.
# Everything passed to `execute_left` is executed in the first notebook.
# `execute_right` does the same in the second notebook.
# `hold_left` expects a list of variable names to copy to the test context
# from the first notebook. `hold_right` does the same to the second notebook.
# Every received value is used as a parameter for the test function.
@JPTestComparison('Task 1', max_score=1, execute=import_pandas,
                  prepare_left=('task-1',), hold_left='students_df',
                  prepare_right=sample_solution, hold_right='correct_df')
async def test_task1(students_val, correct_val):
    pass
```

## Function Injection

## Function Replacing

## Function Tracking

## Output Formats

## Parallelization

- less inter process communication
- prepare in parallel
- use static functions in notebook reference
- Tuning via -proc

## Running Without Tests
