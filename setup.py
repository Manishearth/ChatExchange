import setuptools


setuptools.setup(
    name='ChatExchange3',
    version='0.0.1',
    url='https://github.com/ByteCommander/ChatExchange3',
    packages=[
        'chatexchange3', 'chatexchange3_tests'
    ],
    install_requires=[
        'beautifulsoup4>=4.3.2',
        'requests>=2.2.1',
        'websocket-client>=0.13.0',
        # only for dev:
        'coverage>=3.7.1',
        'epydoc>=3.0.1',
        'httmock>=1.2.2',
        'pytest-capturelog>=0.7',
        'pytest-timeout>=0.3',
        'pytest>=2.5.2'
    ]
)
