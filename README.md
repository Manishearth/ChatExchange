ChatExchange
============

[![Github Actions build status for master][1]][2]

  [1]: https://github.com/Manishearth/ChatExchange/actions/workflows/lint+test.yml/badge.svg
  [2]: https://github.com/Manishearth/ChatExchange/actions

A Python3 API for talking to Stack Exchange chat.

 - Supported Python versions (tests run by Github Actions):
   3.7, 3.8, 3.9, 3.10, 3.11, 3.12
 - Unclear versions (not run on Github Actions
   as Github no longer supports them):
   2.7 (sic), 3.4, 3.5, 3.6

## Dependencies

`pip install chatexchange` pulls in the following libraries:

 - BeautifulSoup (`pip install beautifulsoup4`)
 - Requests (`pip install requests`)
 - python-websockets for the experimental websocket listener
   (`pip install websocket-client`).
   This module is optional; without it, `initSocket()` from SEChatBrowser
   will not work.

The package has a number of additional development requirements;
install them with

    pip install chatexchange[dev]

or `.[dev]` if you are in the top directory of a local copy of the source.

## Shortcuts

1. `make install-dependencies` will install the necessary
   Python package dependencies into your current environment
   (active virtualenv or system site packages)
2. `make test` will run the tests
3. `make run-example` will run the example script
4. `make` will run the above three in order

## License

Licensed under either of

 * Apache License, Version 2.0, ([LICENSE-APACHE](LICENSE-APACHE)
   or http://www.apache.org/licenses/LICENSE-2.0)
 * MIT license ([LICENSE-MIT](LICENSE-MIT)
   or http://opensource.org/licenses/MIT)

at your option.

### Contribution

Unless you explicitly state otherwise, any contribution
intentionally submitted for inclusion in the work by you,
as defined in the Apache-2.0 license, shall be dual licensed as above,
without any additional terms or conditions.
