## Generate a user-based arcade expression

This script can generate a simple Arcade Expression that can be used when visualizing track or LKL data in a map. It takes a CSV file and at least two columns (usernames, category) and it wil generate an expression to use in a map.

Supports Python 3.6+

----

The script uses these arguments:
- `--file <csv-file>` - the CSV file to read
- `--username-column <column-name>` - the column in the CSV file containing the usernames of the tracked users
- `--other-column <column-name>` - the column in the CSV file containing the values to associate with the users (e.g. a category)

Example Usage 1 - Printing to console
```bash
python --file users.csv --username-column usernames --other-column category
```

Example Usage 2 - Direct to file
```bash
python --file users.csv --file users.csv --username-column usernames --other-column category > output.txt
```

Example Usage 3 - Direct to Clipboard on Mac
```bash
python --file users.csv --file users.csv --username-column usernames --other-column category | pbcopy
```

Example Usage 4 - Direct to Clipboard on Windows
```bash
python --file users.csv --file users.csv --username-column usernames --other-column category | CLIP
```

## What it does

 1. Reads the provided CSV file
 2. Generates an if/else if based arcade expression like:
 ```

if ($feature.created_user == 'username1') {
    return 'Fire Fighter'
}

else if ($feature.created_user == 'username2') {
    return 'Police Officer'
}

return ''

```
3. Prints the expression
