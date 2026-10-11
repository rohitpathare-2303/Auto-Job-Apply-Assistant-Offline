import streamlit as st,pandas as pd
from backend import services as s
from backend.db import connect,run
from datetime import date
st.set_page_config(page_title='Career Studio Offline',page_icon='✦',layout='wide')
st.markdown("""<style>.block-container{max-width:1400px;padding-top:1.4rem}.hero{padding:1.7rem 2rem;border:1px solid #2b4067;border-radius:20px;background:linear-gradient(120deg,#182e51,#151b32 70%,#292348);margin-bottom:1.2rem}.eyebrow{color:#9cb4ff;letter-spacing:.16em;font-size:.72rem;font-weight:700}.hero h1{font-size:2.2rem;letter-spacing:-.04em;margin:.3rem 0}.hero p{color:#b8c8e4;margin:0}.metric{border:1px solid #2a3a56;background:#111c2f;border-radius:16px;padding:1rem}.metric small{color:#a8b8d0}.metric strong{display:block;font-size:1.8rem}.stButton button{border-radius:10px;font-weight:650}</style>""",unsafe_allow_html=True)
def hero(t,sub):st.markdown(f'<div class="hero"><div class="eyebrow">OFFLINE CAREER WORKSPACE</div><h1>{t}</h1><p>{sub}</p></div>',unsafe_allow_html=True)
def metric(label,val):st.markdown(f'<div class="metric"><small>{label}</small><strong>{val}</strong></div>',unsafe_allow_html=True)
def ready():
 try:c=connect();c.close();return True
 except Exception as e:st.error(str(e));st.info('Start MySQL Server, verify .env, and run schema.sql in Workbench as administrator if needed.');return False
if 'user' not in st.session_state:st.session_state.user=None
if 'page' not in st.session_state:st.session_state.page='Dashboard'
if not st.session_state.user:
 hero('Your next role starts here.','A polished job-search workspace powered by a bundled static dataset. No APIs or external job feeds.')
 a,b=st.columns([1.15,.85],gap='large')
 with a:
  st.markdown('### Career tools, one workspace')
  st.markdown('**120 fictional demo listings** · Resume PDF/DOCX analysis · Keyword matching · Saved jobs · Application pipeline · Cover-letter drafts · MySQL-backed user accounts')
  st.info('All jobs and company names are synthetic sample data, not live vacancies. The app never submits applications automatically.')
 with b:
  mode=st.radio('Welcome',['Sign in','Create account'],horizontal=True)
  if mode=='Sign in':
   with st.form('login'):
    email=st.text_input('Email');pw=st.text_input('Password',type='password');go=st.form_submit_button('Sign in',use_container_width=True)
   if go and ready():
    try:st.session_state.user=s.login(email,pw);st.rerun()
    except Exception as e:st.error(str(e))
  else:
   with st.form('register'):
    name=st.text_input('Full name');email=st.text_input('Email');pw=st.text_input('Password (10+ chars, letter and number)',type='password');conf=st.text_input('Confirm password',type='password');go=st.form_submit_button('Create account',use_container_width=True)
   if go and ready():
    try:st.session_state.user=s.register(name,email,pw,conf);st.success('Account created');st.rerun()
    except Exception as e:st.error(str(e))
 st.stop()
u=st.session_state.user;uid=u['id']
with st.sidebar:
 st.markdown('## ✦ Career Studio');st.caption('Static dataset edition');st.markdown(f"**{u['full_name']}**");st.caption(u['email']);st.divider()
 pages=['Dashboard','Find Jobs','Resume Lab','Saved Jobs','Applications','Cover Letters','Preferences','Account']
 page=st.radio('WORKSPACE',pages,index=pages.index(st.session_state.page));st.session_state.page=page;st.divider();st.caption('120 fictional listings · no API')
 if st.button('Log out',use_container_width=True):st.session_state.user=None;st.rerun()
