import json, os
import streamlit as st
from workflow import run, to_dict

st.set_page_config(page_title='AI Study Pack Generator',page_icon='🎓',layout='wide')
st.title('🎓 AI Study Pack Generator')
st.caption('Planning → Content Generation → Assessment → Review → Refinement')

def key():
    try:return st.secrets.get('GROQ_API_KEY','') or os.getenv('GROQ_API_KEY','')
    except:return os.getenv('GROQ_API_KEY','')

def render(p,s):
    o=[f"# {p.get('title','AI Study Pack')}"]
    if 'Summary' in s:
        if p.get('summary'):o+=['## 📚 Summary\n'+p['summary']]
        if p.get('key_points'):o+=['## 🔑 Key Points\n'+'\n'.join('- '+x for x in p['key_points'])]
        if p.get('examples'):o+=['## 💡 Examples\n'+'\n'.join('- '+x for x in p['examples'])]
    if 'Flashcards' in s and p.get('flashcards'):
        o+=['## 🧠 Flashcards\n'+'\n\n'.join(f"### Card {i}\n**Q:** {x.get('front','')}\n\n**A:** {x.get('back','')}" for i,x in enumerate(p['flashcards'],1))]
    if 'Quiz' in s and p.get('quiz'):
        o+=['## 📝 Quiz\n'+'\n\n'.join(f"### {i}. {q.get('question','')}\n\n"+'\n'.join('- '+x for x in q.get('options',[]))+f"\n\n**Answer:** {q.get('answer','')}\n\n**Explanation:** {q.get('explanation','')}" for i,q in enumerate(p['quiz'],1))]
    if p.get('study_tips'):o+=['## 🎯 Study Tips\n'+'\n'.join('- '+x for x in p['study_tips'])]
    return '\n\n'.join(o)

with st.sidebar:
    st.header('⚙️ Study Preferences')
    topic=st.text_input('📖 Topic',placeholder='e.g. Photosynthesis')
    level=st.selectbox('🎓 Student Level',['School','High School','College','University','Professional'],index=1)
    language=st.selectbox('🌐 Language',['English','Urdu','Roman Urdu'])
    difficulty=st.select_slider('⚡ Difficulty',['Easy','Medium','Hard'],value='Medium')
    sections=st.multiselect('📦 Sections',['Summary','Flashcards','Quiz'],default=['Summary','Flashcards','Quiz'])
    n=st.slider('❓ Quiz Questions',3,20,10)
    extra=st.text_area('➕ Extra Instructions')
    go=st.button('🚀 Generate Study Pack',type='primary',use_container_width=True)

if go:
    if not topic.strip():st.warning('Enter a topic.');st.stop()
    if not sections:st.warning('Select at least one section.');st.stop()
    api=key()
    if not api:st.error('GROQ_API_KEY is missing. Add it to Streamlit Secrets.');st.stop()
    bar=st.progress(0); status=st.empty()
    def progress(i,name):bar.progress(i/5);status.info(f'Stage {i}/5 — **{name}**')
    try:c=run(topic,level,language,difficulty,sections,n,extra,api,progress)
    except Exception as e:st.error(str(e));st.stop()
    if c.refined_pack:
        st.success('🎉 Workflow completed.')
        a,b,d=st.tabs(['📚 Final Study Pack','🔄 Workflow Trace','🧩 Context'])
        with a:
            st.markdown(render(c.refined_pack,sections))
            st.download_button('⬇️ Download JSON',json.dumps(c.refined_pack,ensure_ascii=False,indent=2),'study_pack.json','application/json')
        with b:
            for x in ['Planning','Content Generation','Assessment','Review','Refinement']:
                st.success(x+' completed') if x in c.completed else st.warning(x+' not completed')
            for e in c.errors:st.warning(e)
        with d:st.json(to_dict(c))
    else:
    st.error("Workflow failed.")

    for error in c.errors:
        st.warning(error)

with st.expander('ℹ️ Workflow'):
    st.markdown('**Planning** creates the learning strategy. **Content Generation** uses the plan. **Assessment** tests generated concepts. **Review** critiques the draft. **Refinement** applies feedback and creates the final pack. Each stage receives context from previous stages and AI calls use retries plus validation.')
