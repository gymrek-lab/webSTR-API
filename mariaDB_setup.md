# MariaDB Setup and Configuration 


## 1. Install MariaDB

### Ubuntu/Debian:

```bash
sudo apt update
sudo apt install mariadb-server
```

### CentOS/RHEL:

```bash
sudo yum install mariadb-server
```


## 2. Start and Secure MariaDB

Start the MariaDB service and ensure it runs on startup:

```bash
sudo systemctl start mariadb
sudo systemctl enable mariadb
```

Run the following command to secure the MariaDB installation:

```bash
sudo mysql_secure_installation
```

**Note**: The original database setup included the following configurations:
- Removed anonymous users
- Disabled remote root login
- Deleted the default test database


## 3. Create a Database and Non-Root User

Log in to the MariaDB shell as the root user:

```bash
sudo mysql -u root -p
```

Run the following commands to create a new database and user, and grant the necessary permissions:

```sql
CREATE DATABASE testdb;
CREATE USER 'your_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON testdb.* TO 'your_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

## 4. Configure Your Application


### Example:

```bash
export DATABASE_URL="mysql+pymysql://your_user:your_password@localhost:3306/testdb"
```


## 5. Run FastAPI App

```bash
uvicorn strAPI.main:app --host=0.0.0.0 --port=5000 --reload
```

## Useful Commands for MariaDB


1. **Check if MariaDB is running**:
   ```bash
   sudo systemctl status mariadb
   ```

2. **Start MariaDB**:
   ```bash
   sudo systemctl start mariadb
   ```

3. **Stop MariaDB**:
   ```bash
   sudo systemctl stop mariadb
   ```

4. **Log into MariaDB**:
   ```bash
   sudo mysql -u root -p
   ```

5. **Show all databases**:
   ```sql
   SHOW DATABASES;
   ```

6. **Select a database**:
   ```sql
   USE testdb;
   ```

7. **Show all tables in a database**:
   ```sql
   SHOW TABLES;
   ```

8. **Describe a table (view table structure and data types)**:
   ```sql
   DESCRIBE table_name;
   ```

9. **View the first few rows of a table**:
   ```sql
   SELECT * FROM table_name LIMIT 5;
   ```

10. **Create a new table**:
   ```sql
   CREATE TABLE example_table (
     id INT AUTO_INCREMENT PRIMARY KEY,
     name VARCHAR(100),
     age INT
   );
   ```

11. **Insert data into a table**:
   ```sql
   INSERT INTO example_table (name, age) VALUES ('Alice', 30);
   ```

12. **Update data in a table**:
   ```sql
   UPDATE example_table SET age = 31 WHERE name = 'Alice';
   ```

13. **Delete data from a table**:
   ```sql
   DELETE FROM example_table WHERE name = 'Alice';
   ```

14. **Drop (delete) a table**:
   ```sql
   DROP TABLE example_table;
   ```

15. **Check users in MariaDB**:
   ```sql
   SELECT user, host FROM mysql.user;
   ```
