import re,json,uuid,hashlib,os
from pathlib import Path
from datetime import date,datetime,timedelta
import pandas as pd,fitz
from docx import Document
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError,VerificationError
from backend.db import all,one,run
from backend.db import ROOT
UPLOAD=Path(os.getenv('RESUME_STORAGE_DIR','private_uploads'));UPLOAD=UPLOAD if UPLOAD.is_absolute() else ROOT/UPLOAD
MAX_MB=int(os.getenv('MAX_RESUME_SIZE_MB','5'));PH=PasswordHasher()
STATUSES=['Interested','Saved','Applied','Assessment','Shortlisted','Interview Scheduled','Offer Received','Rejected','Withdrawn']
def pw_hash(p):
 if len(p)<10 or not re.search(r'[A-Za-z]',p) or not re.search(r'\d',p):raise ValueError('Use at least 10 characters with a letter and a number.')
 return PH.hash(p)
def verify(h,p):
 try:return PH.verify(h,p)
 except (VerifyMismatchError,VerificationError,ValueError):return False
def register(name,email,p,conf):
 name=name.strip();email=email.strip().lower()
 if len(name)<2:raise ValueError('Enter your full name.')
 if not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+',email):raise ValueError('Enter a valid email.')
 if p!=conf:raise ValueError('Passwords do not match.')
 if one('SELECT id FROM users WHERE email=%s',(email,)):raise ValueError('Email already registered.')
 uid=run('INSERT INTO users(full_name,email,password_hash) VALUES(%s,%s,%s)',(name,email,pw_hash(p)))
 run('INSERT INTO user_preferences(user_id,roles_json,locations_json) VALUES(%s,%s,%s)',(uid,'[]','[]'))
 return {'id':uid,'full_name':name,'email':email}
def login(email,p):
 u=one('SELECT id,full_name,email,password_hash FROM users WHERE email=%s',(email.strip().lower(),))
 if not u or not verify(u['password_hash'],p):raise ValueError('Invalid email or password.')
 return {k:u[k] for k in ('id','full_name','email')}
def change_pw(uid,old,new,conf):
 u=one('SELECT password_hash FROM users WHERE id=%s',(uid,))
 if not u or not verify(u['password_hash'],old):raise ValueError('Current password is incorrect.')
 if new!=conf:raise ValueError('Passwords do not match.')
 run('UPDATE users SET password_hash=%s WHERE id=%s',(pw_hash(new),uid))
def jobs():return pd.read_csv(ROOT/'data'/'jobs.csv').fillna('')
def prefs(uid):
 p=one('SELECT * FROM user_preferences WHERE user_id=%s',(uid,)) or {'roles_json':'[]','locations_json':'[]','work_mode':'Any','experience_level':'Any','employment_type':'Any','min_salary':None,'max_salary':None}
 p['roles']=json.loads(p.pop('roles_json'));p['locations']=json.loads(p.pop('locations_json'));return p
def save_prefs(uid,roles,locs,mode,level,typ,mn,mx):
 if mn and mx and mn>mx:raise ValueError('Minimum salary cannot exceed maximum salary.')
 run('UPDATE user_preferences SET roles_json=%s,locations_json=%s,work_mode=%s,experience_level=%s,employment_type=%s,min_salary=%s,max_salary=%s WHERE user_id=%s',(json.dumps(roles),json.dumps(locs),mode,level,typ,mn or None,mx or None,uid))
def resumes(uid):return all('SELECT id,label,original_name,extracted_text,is_active,created_at FROM resumes WHERE user_id=%s ORDER BY id DESC',(uid,))
def active_resume(uid):return one('SELECT * FROM resumes WHERE user_id=%s AND is_active=1 ORDER BY id DESC LIMIT 1',(uid,))
def add_resume(uid,label,name,data):
 if len(data)>MAX_MB*1024*1024:raise ValueError(f'Maximum file size is {MAX_MB} MB.')
 suffix=Path(name).suffix.lower()
 if suffix=='.pdf':
  if not data.startswith(b'%PDF'):raise ValueError('Invalid PDF file.')
  d=fitz.open(stream=data,filetype='pdf');txt='\n'.join(p.get_text() for p in d);d.close()
 elif suffix=='.docx':
  if not data.startswith(b'PK'):raise ValueError('Invalid DOCX file.')
  import io;d=Document(io.BytesIO(data));txt='\n'.join(p.text for p in d.paragraphs)
 else:raise ValueError('Only PDF and DOCX files are supported.')
 if not txt.strip():raise ValueError('No embedded text found. Scanned image-only PDFs are not supported.')
 UPLOAD.mkdir(parents=True,exist_ok=True);stored=uuid.uuid4().hex+suffix;(UPLOAD/stored).write_bytes(data)
 run('UPDATE resumes SET is_active=0 WHERE user_id=%s',(uid,))
 return run('INSERT INTO resumes(user_id,label,storage_name,original_name,extracted_text,is_active) VALUES(%s,%s,%s,%s,%s,1)',(uid,(label.strip() or Path(name).stem)[:160],stored,Path(name).name,txt[:500000]))
