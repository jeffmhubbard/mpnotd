from setuptools import setup

setup(
    name='mpnotd',
    version='0.2',
    description='MPD Notification Daemon',
    url='http://github.com/jeffmhubbard/mpnotd',
    author='Jeff M. Hubbard',
    author_email='jeffmhubbard@gmail.com',
    license='MIT',
    packages=['mpnotd'],
    scripts=['bin/mpnotd'],
    install_requires=[
        'python-mpd2',
        'notify2',
        'beautifulsoup4',
        'bs4',
        'dbus-python',
        'pillow',
    ],
    zip_safe=False,
)
