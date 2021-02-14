from os import path
from setuptools import setup

with open(path.join(path.dirname(path.abspath(__file__)), 'README.md')) as f:
    readme = f.read()

setup(
    name='chrispile',
    version='1.0.0',
    packages=['chrispile'],
    url='https://github.com/FNNDSC/chrispile',
    license='MIT',
    author='Jennings Zhang',
    author_email='Jennings.Zhang@childrens.harvard.edu',
    description='Syntactic sugar for running ChRIS apps locally',
    long_description=readme,
    long_description_content_type='text/markdown',
    python_requires='>=3.8',
    install_requires=['pyyaml', 'jinja2'],
    entry_points={
        'console_scripts': [
            'chrispile = chrispile.__main__:main'
            ]
        }
)