try:
 if page=='Dashboard':
  hero(f"Welcome back, {u['full_name'].split()[0]}.",'Your career pipeline, resume insights and saved opportunities at a glance.')
  apps=s.applications(uid);saved=s.saved(uid);resume=s.active_resume(uid);cols=st.columns(4)
  for col,label,val in zip(cols,['Applications','Saved jobs','Interviews','Active resume'],[len(apps),len(saved),sum(a['status']=='Interview Scheduled' for a in apps),'Ready' if resume else 'Missing']):
   with col:metric(label,val)
  st.markdown('### Your application pipeline')
  if apps:st.dataframe(pd.DataFrame([{'Role':a['title'],'Company':a['company'],'Status':a['status'],'Follow-up':str(a['follow_up_date'] or '—')} for a in apps]),use_container_width=True,hide_index=True)
  else:st.info('Your pipeline is empty. Search the sample dataset and track a role.')
  st.markdown('### Explore sample roles');df=s.jobs().head(6);cols=st.columns(3)
  for i,(_,j) in enumerate(df.iterrows()):
   with cols[i%3]:
    st.markdown(f"**{j.title}**  \n{j.company}  \n<small>{j.location} · {j.work_mode} · {j.category}</small>",unsafe_allow_html=True)
    if st.button('Find this role',key=f'rec{i}'):st.session_state.query=j.title;st.session_state.page='Find Jobs';st.rerun()
 elif page=='Find Jobs':
  hero('Find your next opportunity.','Search 120 fictional listings bundled with this project. Works offline.')
  df=s.jobs()
  with st.form('filters'):
   q=st.text_input('Search title, company, skills or description',value=st.session_state.get('query',''));c1,c2,c3=st.columns(3)
   cat=c1.selectbox('Category',['All']+sorted(df.category.unique()));loc=c2.selectbox('Location',['All']+sorted(df.location.unique()));mode=c3.selectbox('Work mode',['Any']+sorted(df.work_mode.unique()))
   c4,c5=st.columns(2);typ=c4.selectbox('Employment type',['Any']+sorted(df.employment_type.unique()));level=c5.selectbox('Experience',['Any']+sorted(df.experience_level.unique()));go=st.form_submit_button('Search dataset',use_container_width=True)
  if go:st.session_state.query=q
  q=st.session_state.get('query','');f=df.copy()
  if q:f=f[f[['title','company','location','skills','description','category']].astype(str).agg(' '.join,axis=1).str.contains(q,case=False,regex=False)]
  if cat!='All':f=f[f.category==cat]
  if loc!='All':f=f[f.location==loc]
  if mode!='Any':f=f[f.work_mode==mode]
  if typ!='Any':f=f[f.employment_type==typ]
  if level!='Any':f=f[f.experience_level==level]
  st.caption(f'{len(f)} sample listings · Offline demo data only')
  for _,j in f.head(60).iterrows():
   with st.container(border=True):
    a,b=st.columns([4,1]);a.markdown(f"### {j.title}");a.write(f"**{j.company}** · {j.location} · {j.work_mode}");a.caption(f"{j.category} · {j.employment_type} · {j.experience_level} · ₹{int(j.salary_min_inr):,}–₹{int(j.salary_max_inr):,} sample range");a.write(j.description);a.write('**Skills:** '+j.skills);a.caption(f'{j.job_id} · OFFLINE DEMO DATASET · No live apply link')
    if b.button('Save job',key='save'+j.job_id):
     try:s.save_job(uid,j.job_id);st.success('Saved')
     except Exception as e:st.error(str(e))
    if b.button('Track role',key='track'+j.job_id):st.session_state.track_job=j.job_id;st.session_state.page='Applications';st.rerun()
 elif page=='Resume Lab':
  hero('Resume Lab','Upload a PDF or DOCX, inspect extracted text and compare it with a sample role.')
  f=st.file_uploader('Upload resume (PDF/DOCX)',type=['pdf','docx']);label=st.text_input('Resume label',placeholder='e.g. Software Engineer Resume')
  if st.button('Upload and analyze',disabled=f is None):
   try:st.success(f'Resume uploaded (ID {s.add_resume(uid,label,f.name,f.getvalue())}) and set active.')
   except Exception as e:st.error(str(e))
  rr=s.resumes(uid)
  for r in rr:
   with st.container(border=True):
    a,b,c=st.columns([3,1,1]);a.markdown(f"**{r['label']}** {'· Active' if r['is_active'] else ''}  \n`{r['original_name']}`")
    if not r['is_active'] and b.button('Set active',key=f'act{r["id"]}'):s.set_active(uid,r['id']);st.rerun()
    if c.button('Delete',key=f'del{r["id"]}'):
     from backend.services import delete_resume
     delete_resume(uid,r['id']);st.rerun()
    with st.expander('Preview extracted text'):st.text(r['extracted_text'][:6000])
  if rr:
   active=s.active_resume(uid);df=s.jobs();jid=st.selectbox('Compare with sample job',df.job_id.tolist(),format_func=lambda x:f"{x} · {df.loc[df.job_id==x,'title'].iloc[0]}")
   j=df[df.job_id==jid].iloc[0]
   if st.button('Calculate resume match'):
    try:
     score,found,missing=s.match(active['extracted_text'] if active else '',str(j.description)+' Skills: '+str(j.skills));st.progress(score/100,text=f'Text similarity: {score}%');st.caption('Heuristic text similarity, not hiring probability.');a,b=st.columns(2);a.markdown('**Keywords found**');a.write(', '.join(found[:30]) or 'None');b.markdown('**Potential keywords to review**');b.write(', '.join(missing[:30]) or 'None')
    except Exception as e:st.error(str(e))
 elif page=='Saved Jobs':
  hero('Saved opportunities','Your private shortlist.');ss=s.saved(uid)
  if not ss:st.info('No saved jobs yet. Save listings from Find Jobs.')
  for j in ss:
   with st.container(border=True):
    st.markdown(f"### {j['title']} · {j['company']}");st.write(j['location']);st.write('**Skills:** '+j['skills']);notes=st.text_area('Notes',value=j['notes'] or '',key=f"sn{j['id']}");a,b=st.columns(2)
    if a.button('Update notes',key=f"un{j['id']}"):run('UPDATE saved_jobs SET notes=%s WHERE id=%s AND user_id=%s',(notes,j['id'],uid));st.success('Notes saved')
    if b.button('Remove',key=f"rm{j['id']}"):run('DELETE FROM saved_jobs WHERE id=%s AND user_id=%s',(j['id'],uid));st.rerun()
 elif page=='Applications':
  hero('Application tracker','Track progress manually. Only mark Applied after submitting on an employer site.')
  df=s.jobs();pre=df[df.job_id.astype(str)==str(st.session_state.get('track_job',''))]
  with st.expander('Add an application',expanded=not pre.empty):
   j=pre.iloc[0] if not pre.empty else None
   with st.form('newapp'):
    title=st.text_input('Job title',value=str(j.title) if j is not None else '');company=st.text_input('Company',value=str(j.company) if j is not None else '');loc=st.text_input('Location',value=str(j.location) if j is not None else '');status=st.selectbox('Status',s.STATUSES);follow=st.date_input('Follow-up date',value=None);notes=st.text_area('Notes');go=st.form_submit_button('Add to tracker',use_container_width=True)
   if go:
    try:
     ar=s.active_resume(uid);s.add_app(uid,title,company,loc,str(j.job_id) if j is not None else None,status,notes,follow if follow else None,ar['id'] if ar else None);st.session_state.track_job='';st.success('Added');st.rerun()
    except Exception as e:st.error(str(e))
  apps=s.applications(uid)
  for a in apps:
   with st.container(border=True):
    st.markdown(f"**{a['title']}** · {a['company']}  \n{a['location']} · Added {a['date_added']}");c1,c2=st.columns(2);status=c1.selectbox('Status',s.STATUSES,index=s.STATUSES.index(a['status']),key=f"as{a['id']}");notes=c1.text_input('Notes',value=a['notes'] or '',key=f"an{a['id']}");follow=c2.date_input('Follow-up',value=a['follow_up_date'] if a['follow_up_date'] else None,key=f"af{a['id']}");x,y=c2.columns(2)
    if x.button('Save changes',key=f"upd{a['id']}"):s.update_app(uid,a['id'],status,notes,follow if follow else None);st.success('Updated');st.rerun()
    if y.button('Delete',key=f"da{a['id']}"):run('DELETE FROM applications WHERE id=%s AND user_id=%s',(a['id'],uid));st.rerun()
  if apps:st.download_button('Export tracker CSV',pd.DataFrame(apps).to_csv(index=False).encode(), 'applications.csv','text/csv')
 elif page=='Cover Letters':
  hero('Cover letter studio','Create a conservative editable draft from your active resume. Review every sentence before use.')
  ar=s.active_resume(uid)
  with st.form('genletter'):
   title=st.text_input('Target role');company=st.text_input('Company');go=st.form_submit_button('Generate draft')
  if go:
   if not ar:st.error('Upload and activate a resume first.')
   else:st.session_state.letter=s.letter(u['full_name'],ar['extracted_text'],title,company);st.session_state.letter_title=f'{title} — {company}'
  with st.form('saveletter'):
   lt=st.text_input('Draft title',value=st.session_state.get('letter_title','Cover letter'));body=st.text_area('Edit cover letter',value=st.session_state.get('letter',''),height=300);save=st.form_submit_button('Save draft')
  if save:
   try:s.save_draft(uid,lt,body);st.success('Draft saved to MySQL')
   except Exception as e:st.error(str(e))
  if st.session_state.get('letter'):st.download_button('Download draft TXT',st.session_state.letter.encode(),'cover_letter.txt','text/plain')
  ds=s.drafts(uid)
  if ds:
   st.markdown('### Saved drafts')
   for d in ds:
    with st.expander(d['title']):st.text(d['body'])
 elif page=='Preferences':
  hero('Career preferences','Save target roles and locations to your own account.');p=s.prefs(uid);df=s.jobs();levels=['Any']+sorted(df.experience_level.unique());types=['Any']+sorted(df.employment_type.unique())
  with st.form('prefs'):
   roles=st.multiselect('Target roles',sorted(df.title.unique()),default=[x for x in p['roles'] if x in df.title.unique()]);locs=st.multiselect('Preferred locations',sorted(df.location.unique()),default=[x for x in p['locations'] if x in df.location.unique()]);mode=st.selectbox('Work mode',['Any','On-site','Hybrid','Remote'],index=['Any','On-site','Hybrid','Remote'].index(p['work_mode']));level=st.selectbox('Experience',levels,index=levels.index(p['experience_level']) if p['experience_level'] in levels else 0);typ=st.selectbox('Employment type',types,index=types.index(p['employment_type']) if p['employment_type'] in types else 0);mn=st.number_input('Minimum INR salary',min_value=0,value=int(p['min_salary'] or 0),step=10000);mx=st.number_input('Maximum INR salary',min_value=0,value=int(p['max_salary'] or 0),step=10000);go=st.form_submit_button('Save preferences')
  if go:
   try:s.save_prefs(uid,roles,locs,mode,level,typ,mn,mx);st.success('Preferences saved')
   except Exception as e:st.error(str(e))
 elif page=='Account':
  hero('Account & security','Manage your account credentials.');st.write(f"**Name:** {u['full_name']}  \n**Email:** {u['email']}")
  with st.form('pw'):
   old=st.text_input('Current password',type='password');new=st.text_input('New password',type='password');conf=st.text_input('Confirm new password',type='password');go=st.form_submit_button('Change password')
  if go:
   try:s.change_pw(uid,old,new,conf);st.success('Password changed')
   except Exception as e:st.error(str(e))
except Exception as e:
 st.error(str(e));st.info('Check MySQL Server status, .env credentials and schema.sql. The included dataset works without any API credentials.')