def set_active(uid,rid):
 if not one('SELECT id FROM resumes WHERE id=%s AND user_id=%s',(rid,uid)):raise ValueError('Resume not found.')
 run('UPDATE resumes SET is_active=0 WHERE user_id=%s',(uid,));run('UPDATE resumes SET is_active=1 WHERE id=%s AND user_id=%s',(rid,uid))
def delete_resume(uid,rid):
 r=one('SELECT storage_name FROM resumes WHERE id=%s AND user_id=%s',(rid,uid))
 if not r:raise ValueError('Resume not found.')
 try:(UPLOAD/r['storage_name']).unlink(missing_ok=True)
 except OSError:pass
 run('DELETE FROM resumes WHERE id=%s AND user_id=%s',(rid,uid))
def save_job(uid,jid):
 df=jobs();m=df[df.job_id.astype(str)==str(jid)]
 if m.empty:raise ValueError('Sample job not found.')
 j=m.iloc[0];run('INSERT INTO saved_jobs(user_id,job_id,title,company,location,description,skills,notes) VALUES(%s,%s,%s,%s,%s,%s,%s,'') ON DUPLICATE KEY UPDATE title=VALUES(title),company=VALUES(company),location=VALUES(location)',(uid,str(j.job_id),str(j.title),str(j.company),str(j.location),str(j.description),str(j.skills)))
def saved(uid):return all('SELECT * FROM saved_jobs WHERE user_id=%s ORDER BY saved_at DESC',(uid,))
def applications(uid):return all('SELECT * FROM applications WHERE user_id=%s ORDER BY updated_at DESC',(uid,))
def add_app(uid,title,company,loc,jid,status,notes,follow,resume_id=None,letter=''):
 if status not in STATUSES:raise ValueError('Invalid status.')
 run('INSERT INTO applications(user_id,job_id,title,company,location,status,date_added,date_applied,resume_id,cover_letter,notes,follow_up_date,confirmed_submitted) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(uid,jid,title,company,loc,status,date.today(),date.today() if status=='Applied' else None,resume_id,letter,notes,follow,1 if status=='Applied' else 0))
def update_app(uid,aid,status,notes,follow):
 if status not in STATUSES:raise ValueError('Invalid status.')
 run("UPDATE applications SET status=%s,notes=%s,follow_up_date=%s,date_applied=CASE WHEN %s='Applied' AND date_applied IS NULL THEN %s ELSE date_applied END,confirmed_submitted=CASE WHEN %s='Applied' THEN 1 ELSE confirmed_submitted END WHERE id=%s AND user_id=%s",(status,notes,follow,status,date.today(),status,aid,uid))
def match(text,desc):
 from sklearn.feature_extraction.text import TfidfVectorizer
 from sklearn.metrics.pairwise import cosine_similarity
 if not text.strip():raise ValueError('Upload and activate a resume first.')
 try:m=TfidfVectorizer(stop_words='english',ngram_range=(1,2)).fit_transform([text,desc]);score=round(float(cosine_similarity(m[0:1],m[1:2])[0][0])*100)
 except ValueError:score=0
 words=lambda s:set(re.findall(r'[a-zA-Z][a-zA-Z0-9+#.]{2,}',s.lower()))
 return score,sorted(words(text)&words(desc)),sorted(words(desc)-words(text))
def letter(name,text,title,company):
 excerpt=' '.join(x.strip() for x in text.splitlines() if x.strip())[:500]
 return f'Dear Hiring Team,\n\nI am writing to express my interest in the {title} position at {company or "your organization"}. My resume includes: {excerpt or "the skills and experience described in my resume"}.\n\nI would welcome the opportunity to discuss how my background may align with your team’s needs. Thank you for your time and consideration.\n\nSincerely,\n{name}'
def drafts(uid):return all('SELECT * FROM cover_letter_drafts WHERE user_id=%s ORDER BY updated_at DESC',(uid,))
def save_draft(uid,title,body):
 if not body.strip():raise ValueError('Draft cannot be empty.')
 return run('INSERT INTO cover_letter_drafts(user_id,title,body) VALUES(%s,%s,%s)',(uid,title,body))
