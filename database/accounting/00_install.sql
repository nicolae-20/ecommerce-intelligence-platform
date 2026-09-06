-- Oracle Accounting Bootstrap
-- Fresh schema only. This script intentionally does not reset existing data.

SET SQLBLANKLINES ON
WHENEVER SQLERROR EXIT SQL.SQLCODE ROLLBACK

@@01_schema.sql
@@02_seed_demo.sql
@@03_reconciliation.sql
