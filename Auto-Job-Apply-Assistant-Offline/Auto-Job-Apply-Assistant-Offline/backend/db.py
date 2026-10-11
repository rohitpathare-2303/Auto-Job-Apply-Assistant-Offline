import os
from pathlib import Path
from dotenv import load_dotenv
import mysql.connector

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / '.env', override=True)

HOST = os.getenv('MYSQL_HOST', '127.0.0.1')

CFG = {
    'host': HOST,
    'port': int(os.getenv('MYSQL_PORT', '3306')),
    'database': os.getenv('MYSQL_DATABASE', 'auto_job_assistant_offline'),
    'user': os.getenv('MYSQL_USER', ''),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'charset': 'utf8mb4',
    'connection_timeout': 8,
    'autocommit': False,
}

# Use SSL only for hosted databases (TiDB Cloud etc.), not for local MySQL
if HOST not in ('127.0.0.1', 'localhost'):
    try:
        import certifi
        CFG['ssl_ca'] = certifi.where()
    except ImportError:
        CFG['ssl_ca'] = '/etc/ssl/certs/ca-certificates.crt'
    CFG['ssl_verify_cert'] = True


def connect():
    if not CFG['user'] or not CFG['password']:
        raise RuntimeError('Set MYSQL_USER and MYSQL_PASSWORD in the real .env file.')
    try:
        return mysql.connector.connect(**CFG)
    except mysql.connector.Error as e:
        if getattr(e, 'errno', None) == 1045:
            raise RuntimeError('MySQL access denied. Match the username/password in .env with MySQL Workbench.') from e
        raise RuntimeError(f'MySQL connection failed: {e}. Check that MySQL Server is running and schema.sql was executed.') from e


def all(sql, args=()):
    c = connect()
    try:
        q = c.cursor(dictionary=True)
        q.execute(sql, args)
        return q.fetchall()
    finally:
        q.close()
        c.close()


def one(sql, args=()):
    r = all(sql, args)
    return r[0] if r else None


def run(sql, args=()):
    c = connect()
    try:
        q = c.cursor()
        q.execute(sql, args)
        c.commit()
        return q.lastrowid
    except Exception:
        c.rollback()
        raise
    finally:
        q.close()
        c.close()
