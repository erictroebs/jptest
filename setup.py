from setuptools import setup, find_packages

with open('README.md', 'r', encoding='utf-8') as file:
    long_description = file.read()

setup(
    name='jptest2',
    version='2.0.20',
    author='Eric Tröbs',
    author_email='eric.troebs@tu-ilmenau.de',
    description='write graded unit tests for Jupyter Notebooks in a few lines of code',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/erictroebs/jptest',
    project_urls={
        'Bug Tracker': 'https://github.com/erictroebs/jptest/issues',
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    package_dir={'': 'src'},
    packages=find_packages(where='src'),
    python_requires='>=3.6',
    install_requires=[
        'jupyter',
        'aiofiles'
    ],
    extras_require={
        'demo': [
            'watchfiles'
        ],
        'sqlite': [
            'aiosqlite'
        ],
        'duckdb': [
            'duckdb'
        ]
    }
)
