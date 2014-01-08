__author__ = 'tarzan'

from setuptools import setup, find_packages
import os

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.md')) as f:
    README = f.read()
with open(os.path.join(here, 'CHANGES.md')) as f:
    CHANGES = f.read()

install_requires = [
    "requests >= 2.0"
]

setup(
    name='restful_client',
    version='0.1.0',
    author='Hoc .T Do',
    author_email='hoc3010@gmail.com',
    packages=find_packages(),
    scripts=[],
    url='https://github.com/tarzanjw/restful_client',
    license='LICENSE',
    description='Efficient RESTful client',
    long_description=README + "\n\n" + CHANGES,
    install_requires=install_requires,
)