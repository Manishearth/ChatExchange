import setuptools


setuptools.setup(
    name='ChatExchange3',
    version='0.0.1',
    url='https://github.com/ByteCommander/ChatExchange3',
    packages=[
        'chatexchange3'
    ],
    install_requires=[
        'beautifulsoup4>=4.3.2',
        'requests>=2.2.1',
        'websocket-client>=0.13.0'
    ]
)
