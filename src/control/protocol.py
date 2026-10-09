"""Recognize explicit UNO faults without changing valid legacy reply formats.

Frames use {tag_error_reason} or {error_reason}; tags identify requests and
reason is a firmware code. Any fault ends acquisition, even for another tag.
"""

import re


class FirmwareFault(RuntimeError):
    """Carry the failing request tag (or None) and firmware reason string."""

    def __init__(self, tag, reason):
        """Store protocol fields and produce an actionable acquisition error."""
        self.tag = tag
        self.reason = reason
        super().__init__(f'Firmware fault ({tag or "untagged"}): {reason}')

    @classmethod
    def check_frame(cls, frame):
        """Raise on a complete explicit fault; leave successful frames unchanged.

        frame is a brace-delimited ASCII string. Returns None for acknowledgments,
        heartbeat and measurements. A RuntimeError bypasses gyro-bias retries.
        """
        match = re.fullmatch(r'\{(?:(.*?)_)?error_([a-z0-9_]+)\}', frame)
        if match:
            raise cls(match[1] or None, match[2])
