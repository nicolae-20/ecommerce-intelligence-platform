# Oracle Accounting Bootstrap

This directory reproduces the current accounting and reconciliation database
contract from tracked files. It is intended for a fresh Oracle schema.

## Install order

Run `00_install.sql` with an Oracle SQL client that supports `@@` relative
script includes. The installer explicitly sets `SQLBLANKLINES ON` because the
schema DDL intentionally uses readable multi-line statements containing blank
lines; it therefore does not depend on a local SQL*Plus default. It also sets
`WHENEVER SQLERROR EXIT SQL.SQLCODE ROLLBACK`, so SQL*Plus or SQLcl stops on
the first Oracle SQL error rather than intentionally continuing to later
includes. SQL*Plus client-command errors and Oracle SQL errors are different
error classes.
It executes:

1. `01_schema.sql`
2. `02_seed_demo.sql`
3. `03_reconciliation.sql`

## Fresh-schema prerequisites

Before running the installer, provision the schema/user in the intended
application PDB and service. The demonstrated working contract for this
project, verified using `FREEPDB1`, includes:

* `CREATE SESSION` to connect as the fresh schema.
* `CREATE TABLE` to create the accounting tables and constraints.
* `CREATE PROCEDURE` to create `RECONCILE_BANK_TRANSACTIONS`.
* `CREATE SEQUENCE`, which is required by the Oracle identity-column
  generators used by this schema.
* A 50 MB quota on the `USERS` tablespace so the schema can allocate the
  table, index, and identity-related storage used by the bootstrap.

The tested 50 MB quota was sufficient for this small bootstrap/demo dataset.
This is the demonstrated working contract for this project, not a claim of
universal Oracle privilege minimality across every Oracle installation.
Administrative user creation and privilege granting should be performed
separately by an appropriately privileged administrator. This bootstrap does
not create or drop Oracle users and does not grant system privileges.

The schema creates `ACCOUNTING_CATEGORIES`, `FINANCIAL_TRANSACTIONS`,
`BANK_TRANSACTIONS`, and `AUDIT_LOG`. The seed adds eight deterministic
categories, five synthetic financial transactions, and four synthetic bank
transactions. It deliberately seeds no audit history.

Identity values rely on fresh-schema insertion order: categories receive IDs
1 through 8, financial transactions IDs 1 through 5, and bank transactions
IDs 1 through 4. The seed script follows the repository convention of an
explicit final `COMMIT`.

Normal bootstrap never drops, truncates, deletes, or resets data. If table
creation fails because objects already exist, the installer exits before it
intentionally runs later seed or procedure includes. Oracle DDL can still have
implicit-commit effects before a later failure, so this is not a general
rollback-safe migration system. The reconciliation procedure uses `CREATE OR
REPLACE`, matching the existing procedure installation behavior, and retains
its current internal `COMMIT`.

Do not run this bootstrap against a schema containing important existing data
without deliberate review. No reset script is included.

This bootstrap captures current behavior rather than correcting known future
work such as category/accounting-category alignment, reconciliation-state
asymmetry, or multi-candidate matching semantics.
