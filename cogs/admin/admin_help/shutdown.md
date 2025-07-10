## ~shutdown [inform_admin] [description]

Gracefully shuts down the bot process, with optional admin notification

**Usage:**
`~shutdown [inform_admin] [description]`
Example: `~shutdown true Emergency server update`

**Who can use:**
Guildmaster, Oracle, V

**Details:**

- Announces shutdown in the channel, writes status to the database
- Optionally sends a DM to V (if `inform_admin` is `true`) with an optional description
- Use before planned restarts, server moves, or emergencies
- All commands and connections are stopped after this is run
