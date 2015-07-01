# Documentation
This file contains the documentation for the ChatExchange code and its use. The documented code is that found in `chatexchange/*`.

## `_utils.py`
Contains utility functions for use within ChatExchange. Not originally indented for external use, but are accessible from external code.

**`log_and_ignore_exceptions(f, exceptions=Exception, logger=logging.getLogger('exceptions'))`**  