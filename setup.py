import setuptools


setuptools.setup(
    name='ChatExchange',
    version='0.0.0dev12',
    url='https://github.com/Manishearth/ChatExchange',
    packages=[
        'chatexchange'
    ],
    install_requires=[
        'beautifulsoup4==4.3.2',
        'coverage==3.7.1',
        'httmock==1.2.2',
        'pytest-capturelog==0.7',
        'pytest==2.5.2',
        'requests==2.2.1',
        'websocket-client==0.13.0'
    ]
)
