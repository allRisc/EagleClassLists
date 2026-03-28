####################################################################################################
# EagleClassLists is a tool used to aid in the creation of class lists for schools.
# Copyright (C) 2026, Benjamin Davis
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
####################################################################################################

"""Entry point for running the Streamlit application."""

from __future__ import annotations

import signal
import subprocess
import sys
from pathlib import Path
from types import FrameType


def setup_signal_handlers() -> None:
    """Set up signal handlers for graceful shutdown."""

    def signal_handler(signum: int, frame: FrameType | None) -> None:
        print("\nShutdown signal received. Exiting gracefully...")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def main() -> None:
    """Run the Streamlit application with signal handling."""
    setup_signal_handlers()

    app_path = Path(__file__).parent / "app.py"

    try:
        ret = subprocess.call(["streamlit", "run", str(app_path)])
        sys.exit(ret)
    except KeyboardInterrupt:
        print("\nServer stopped by user.")
        sys.exit(0)


if __name__ == "__main__":
    main()
