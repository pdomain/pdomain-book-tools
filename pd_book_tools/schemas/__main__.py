"""Allow ``python -m pd_book_tools.schemas`` to dispatch to .emit."""

import sys

from pd_book_tools.schemas.emit import main

if __name__ == "__main__":
    sys.exit(main())
