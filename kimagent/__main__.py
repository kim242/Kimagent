"""Point d'entrée : python -m kimagent …"""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
