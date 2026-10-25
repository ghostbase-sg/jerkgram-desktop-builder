#!/usr/bin/env python3
"""Generate presentation identity without changing upstream protocol versions."""
import json
from pathlib import Path
import re


def render(version, commit):
    if not re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?', version):
        raise ValueError('Invalid presentation version')
    if not re.fullmatch(r'[0-9a-f]{40}', commit):
        raise ValueError('Invalid upstream SHA')
    return f'''// Generated from builder JERKGRAM_VERSION and pinned upstream identity.
#pragma once
#ifndef TDESKTOP_DISABLE_AUTOUPDATE
#error Jerkgram alpha requires DESKTOP_APP_DISABLE_AUTOUPDATE=ON
#endif
namespace Jerkgram {{
inline constexpr auto Version = "{version}";
inline constexpr auto UpstreamVersion = "7.3.1";
inline constexpr auto UpstreamCommit = "{commit}";
}} // namespace Jerkgram
'''


if __name__ == '__main__':
    root = Path(__file__).resolve().parents[1]
    (root/'payloads/linux-identity/jerkgram_identity.h').write_text(render(
        (root/'JERKGRAM_VERSION').read_text().strip(), json.loads((root/'PINNED_UPSTREAM').read_text())['commit']))
