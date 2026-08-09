"""Resolves (downloading on first use if needed) and execs the real
cloudcosttree CLI binary -- this package is a thin pip-installable wrapper
around the Go binary published at github.com/rulssss/cloudcosttree/releases,
not a reimplementation. Mirrors the same "resolve or download" pattern the
VS Code extension's binaryInstaller.ts already uses, simplified: no
background update-checking here -- `pip install --upgrade cloudcosttree`
bumping __version__ is what triggers a fresh binary download, matching
ordinary pip upgrade semantics instead of a bespoke self-updater.
"""

from __future__ import annotations

import platform
import shutil
import stat
import subprocess
import sys
import urllib.request
from pathlib import Path

from . import __version__

RELEASES_REPO = "rulssss/cloudcosttree"

# Same platform/arch -> release-asset-name convention install.sh and the
# VS Code extension's binaryInstaller.ts both already use.
_OS_NAMES = {"Darwin": "darwin", "Linux": "linux", "Windows": "windows"}
_ARCH_NAMES = {
    "x86_64": "amd64",
    "amd64": "amd64",
    "AMD64": "amd64",
    "arm64": "arm64",
    "aarch64": "arm64",
    "ARM64": "arm64",
}


def _release_asset_name() -> str:
    os_name = _OS_NAMES.get(platform.system())
    arch_name = _ARCH_NAMES.get(platform.machine())
    if not os_name or not arch_name:
        raise RuntimeError(
            f"cloudcosttree has no prebuilt binary for {platform.system()}/{platform.machine()}. "
            f"Install it manually: see https://github.com/{RELEASES_REPO}#readme"
        )
    ext = ".exe" if os_name == "windows" else ""
    return f"cloudcosttree-{os_name}-{arch_name}{ext}"


def _home_dir() -> Path:
    # Matches pkg/cost/catalog.go's homeCatalogDir() convention exactly
    # (~/.cloudcosttree) -- the same directory the Go binary itself already
    # falls back to for prices.json, so a pip-installed and a
    # brew/install.sh-installed cloudcosttree on the same machine share
    # one cache location instead of each keeping a separate copy.
    return Path.home() / ".cloudcosttree"


def _binary_path() -> Path:
    asset = _release_asset_name()
    ext = ".exe" if asset.endswith(".exe") else ""
    # Version-suffixed filename: upgrading the pip package (which bumps
    # __version__) naturally points at a not-yet-downloaded path, so there's
    # no separate metadata file to track "is this stale" -- the filename
    # itself answers that.
    return _home_dir() / "bin" / f"cloudcosttree-{__version__}{ext}"


def _download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".download")
    try:
        with urllib.request.urlopen(url) as resp, open(tmp, "wb") as f:
            shutil.copyfileobj(resp, f)
    except Exception as err:
        tmp.unlink(missing_ok=True)
        raise RuntimeError(
            f"could not download {url} ({err}). Check your network connection, "
            f"or install cloudcosttree manually: https://github.com/{RELEASES_REPO}#readme"
        ) from err
    tmp.replace(dest)


def _ensure_binary() -> Path:
    binary = _binary_path()
    if binary.exists():
        return binary

    asset = _release_asset_name()
    print(f"cloudcosttree: downloading the CLI binary (v{__version__}, first run only)...", file=sys.stderr)
    _download(f"https://github.com/{RELEASES_REPO}/releases/download/v{__version__}/{asset}", binary)
    if platform.system() != "Windows":
        binary.chmod(binary.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

    prices = _home_dir() / "prices.json"
    try:
        _download(f"https://github.com/{RELEASES_REPO}/releases/download/v{__version__}/prices.json", prices)
    except RuntimeError as err:
        # Non-fatal: DefaultPricesPath() will fall back to whatever
        # `cloudcosttree update-prices` (network, no AWS account needed)
        # or a --prices flag supplies instead -- same soft-degrade the CLI
        # itself already applies to every other missing-data case.
        print(f"cloudcosttree: warning: {err}", file=sys.stderr)

    return binary


def main() -> None:
    binary = _ensure_binary()
    result = subprocess.run([str(binary), *sys.argv[1:]])
    sys.exit(result.returncode)
