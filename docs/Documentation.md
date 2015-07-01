# Documentation: `_utils.py`
Contains utility functions for use within ChatExchange. Not originally indented for external use, but are accessible from external code.

#### `log_and_ignore_exceptions(f, exceptions=Exception, logger=logging.getLogger('exceptions'))`
Wraps a function to catch and log any exceptions it throws.

**`f`** is the function to wrap. Required.  
**`exceptions`** are the exceptions to catch from `f`. An array of exception types. Optional.  
**`logger`** is the logging manager. You should not need to specify this. Optional.

-----

### `class HTMLTextExtractor(HTMLParser)`
Extends the `HTMLParser` class, which provides methods for working with raw HTML. Adapted from a [Stack Overflow post](http://stackoverflow.com/a/7778368) by [Søren Løvborg](http://stackoverflow.com/u/13679) and Eloff.

#### `handle_data(self, d)`
Appends the given data, **`d`**, to the class' result.

#### `handle_charref(self, number)`
Finds the codepoint specified by **`number`** and appends the Unicode character at this codepoint to the class' result.

#### `handle_entityref(self, name)`
Finds a codepoint based on the HTML entity provided in **`name`** and appends it to the class' result.

-----

#### `html_to_text(html)`
When given a string of valid HTML in **`html`**, returns the text contained in it. Internally, uses the `HTMLTextExtractor` class.

-----

### `class LazyFrom(object)`
A descriptor used when multiple lazy attributes depend on a common source of data. This class lazily extracts data from the specified object and returns it. Only special methods are defined in this class and should not be directly used. For an example of usage, see [`messages.py`](https://github.com/Manishearth/ChatExchange/blob/master/chatexchange/messages.py).