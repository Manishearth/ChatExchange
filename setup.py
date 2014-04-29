import setuptools


setuptools.setup(
    name='ChatExchange',
    version='0.0.0dev5',
    url='https://github.com/Manishearth/ChatExchange',
    packages=[
        'chatexchange'
    ],
    package_dir={
        '': 'src'
    },
    install_requires=[
        'BeautifulSoup==3.2.1',
        'httmock==1.2.2',
        'pprintpp==0.2.1',
        'pytest-capturelog==0.7',
        'pytest==2.5.2',
        'requests==2.2.1',
        'websocket-client==0.13.0'
    ]
)
