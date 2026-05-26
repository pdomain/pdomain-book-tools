"""Allow ``python -m pdomain_book_tools.schemas`` to dispatch to .emit."""

import sys

from pdomain_book_tools.schemas.emit import main

if __name__ == "__main__":
    sys.exit(main())
