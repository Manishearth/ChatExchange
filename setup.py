import setuptools

setuptools.setup(
    name='ChatExchange',
    version='0.0.3',
    url='https://github.com/Manishearth/ChatExchange',
    packages=[
        'chatexchange'
    ],
    install_requires=[
        'beautifulsoup4>=4.3.2',
        'requests>=2.2.1',
        'websocket-client>=0.13.0',
        # only for dev:
        'coverage==3.7.1',
        'epydoc>=3.0.1',
        'httmock>=1.2.2',
        'pytest-capturelog>=0.7',
        'pytest-timeout>=0.3',
        'pytest>=2.7.3',
        'py>=1.4.29',
    ]
)
