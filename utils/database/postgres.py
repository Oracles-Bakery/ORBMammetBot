import asyncpg
import settings

_pool = None

###################
### The Basics™ ###
###################

# Ensure the database connection pool is initialized
def ensure_pool():
    if _pool is None:
        raise RuntimeError("Database not connected. Call connect() first.")

# Connect to the database and create a connection pool
async def connect():
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(dsn=settings.DATABASE_URL)

# Close the database connection pool
async def close():
    global _pool
    if _pool:
        await _pool.close() 
        _pool = None

# Fetch a single value from the database
async def fetchval(query, *args):
    ensure_pool()
    async with _pool.acquire() as conn: # type: ignore
        return await conn.fetchval(query, *args)

# Fetch multiple rows from the database
async def fetch(query, *args):
    ensure_pool()
    async with _pool.acquire() as conn: # type: ignore
        return await conn.fetch(query, *args)

# Execute a query and return the result
async def execute(query, *args):
    ensure_pool()
    async with _pool.acquire() as conn: # type: ignore
        return await conn.execute(query, *args)

# Return the first row of the result set
async def fetchrow(query, *args):
    ensure_pool()
    async with _pool.acquire() as conn: # type: ignore
        return await conn.fetchrow(query, *args)
    
####################
### HEALTH CHECK ###
####################

# Grab the info that a table is built on
def parse_sql_schema(sql_text):
    tables = {}
    create_table_pattern = re.compile(r'CREATE TABLE IF NOT EXISTS (\w+)\s*\((.*?)\);', re.DOTALL | re.IGNORECASE)
    for match in create_table_pattern.finditer(sql_text):
        table_name = match.group(1)
        columns_section = match.group(2)
        columns = []
        for col_line in columns_section.splitlines():
            col_line = col_line.strip()
            if not col_line or col_line.startswith('--') or 'PRIMARY KEY' in col_line or 'FOREIGN KEY' in col_line:
                continue
            col_name = col_line.split()[0]
            columns.append(col_name)
        tables[table_name] = columns
    return tables

# Grab that whol mfer
async def get_actual_schema():
    schema = {}
    rows = await postgres.fetch("""
        SELECT table_name, column_name
        FROM information_schema.columns
        WHERE table_schema='public'
        ORDER BY table_name, ordinal_position;
    """)
    for row in rows:
        schema.setdefault(row['table_name'], []).append(row['column_name'])
    return schema

# Compare the schema of the actual table against what is expected
def compare_schemas(expected, actual):
    issues = []
    for table, exp_cols in expected.items():
        if table not in actual:
            issues.append(f"Table `{table}` is missing from DB!")
            continue
        for col in exp_cols:
            if col not in actual[table]:
                issues.append(f"Column `{col}` missing from table `{table}`.")
    for table in actual:
        if table not in expected:
            issues.append(f"Extra table `{table}` present in DB (not in SQL).")
        else:
            for col in actual[table]:
                if col not in expected[table]:
                    issues.append(f"Extra column `{col}` present in table `{table}`.")
    return issues



######################################
### Consistent Channels Management ###
######################################

async def upsert_consistent_channel(purpose: str, channel_id: int, message_id: int):
    ensure_pool()
    query = """
        INSERT INTO consistentchannels (purpose, channel_id, message_id)
        VALUES ($1, $2, $3)
        ON CONFLICT (purpose) DO UPDATE
        SET channel_id = EXCLUDED.channel_id,
            message_id = EXCLUDED.message_id
    """
    async with _pool.acquire() as conn: # type: ignore
        await conn.execute(query, purpose, channel_id, message_id)

async def get_consistent_channel_by_purpose(purpose: str):
    ensure_pool()
    query = "SELECT * FROM consistentchannels WHERE purpose = $1 LIMIT 1"
    async with _pool.acquire() as conn: # type: ignore
        return await conn.fetchrow(query, purpose)

async def fetch_all_consistent_channels():
    """
    Fetches all rows from consistentChannels.
    """
    ensure_pool()
    query = "SELECT * FROM consistentChannels"
    return await fetch(query)

################################
### Discord Roles Management ###
################################

async def upsert_role(role_id: int, role_name: str, emoji_id: int | None = None):
    ensure_pool()
    query = """
        INSERT INTO discord_roles (role_id, role_name, emoji_id)
        VALUES ($1, $2, $3)
        ON CONFLICT (role_id) DO UPDATE
        SET role_name = EXCLUDED.role_name,
            emoji_id = EXCLUDED.emoji_id
    """
    async with _pool.acquire() as conn: # type: ignore
        await conn.execute(query, role_id, role_name, emoji_id)

async def get_role_by_id(role_id: int):
    ensure_pool()
    query = """
        SELECT * FROM discord_roles WHERE role_id = $1
    """
    async with _pool.acquire() as conn: # type: ignore
        return await conn.fetchrow(query, role_id)

async def get_roles_by_category(category: str):
    ensure_pool()
    query = """
        SELECT role_name FROM discord_roles
        WHERE category = $1
        ORDER BY role_name ASC
    """
    async with _pool.acquire() as conn: # type: ignore
        return await conn.fetch(query, category)
