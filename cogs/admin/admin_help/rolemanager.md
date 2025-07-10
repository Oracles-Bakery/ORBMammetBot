## ~rolemanager

Populates the bot's user database with all current server members

**Usage:**
`~populatemembers`

**Who can use:**
Oracle, Guildmaster, V

**Details:**

- Scans all members (skips bots) and adds them to the database
- Sets the "preferred name" to nickname if present, else uses the username
- Runs an insert for each member (small pause between each to avoid rate limits)
- Summary of successes and failures is reported at the end
- Steam ID field is set to `None` by default and can be populated by user later
