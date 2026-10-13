# Synthetic sample: Introduction to Database Design

This fictional study material was written solely for public application screenshots.

## Page 1: Tables and keys

A relational database stores information in tables. Each table contains rows and columns.
A primary key uniquely identifies each row in a table. A foreign key references a key in another table and connects related records.
For example, a fictional library database can have Books and Loans tables. BookID is the primary key of Books. The BookID column in Loans is a foreign key referencing Books.
Referential integrity prevents a loan from referencing a book that does not exist.

## Page 2: Normalization

Normalization organizes relational tables to reduce repeated data and avoid update anomalies.
First normal form requires each field to contain a single value and each row to be identifiable.
Second normal form requires first normal form and removes partial dependencies on a composite primary key.
Third normal form requires second normal form and removes transitive dependencies between non-key attributes.
In a fictional inventory system, product category descriptions belong in a Categories table instead of being repeated for every product.

## Page 3: Queries and indexes

SQL is used to query and modify relational data. SELECT retrieves rows. WHERE filters rows. JOIN combines related tables using matching values.
An index can improve lookup speed but requires storage and may slow down inserts and updates.
A transaction groups operations into one unit. COMMIT saves the changes, and ROLLBACK cancels uncommitted changes.
Parameterized queries separate SQL statements from input values and help prevent SQL injection.
