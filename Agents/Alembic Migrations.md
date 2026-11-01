# Alembic --- Database Migrations with SQLAlchemy

## 1. The Fundamental Difference

**SQLAlchemy interacts with the database. Alembic manages and versions
changes to the database schema.**

  -----------------------------------------------------------------------
  SQLAlchemy                          Alembic
  ----------------------------------- -----------------------------------
  ORM and SQL toolkit                 Database migration tool

  Defines tables through Python       Manages schema changes over time
  models                              

  Reads, inserts, updates, and        Adds, removes, or modifies tables,
  deletes records                     columns, and indexes

  Handles runtime database operations Handles schema evolution
  -----------------------------------------------------------------------

A SQLAlchemy model describes the desired table structure. Defining or
changing a model does **not** automatically update an existing database.

## 2. Why Do We Need Migrations?

Imagine an e-commerce application with a `customers` table:

    id name    email
  ---- ------- -----------------
     1 Rahul   rahul@gmail.com
     2 Aman    aman@gmail.com

A new requirement asks us to store each customer's phone number.

The database schema must change:

``` sql
ALTER TABLE customers
ADD COLUMN phone VARCHAR(15);
```

In a team, there may be multiple database environments:

-   A developer's local database
-   A teammate's local database
-   A staging database
-   The production database

Manually executing SQL changes in every environment is error-prone. A
migration records the change in a version-controlled file so it can be
applied consistently.

## 3. What Is Alembic?

Alembic is a database migration tool designed to work with SQLAlchemy.

It maintains a history of database schema changes, for example:

1.  **Migration 001:** Create the `customers` table.
2.  **Migration 002:** Add the `phone` column.
3.  **Migration 003:** Create the `orders` table.
4.  **Migration 004:** Add an index for order queries.

The database records its currently applied migration revision in a table
named `alembic_version`.

This lets Alembic determine which migrations have already been applied
and which are pending.

> Mental model: Alembic is somewhat like Git history, but for database
> schema changes. The analogy is useful, although Git and Alembic are
> not the same system.

## 4. How SQLAlchemy Models Connect to Alembic

Example SQLAlchemy model:

``` python
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255))
```

This model describes the desired structure of the `customers` table.

Alembic needs access to the SQLAlchemy metadata to compare the model
definitions with the actual database schema.

In `alembic/env.py`:

``` python
from app.database import Base
from app import models

target_metadata = Base.metadata
```

Importing the models matters: it ensures their table definitions have
been registered with `Base.metadata`.

## 5. Hands-On: Alembic Workflow

### Step 1 --- Initialize Alembic

``` bash
alembic init alembic
```

This creates a structure similar to:

``` text
project/
├── alembic/
│   ├── versions/
│   ├── env.py
│   └── script.py.mako
└── alembic.ini
```

  File/folder           Purpose
  --------------------- ---------------------------------------------------
  `alembic/env.py`      Configures the migration environment and metadata
  `alembic/versions/`   Stores migration files
  `alembic.ini`         Main Alembic configuration
  `script.py.mako`      Template used to generate migration scripts

### Step 2 --- Configure metadata

In `alembic/env.py`, provide the metadata from your application's
SQLAlchemy models:

``` python
from app.database import Base
from app import models

target_metadata = Base.metadata
```

Configure the database URL using your project's configuration. Avoid
hardcoding production credentials in source control.

### Step 3 --- Generate the initial migration

``` bash
alembic revision --autogenerate -m "create customers table"
```

Alembic compares:

-   The actual database schema
-   The SQLAlchemy model metadata

It then generates a migration file containing detected differences.

Example generated migration:

``` python
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
        "customers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=100)),
    )

def downgrade():
    op.drop_table("customers")
```

### Step 4 --- Understand `upgrade()` and `downgrade()`

-   **`upgrade()`** applies the schema change and moves the database
    forward.
-   **`downgrade()`** reverses that migration's schema change.

A downgrade is not necessarily a recovery mechanism for data. For
example, dropping a column can permanently delete the values stored in
it.

### Step 5 --- Apply the migration

``` bash
alembic upgrade head
```

`head` means the latest revision in the migration history.

This command applies pending migrations up to that revision. It is the
step that actually changes the database.

### Step 6 --- Add a new model field

Suppose the `Customer` model now includes a phone number:

``` python
class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(
        String(15),
        nullable=True,
    )
```

Generate a new migration:

``` bash
alembic revision --autogenerate -m "add customer phone"
```

A generated migration may look like:

``` python
def upgrade():
    op.add_column(
        "customers",
        sa.Column("phone", sa.String(length=15), nullable=True),
    )

def downgrade():
    op.drop_column("customers", "phone")
```

Review the migration, then apply it:

``` bash
alembic upgrade head
```

