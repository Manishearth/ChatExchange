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
        'websocket-client>=0.13.0'
    ],
    extras_require={
        'dev': [
            'coverage>=4.5.0',
            'epydoc>=3.0.1',
            'httmock>=1.2.2',
            'pytest-timeout>=0.3',
            'pytest>=3.4.2',
            'py>=1.5.0',
            'bpython>=0.16'
        ]
    }
)
