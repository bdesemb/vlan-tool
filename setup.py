from setuptools import setup, find_packages


with open('README.rst') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='vlantool',
    version='0.0.1',
    description='Tool for configuring vlan on RPI',
    long_description=readme,
    author='Benoit Desemberg',
    author_email='benoit.d@bookvideo.com',
    url='http://www.bookvideo.com',
    license=license,
    packages=find_packages(exclude=('tests', 'docs'))
)