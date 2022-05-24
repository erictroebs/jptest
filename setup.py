from setuptools import setup, find_packages

with open('README.md', 'r', encoding='utf-8') as file:
    long_description = file.read()

setup(
    name='jptest',
    version='0.1.0',
    author='Eric Tröbs',
    author_email='eric.troebs@tu-ilmenau.de',
    description='write complex unit tests for Jupyter Notebooks in less lines of code',
    long_description=long_description,
    long_description_content_type='text/markdown',
    # url='https://github.com/pypa/sampleproject',
    # project_urls={
    #     'Bug Tracker': 'https://github.com/pypa/sampleproject/issues',
    # },
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
        'pytest~=7.1.2',
        'testbook~=0.4.2'
    ]
)
