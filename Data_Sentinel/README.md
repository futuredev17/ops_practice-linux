\# 🛡️ Data Sentinel



A small, dependency-free backup and restore tool for Linux, built as part of my daily Linux/DevOps practice. It creates timestamped `.tar.gz` archives, keeps a rolling retention window, logs every run, and verifies restores with `diff`.



\## Features



\- Timestamped `.tar.gz` backups of source directories

\- Retention: keeps the last N archives

\- Exclude patterns for files and directories

\- Dual logging: console + `sentinel.log`

\- Restore mode with a post-restore `diff` verification

\- CLI validation for backup vs. restore mode

\- Repeatable `-s` and `-x` options

\- `--verify` re-opens the archive after writing

\- `--dry-run` shows what would be backed up without writing

\- Built-in ignore list for `.git`, `\_\_pycache\_\_`, and similar files



\## Tech Stack



\- Python 3 (`argparse`, `pathlib`, `logging`, `subprocess`)

\- Linux (Ubuntu 24.04)



\## Quick Start



\### Backup



```bash

python3 auto\_guardian.py \\

&#x20; -s \~/Germany/ops\_practice/Data\_Sentinel \\

&#x20; -d /tmp/backups \\

&#x20; -k 7

```



\### Backup with restore test



```bash

python3 auto\_guardian.py \\

&#x20; -s \~/Germany/ops\_practice/Data\_Sentinel \\

&#x20; -d /tmp/backups \\

&#x20; -k 7 \\

&#x20; --restore

```



`--restore` runs the backup first, then extracts the new archive and verifies it with `diff`. A successful run ends with:



```

\+ Restore test passed!

```



\### CLI Options



| Option | Description |

| --- | --- |

| `-s, --source` | Source directory to back up; repeatable (`-s a -s b`) |

| `-d, --dest` | Destination directory for archives |

| `-k, --keep` | Keep the N most recent archives (default 7; `0` keeps all) |

| `-x, --exclude` | Extra exclude pattern; repeatable, `fnmatch` style |

| `--no-default-excludes` | Disable the built-in ignore list |

| `--verify` | Re-open the archive after writing to verify it |

| `--dry-run` | Show what would be backed up; write nothing |

| `--restore` | Run the backup, then test restoring the new archive |



\## How It Works



1\. Parse CLI arguments and validate the selected mode.

2\. Collect source files and apply exclude patterns.

3\. Create a timestamped archive in the destination directory.

4\. Prune archives beyond the retention limit.

5\. With `--verify`, re-open the archive to confirm it is readable.

6\. With `--restore`, extract the new archive and run `diff` against the source.



\## Sample Output



```

DATA SENTINEL - auto\_guardian

time    : 2026-10-21 11:46:04

dest    : /tmp/backups

keep    : 7

exclude : 20 patterns

archive : /tmp/backups/backup\_20261021\_114604.tar.gz

\+ backup done in 0.02s

&#x20; files       : 26

&#x20; raw size    : 67.7KB

&#x20; archive size: 19.7KB (29.0% of raw)

\+ Restore test passed!

```



\## What I Learned



\- Keep required core arguments (`-s`, `-d`) separate from optional modes (`--restore`, `--dry-run`); that makes `argparse` validation predictable.

\- `subprocess` needs its return code checked, not just its output.

\- `logging` with two handlers gives both live feedback and a durable audit trail.

\- Re-opening the archive (`--verify`) catches corruption that a successful exit code alone would miss.

\- A backup is not finished until a restore has been tested.



\## Roadmap



\- \[ ] Remote backups over SSH with `paramiko`

\- \[ ] Run on a schedule with a systemd timer

\- \[ ] SHA-256 checksums for archive integrity

\- \[ ] Retention by age as well as count

\- \[ ] Restore to a user-selected directory

\- \[ ] Email or webhook notification on failure



\## Notes



\- `/tmp` is fine for testing but is not a durable backup location.

\- This project started from a scaffold and was debugged and extended as part of my daily practice.



\---



\*One commit a day.\*



