import json
from dataclasses import dataclass, field, asdict
from typing import Any, Optional
from groq import Groq
import prompts

MODEL="openai/gpt-oss-120b"
@dataclass
class Context:
    topic:str; level:str; language:str; difficulty:str; sections:list; num_questions:int; extra_instructions:str
    plan:Optional[dict]=None; content:Optional[dict]=None; assessment:Optional[dict]=None; review:Optional[dict]=None; refined_pack:Optional[dict]=None
    errors:list=field(default_factory=list); completed:list=field(default_factory=list)

def parse_json(x):
    x=(x or '').strip()
    if x.startswith('```'): x=x.split('\n',1)[-1].removesuffix('```').strip()
    try:return json.loads(x)
    except: return json.loads(x[x.find('{'):x.rfind('}')+1])

def ai(client,prompt,temp=.25,retries=2):
    err='Unknown error'
    for _ in range(retries+1):
        try:
            r=client.chat.completions.create(model=MODEL,messages=[{'role':'system','content':prompts.SYSTEM},{'role':'user','content':prompt}],temperature=temp,max_tokens=7000)
            return parse_json(r.choices[0].message.content),None
        except Exception as e: err=str(e)
    return None,err

def quiz_errors(q,n):
    e=[]
    if len(q)!=n:e.append(f'Expected {n} questions; received {len(q)}.')
    for i,x in enumerate(q,1):
        opts=x.get('options',[]) if isinstance(x,dict) else []
        if len(opts)!=4:e.append(f'Question {i}: exactly 4 options required.')
        if isinstance(x,dict) and x.get('answer') not in opts:e.append(f'Question {i}: answer is not an option.')
    return e

def run(topic,level,language,difficulty,sections,num_questions,extra,api_key,progress=None):
    c=Context(topic,level,language,difficulty,sections,int(num_questions),extra); client=Groq(api_key=api_key)
    stages=[('Planning',lambda:prompts.plan(c),.25),('Content Generation',lambda:prompts.content(c),.35),('Assessment',lambda:prompts.assessment(c),.25),('Review',lambda:prompts.review(c),.15),('Refinement',lambda:prompts.refine(c),.2)]
    for i,(name,make,temp) in enumerate(stages,1):
        if progress:progress(i,name)
        result,err=ai(client,make(),temp)
        if err:c.errors.append(f'{name} failed: {err}');return c
        setattr(c,['plan','content','assessment','review','refined_pack'][i-1],result);c.completed.append(name)
        if name=='Assessment':c.errors+=quiz_errors(result.get('quiz',[]),c.num_questions)
    if c.refined_pack and 'Quiz' in c.sections:c.errors+=quiz_errors(c.refined_pack.get('quiz',[]),c.num_questions)
    return c

def to_dict(c):return asdict(c)
