## ~checkdbintegrity

Checks the database for missing required fields (NULLs), invalid references, and other integrity issues

**Usage:**
`~checkdbintegrity`

**Who can use:**
Guildmaster, Oracle, V

**Details:**

- Checks for NULLs in required columns (like Discord IDs)
- Looks for roles, users, or messages that reference missing data
- Reports on missing channels/messages from the bot's tracking table
- Lists all issues found, or confirms that the DB passed the integrity check
- Use this after migrations, major changes, or troubleshooting
