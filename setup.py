from setuptools import setup

setup(
    name='add_trailing_comma',
    description='Automatically add trailing commas to calls and literals',
    url='https://github.com/asottile/add_trailing_comma',
    version='0.6.1',
    author='Anthony Sottile',
    author_email='asottile@umich.edu',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
    install_requires=['tokenize-rt>=2'],
    py_modules=['add_trailing_comma'],
    entry_points={
        'console_scripts': ['add-trailing-comma = add_trailing_comma:main'],
    },
)
