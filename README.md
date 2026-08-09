# cloudcosttree (pip)

`pip install cloudcosttree` — a thin wrapper that downloads and runs the real
[CloudCostTree](https://cloudcosttree.com) CLI (a Go binary, published at
[rulssss/cloudcosttree](https://github.com/rulssss/cloudcosttree)) on first
use. This package isn't a reimplementation; every `cloudcosttree` command
just execs the real binary.

## Install

```sh
pip install cloudcosttree
```

The first `cloudcosttree` invocation downloads the matching platform binary
(and the bundled price catalog) into `~/.cloudcosttree/` — the same
directory `install.sh`/Homebrew installs already use. No AWS account or
credentials needed for a plain `analyze`/`tree`/`diff` run.

## Upgrading

```sh
pip install --upgrade cloudcosttree
```

Downloads the CLI version matching the new package version on next run —
same as any other pip package's upgrade.

See the [main repo](https://github.com/rulssss/cloudcosttree#readme) for
full CLI documentation.
