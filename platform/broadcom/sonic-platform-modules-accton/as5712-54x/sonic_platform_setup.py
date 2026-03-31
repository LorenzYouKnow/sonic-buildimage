from setuptools import setup

DEVICE_NAME = 'accton'
HW_SKU = 'x86_64-accton_as5712_54x-r0'

setup(
    name='sonic-platform',
    version='1.0',
    description='SONiC platform API implementation on Accton Platform AS5712-54x',
    license='Apache 2.0',
    author='Lorenz Knak',
    author_email='l.knak@it-adjutor.de',
    url='',
    maintainer='',
    maintainer_email='',
    packages=[
        'sonic_platform',
    ],
    package_dir={
        'sonic_platform': '../../../../device/{}/{}/sonic_platform'.format(
            DEVICE_NAME, HW_SKU
        )
    },
    classifiers=[

    ],
    keywords='',
)
