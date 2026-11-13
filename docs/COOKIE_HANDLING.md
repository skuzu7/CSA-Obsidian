# Browser Cookie Safety

`chrome_cookies.extract()` previously wrote a decrypted-cookie JSON file by default. The new default returns cookie dictionaries **in memory only** and no longer creates `chrome_cookies.json` during `import_chrome_cookies.py` automation.

For a deliberate local export of your **own** browser session (never share these files):

```sh
python chrome_cookies.py --output path/to/new-private-cookies.json
```

Safety notes:
- The output path **must not already exist**; no silent overwrite of existing exports.
- On POSIX the new file is created with mode `0600`. On Windows, access depends on directory/NTFS ACLs and requires separate inspection.
- Decrypted session cookies can grant access to authenticated services. Keep them outside synced/shared folders, never commit or upload them, and delete them immediately after authorized use.
- If a cookie export was ever published, revoke affected sessions at the service and review access activity. A Git deletion cannot invalidate active cookies.
- This module depends on Windows Chrome profile internals. Tests in Linux CI cover *export policy*, not the live Windows Chrome decryption path.