The PostgreSQL database now has the `phone` column.

## 6. Important: Autogenerate Is Not Perfect

`--autogenerate` creates a candidate migration. It does **not**
guarantee a correct migration, and it does not apply the migration.

Always inspect the generated file before running `upgrade`.

Pay particular attention to:

-   Column renames: a rename may be detected as a drop plus an add.
-   Constraint changes: verify the intended constraints are preserved.
-   Data migrations: existing rows may need transformation or
    backfilling.
-   Nullable changes: adding a non-null column to a populated table may
    require a default or a staged migration.

The safe workflow is:

``` text
Update SQLAlchemy model
        |
        v
Generate migration
        |
        v
Review and edit migration
        |
        v
Apply migration
        |
        v
Verify database schema and application
```

## 7. Essential Alembic Commands

  ------------------------------------------------------------------------------------
  Command                                          Purpose
  ------------------------------------------------ -----------------------------------
  `alembic init alembic`                           Initialize Alembic

  `alembic revision -m "message"`                  Create an empty migration

  `alembic revision --autogenerate -m "message"`   Generate a migration from detected
                                                   model/schema differences

  `alembic upgrade head`                           Apply migrations up to the latest
                                                   revision

  `alembic upgrade +1`                             Move forward by one revision

  `alembic downgrade -1`                           Roll back one revision

  `alembic downgrade base`                         Roll back all revisions

  `alembic current`                                Show the database's current
                                                   revision

  `alembic history`                                Show migration history

  `alembic heads`                                  Show current migration heads
  ------------------------------------------------------------------------------------

## 8. Team and Production Workflow

Imagine three developers make separate schema changes:

-   Developer A adds a `phone` column.
-   Developer B adds an `address` column.
-   Developer C creates an `orders` table.

Each change should be represented by a migration file and reviewed
through version control.

During deployment, the team runs:

``` bash
alembic upgrade head
```

This applies the pending migrations in revision order, subject to the
migration graph.

Benefits:

-   Consistent schema changes across environments
-   Version-controlled migration history
-   Reviewable database changes
-   Repeatable deployments
-   A defined reverse schema operation where one is safe and possible

### Production warning

Do not assume every migration can be safely rolled back. A migration
that drops a column or deletes data may be destructive. Backups and a
deliberate recovery plan are still necessary.

For high-traffic systems, schema changes may need an expand-and-contract
approach so old and new application versions can coexist during
deployment.

## 9. Applying Alembic to the Customer Support Agent

The project's initial SQLAlchemy models are:

-   `Customer`
-   `Order`
-   `SupportTicket`
-   `AgentRun`
-   `AgentToolCall`

The initial migration will create the required tables. Later, if a
feature introduces a `ticket_priority` column, update the model,
generate a migration, review it, and apply it.

``` text
models.py
    |
    | SQLAlchemy model definitions
    v
Base.metadata
    |
    | Alembic autogenerate compares metadata
    v
Migration file in alembic/versions/
    |
    | Review migration
    v
alembic upgrade head
    |
    v
PostgreSQL schema updated
```

## 10. Interview Questions

### Q1. What is Alembic?

Alembic is a database migration tool for SQLAlchemy. It tracks and
applies versioned database schema changes.

### Q2. What is the difference between SQLAlchemy and Alembic?

SQLAlchemy defines models and provides database interaction. Alembic
manages changes to the database schema over time through migrations.

### Q3. What does `target_metadata` do?

It gives Alembic access to SQLAlchemy table metadata so autogenerate can
compare model definitions with the database schema.

### Q4. What does `alembic upgrade head` do?

It applies all pending migrations up to the latest revision.

### Q5. What is the purpose of `downgrade()`?

It defines the reverse schema operation for a migration. It does not
guarantee recovery of data lost by destructive changes.

### Q6. Does changing a SQLAlchemy model automatically change PostgreSQL?

No. The model describes the intended structure. A migration must be
generated, reviewed, and applied to update the database schema.

### Q7. Is autogenerate always correct?

No. It detects many schema differences, but generated migrations must be
reviewed, especially for renames, constraints, and data transformations.

## 11. Quick Revision

-   SQLAlchemy defines models and interacts with the database.
-   Alembic manages versioned schema changes.
-   A migration is a version-controlled description of a schema change.
-   `env.py` configures Alembic and exposes `target_metadata`.
-   `versions/` stores migration scripts.
-   `upgrade()` moves the schema forward.
-   `downgrade()` reverses a schema operation where possible.
-   `alembic_version` tracks the current applied revision.
-   `--autogenerate` generates a candidate migration; it does not apply
    it.
-   `alembic upgrade head` applies pending migrations up to the latest
    revision.

**Remember:** Model change → Generate migration → Review migration →
Apply migration.
