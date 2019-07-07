from setuptools import setup

setup(
    name='mpnotd',
    version='0.1',
    description='MPD Notification Daemon',
    url='http://github.com/jeffmhubbard/mpnotd',
    author='Jeff M. Hubbard',
    author_email='jeffmhubbard@gmail.com',
    license='MIT',
    packages=['mpnotd'],
    scripts=['bin/mpnotd'],
    zip_safe=False,
)
