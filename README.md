# pydupfinder

```Usage: pydupfinder [OPTIONS] PATH

  Find duplicate files.

Options:
  Limits: [mutually_exclusive]    Limits for found duplicates
    -a, --at-least INTEGER RANGE  Find AT LEAST that many duplicates if there
                                  are enough duplicates.  [x>=2]
    -m, --max-size TEXT           Calculate checksums for AT MOST this total
                                  size of files.
  -r, --reset-cache               Remove database, caching checksums
  --help                          Show this message and exit.
```

`max-size` limit allows one, for example, find duplicates in OneDrive without downloading everything.
