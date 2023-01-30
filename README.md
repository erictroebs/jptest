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

Use `pip` to download and install JPTest. Make sure not to install the first version of JPTest, which is missing the `2`
at the end of the package name, as it is only available for compatibility reasons.

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

Please note the test function is an `async` function!

## Table of Contents

- [Contexts and Processes](#contexts-and-processes)
- [The Execute Parameter](#the-execute-parameter )
- [Execute Code](#execute-code)
- [References](#references)
- [Annotations and Parameters](#annotations-and-parameters)
- [Function Injection](#function-injection)
- [Function Replacing](#function-replacing)
- [Function Tracking](#function-tracking)
- [Setup and Teardown Methods](#setup-and-teardown-methods)
- [Output Formats](#output-formats)
- [Parallelization](#parallelization)
- [Running Without Tests](#running-without-tests)
- [Live Preview](#live-preview)
- [Other Kernels](#other-kernels)

## Contexts and Processes

JPTest manages different processes. The first process that is started collects all annotations like `@JPTest` and
stores them together with their respecting test functions. Later, this process will control the startup of notebooks
and take over the evaluation. We refer to this process as the test context.

Jupyter uses kernels that are started in a separate process. JPTest supports Python3 kernels and does not share
them between tests, so for each test at least one independent kernel process is started to run the contents of the
notebook. However, as we will see later, it is also possible to start multiple kernels per test. We refer to this set
of processes as the notebook context.

JPTest always runs on an in-memory copy of the notebook and does not modify files, but tests and code in the notebook
still have the possibility to do so.

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

The easiest way to execute code in the notebook is via the `cells` property. It returns a list of all cells present in
the notebook and allows to filter and execute them one by one.

```python
for cell in nb.cells:
    print(cell.tags)

    if cell.type == 'code':
        await cell.execute()
```

The function `execute_cells` represents a shortcut to select only code cells by tags prior to executing them in their
order of appearance.

```python
# execute all cells with tag `task-1`
await nb.execute_cells('task-1')

# execute all cells from `task-3` to `task-5`
await nb.execute_cells(from_tag='task-3', to_tag='task-5')
```

It is also possible to inject code into the notebook context. `execute_code` creates a new code cell from the given
string, inserts it at the end of the notebook and executes it. Additional indentation of otherwise correct code is
possible.

```python
await nb.execute_code('''
    a = 5
    b = 10
''')
```

Please note that there are functions `store` and `stores` to store values in the notebook. Unlike the previous example
this also works with non-primitive types and references.

```python
ref1 = await nb.store(5, 'a')
ref2 = await nb.store(6)
await nb.store(ref1, 'copy_of_ref1')

ref3, ref4 = await nb.stores(b=10, c={'tiger': 'dangerous'})
```

## References

It is possible to interact with objects and code in the notebook context. The most important class in this regard is
`NotebookReference`. References are returned, for example, by the `ref` and `get` functions, represent objects in the
notebook context and may be used for interaction in various ways:

- `receive` serializes the referenced object and transfers it from the notebook context to the test context. `execute`,
  on the other hand, executes a statement without processing the result and transferring it to the test context.
- Access to an object's attributes or items is possible with the usual syntax. Note that the result is not evaluated
  immediately and thus errors due to missing attributes or keys are carried over until the actual execution.
- References may be called like functions. The parameters are either other references, then these are resolved within
  the notebook context, or local variables from the test context, then these are transferred into the notebook context
  and used for the call. Function calls are also not executed immediately.
- For references to lists and other sequences there is a function `len` to determine the length. The built-in `len`
  function, however, cannot be used with the `async`/`await` syntax.

```python
my_fun_in_nb = nb.my_fun
my_fun_return = my_fun_in_nb()

my_dict_in_nb = nb.my_dict
val_of_x = my_dict_in_nb['x']

# Raises an exception if `my_fun` does not exist
# or raises an exception itself.
print(await my_fun_return.receive())

# Raises an exception if `my_dict` does not `x` is not a key in `my_dict`.
print(await val_of_x.receive())
```

Pickle is used to serialize and deserialize objects. Therefore, it is also possible to transfer more complex objects
like Pandas DataFrames or NumPy Arrays.

References to a notebook's objects can be used as parameters to call a function within another notebook. JPTest will
transfer the value to the notebook containing the function prior to calling it. This means the used reference has to be
serializable.

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


# Everything passed to `prepare` is executed in both notebooks independently.
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

There are two ways to inject functions:

The first method `inject_fun` transfers a function to the notebook context and returns a reference. This can be called
as described before or passed as a parameter to another function.

```python
def fun(i: int):
    return i + 1


injected = await nb.inject_fun(fun)
result = await injected(5).receive()

# `result` equals `6`.
```

You can also send classes to the notebook context. But there is no way to transfer needed superclasses automatically
as well.

The second method `execute_fun` executes a function's body in the notebook context while the header is only used in the
test context. This makes it possible to write syntactically correct code with alle benefits of analysis within an IDE,
although it is later executed in the notebook context.

```python
def fun(i: int):
    k = i + 1


# `i` has to be available in the notebook context!
await nb.execute_fun(fun)

# `k` is defined globally in the notebook context
# after the execution.
```

## Function Replacing

Functions in the notebook context can be replaced with others, for example to skip network requests and return a fixed
response instead to speed them up.

```python
await nb.execute_code('''
    from time import sleep

    def my_fun():
        sleep(10)
        return 1                
''')


def replacement():
    return 2


async with nb.replace_fun('my_fun', replacement):
    # executes `replacement` in notebook context.
    result = await nb.ref('my_fun')().receive()
    # prints `2`
    print(result)
```

## Function Tracking

Furthermore, it is possible to track function calls. This may be used to check if an implementation uses recursion.
In addition, the parameters and return values used can be extracted.

```python
await nb.execute_code('''
    def fib(i):
        return i if i <= 1 else fib(i-1) + fib(i-2)
''')

async with nb.track_fun('fib') as calls:
    await nb.ref('fib')(15).execute()

print(len(await calls.receive()) > 1000)
```

## Setup and Teardown Methods

Use `@JPSetup` and `@JPTeardown` to annotate `async` functions. Setup functions are run prior to all tests and teardown
functions after all tests have completed.

```python
@JPSetup
async def setup():
    print('setup')


@JPTeardown
async def teardown():
    print('teardown')
```

Multiple setup or teardown functions are run in parallel.

## Output Formats

The default output format is JSON. You can switch it to Markdown using the command line flag `--md`.

## Parallelization

Since all notebook kernels are started in different processes, multicore processors can be fully utilized. However,
there are a few things to keep in mind:

- The test context can become a bottleneck because it uses only one thread. Therefore, the notebooks should work as
  independently as possible and the test context should only be used for coordination and evaluation.
- Keep inter-process communication to a minimum and outsource computationally intensive operations to the notebook
  context.
- Use the parameter `--tests` to limit the number of concurrently running tests.

## Running Without Tests

If no test file is given on startup, JPTest will choose a default test set. It executes all cells once in the correct
order, does not score and passes exceptions. This can be used to check notebooks for syntax errors, determine if
libraries are missing within an image or if data sets have not been shipped.

Use the command line parameter `--quiet` to suppress any output other than exceptions and stacktraces.

## Live Preview

The live preview is activated with the `--live` switch. It monitors changes to the given files and automatically reruns
the evaluation as soon as one of them is modified. This mode is useful for developing tests or for demonstrations.

Install the package `jptest2[demo]` to receive the optional dependencies. The `clear` command is used to clear the
terminal window and therefore must be available.

## Other Kernels

While the main focus is on Python notebooks, development to support other kernels is possible. Set the `kernel`
parameter to specify which language is used in the notebook. Besides Python3, two databases are supported at the moment.
However, they do not start an actual Jupyter Kernel but send the queries directly to a connected database.

1. **SQLite** using `jptest2[sqlite]`
2. **DuckDB** using `jptest2[duckdb]`
