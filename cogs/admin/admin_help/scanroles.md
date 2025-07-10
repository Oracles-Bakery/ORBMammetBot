## ~scanroles

Scans all roles in the server and stores/updates them in the database

**Usage:**
`~scanroles`

**Who can use:**
Oracle, Guildmaster, V

**Details:**

- Skips the `@everyone` role, managed roles, and roles with names starting with "↳" to avoid the categor identifiers
- Updates or adds each role in the database
- Reports how many were stored/updated and how many skipped
- Useful after role restructuring or when adding new roles
- Primarily for the initialisation stage of the bot though
