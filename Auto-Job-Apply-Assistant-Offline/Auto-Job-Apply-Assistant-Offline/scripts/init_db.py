from backend.db import CFG,ROOT
import mysql.connector
def main():
 cfg=dict(CFG);db=cfg.pop('database')
 if not cfg.get('user') or not cfg.get('password'):raise SystemExit('Set MYSQL_USER and MYSQL_PASSWORD in .env first.')
 c=mysql.connector.connect(**cfg)
 try:
  q=c.cursor();q.execute(f'CREATE DATABASE IF NOT EXISTS `{db}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci');q.execute(f'USE `{db}`')
  for s in (ROOT/'schema.sql').read_text(encoding='utf-8').split(';'):
   s=s.strip()
   if s and not s.upper().startswith('CREATE DATABASE') and not s.upper().startswith('USE '):q.execute(s)
  c.commit();print(f'Database schema initialized in `{db}`.')
 finally:q.close();c.close()
if __name__=='__main__':main()
