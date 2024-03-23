import streamlit as st
from streamlit_chat import message
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer, util
from datetime import timezone
from datetime import datetime
import math
import random
import requests
import json
import glob
import('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')


st.set_page_config(layout="wide")
docID = 'f44b7fbf-a3ca-4a25-9f13-8e37f20355ce' # This is the ID of the document to query

def asktheknowledgebase(doc_id, question, number_of_words, style_qualifier):
    r = ''
    postmessage = 'https://api.askyourpdf.com/v1/chat/' + doc_id + '?model_name=GPT3'
    # print(postmessage)
    message = question + ' # Answer in approximatively ' + str(number_of_words) + ' words using a ' + style_qualifier + ' style. If the answer is not in the document reply with "~"'
    # print(message)
    headers = {
        'Content-Type': 'application/json',
        'x-api-key': 'ask_ef485b704b2ab30cc05db4c40a17a4e4'
    }

    data = [
        {
            "sender": "User",
            "message": message
        }
    ]
    response = requests.post(postmessage, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        r = (response.json()['answer']['message'])
    else:
        r = ('Error:', response.status_code)
    return r


st.markdown('''<style>
div.stButton > button:first-child {
background-color: #FEEEE8 ;color:purple;font-size:20px;font-weight:bold;height:2em;border-radius:10px 10px 10px 10px;
}
.css-2trqyj:focus:not(:active) {
border-color: #ffffff;
box-shadow: none;
color: #ffffff;
background-color: #0066cc;
}
.css-2trqyj:focus:(:active) {
border-color: #ffffff;
box-shadow: none;
color: #ffffff;
background-color: #0066cc;
}
.css-2trqyj:focus:active){
background-color: #0066cc;
border-color: #ffffff;
box-shadow: none;
color: #ffffff;
background-color: #0066cc;
}
</style>
<script>
        function  aalert(x) {
            alert("@")
        }
</script>
''', unsafe_allow_html=True)


from streamlit_d3graph import d3graph, vec2adjmat
#from d3graph import d3graph, vec2adjmat
st.header('AI powered SEEA course assistant', divider='rainbow')
def addnewvaraintsembeddings():
    chroma_client = chromadb.PersistentClient(path="chromadb")
    collectionfound = False
    try:
        collection = chroma_client.create_collection(name="qquestions")
        collectionfound = True
    except:
        try:
           collection = chroma_client.get_collection(name="qquestions")
           collectionfound = True
        except:
            print("Error opening collection")
    if collectionfound == False:
        print("!!! Error opening the collection")
        return False
    else:
        model = SentenceTransformer('multi-qa-MiniLM-L6-cos-v1')
        dbfile = "questions.db"
        sqliteConnection = sqlite3.connect(dbfile)
        cursor = sqliteConnection.cursor()
        ssql = "SELECT variantid, variant, questionid FROM questions_variants WHERE varitanadded=0"
        cursor= sqliteConnection.execute(ssql)
        recs = cursor.fetchall()
        #print(recs)
        Embeddings=[]
        Documents=[]
        Metadatas=[]
        Ids=[]
        varianids = ''
        if len(recs)>0:
            for rec in recs:
                Embeddings.append(model.encode(rec[1]).tolist())
                Documents.append(rec[1])
                Metadatas.append({"source": "my_source"})
                Ids.append(rec[0])
                if varianids=='':
                    varianids = "'"+rec[0]+"'"
                else:
                    varianids = varianids + ",'" + rec[0]+"'"
            print("Documents:")
            print(Documents)
            collection.add(embeddings=Embeddings, documents=Documents, metadatas=Metadatas, ids=Ids)
        cursor.close()
        for rec in recs:
            ssql = "UPDATE questions_variants SET varitanadded=1 WHERE variantid='"+rec[0]+"'"
            print(ssql)
            sqliteConnection.execute(ssql)
            sqliteConnection.commit()
        sqliteConnection.close()
        return True

def kgraph(inputtext, keywords, depth, maxnbrelations):
    s = inputtext.lower().strip()
    s = "@ "+s+" @"
    #s= ''
    kws = keywords.split(",")
    kws0 = []
    for k in kws:
        k = k.lower().strip()
        if len(k)>0:
            kws0.append(k)
            s = s + " @ "+k+" @"
    #print(s)
    sources = []
    targets = []
    weights = []
    relations = []
    nodes = []
    nodesrelations = []
    if True:
        dbpath = 'knetwork.db'
        conn = sqlite3.connect(dbpath)
        ssql0 = "SELECT DISTINCT source, relation, target FROM knetwork WHERE ('"+s.replace("'","''")+"' LIKE '%' || LOWER(TRIM(source)) || '%') OR ('"+s.replace("'","''")+"' LIKE '%' || LOWER(TRIM(target)) || '%')"  
        print(ssql0)
        curs0 = conn.cursor()
        curs0.execute(ssql0)
        res0 = curs0.fetchall()
        #print(res0)
        kwlist = []
        for rec in res0:
            src = rec[0].lower().strip()
            rel = rec[1].lower().strip()
            trg = rec[2].lower().strip()
            #print(v)
            if not src in kwlist:
                kwlist.append(src)
            if not src in nodes:
                nr = src + " [-"+rel+"-> " + trg
                nodes.append(src)
                nodesrelations.append([src, nr])
            else:
                for t in range(0, len(nodesrelations)):
                    if nodesrelations[t][0]==src:
                        nr = src + " [-"+rel+"-> " + trg
                        nrs = '\n'+nodesrelations[t][1]+"\n"
                        if nrs.find("\n"+src+"\n")<0:
                            nodesrelations[t][1] = nodesrelations[t][1] + "\n" + nr
                       
            if not trg in kwlist:
                kwlist.append(trg)
            if not trg in kwlist:
                kwlist.append(trg)
            if not trg in nodes:
                nr = trg + " <-"+rel+"-] " + src
                nodes.append(trg)
                nodesrelations.append([trg, nr])
            else:
                for t in range(0, len(nodesrelations)):
                    if nodesrelations[t][0]==trg:
                        nr = trg + " <-"+rel+"-] " + src
                        nrs = '\n'+nodesrelations[t][1]+"\n"
                        if nrs.find("\n"+src+"\n")<0:
                            nodesrelations[t][1] = nodesrelations[t][1] + "\n" + nr
            ffound = False
            if len(sources)==0:
               pass
            else:
              for ii in range(0, len(sources)):
                  if src == sources[ii] and trg==targets[ii]:
                      weights[ii] = weights[ii] + 1
                      ffound = True
                  if trg == sources[ii] and src==targets[ii]:
                      weights[ii] = weights[ii] + 1
                      ffound = True
            if ffound == False:
                sources.append(src)
                relations.append(rel)
                targets.append(trg)
                w = 1
                if src in kws0:
                    w = w +1
                if trg in kws0:
                    w = w +1
                weights.append(w)              
        #print(kwlist)
        if depth > 1:
            for h in range(1,depth):
                ssql0 = "SELECT DISTINCT source, target FROM knetwork WHERE "
                u = 0
                for kw in kwlist:
                    u= u + 1
                    if u == 1:
                        ssql0 = ssql0 + "(source='"+kw.replace("'","''")+"') OR (target='"+kw.replace("'","''")+"')"
                    else:
                        ssql0 = ssql0 + " OR (source='"+kw.replace("'","''")+"') OR (target='"+kw.replace("'","''")+"')" 
                #print(ssql0)
                curs0.execute(ssql0)
                res0 = curs0.fetchall()
                #print(res0)
                kwlist = []
                for rec in res0:
                    src = rec[0].lower().strip()
                    rel = rec[1].lower().strip()
                    trg = rec[2].lower().strip()
                    #print(v)
                    if not src in kwlist:
                        kwlist.append(src)
                    if not trg in kwlist:
                        kwlist.append(trg)
                    ffound = False
                    if len(sources)==0:
                       pass
                    else:
                      for ii in range(0, len(sources)):
                          if src == sources[ii] and trg==targets[ii]:
                              weights[ii] = weights[ii] + 1
                              ffound = True
                          if trg == sources[ii] and src==targets[ii]:
                              weights[ii] = weights[ii] + 1
                              ffound = True
                    if ffound == False:
                        sources.append(src)
                        relations.append(rel)
                        targets.append(trg)
                        w = 1
                        if src in kws0:
                            w = w +1
                        if trg in kws0:
                            w = w +1
                        weigths.append(w)    
        print(kwlist)
        ssql0 = "SELECT DISTINCT source, relation, target, weight FROM knetwork WHERE "
        u = 0
        if kwlist == []: #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! Code to update to account for empty keyword list
            kwlist = ['SEEA', 'Natural capital accounting']
        for kw in kwlist:
            u= u + 1
            if u == 1:
                ssql0 = ssql0 + "(source='"+kw.replace("'","''")+"') OR (target='"+kw.replace("'","''")+"')"
            else:
                ssql0 = ssql0 + " OR (source='"+kw.replace("'","''")+"') OR (target='"+kw.replace("'","''")+"')" 
        print(ssql0)
        curs0.execute(ssql0)
        res0 = curs0.fetchall()
        print(res0)
        source = []
        target = []
        weight = []
        relation = []
        for rec in res0:
            source0 = rec[0]
            relation0 = rec[1]
            target0 = rec[2]
            print('Source: ' + source0)
            print('Relation: ' + relation0)
            print('Target: ' + target0)
            source.append(source0.replace(" ","\n"))
            target.append(target0.replace(" ","\n"))
            weight.append(1)
            relation.append(relation0) # + "("+str(i)+")")
        conn.close()
        return [sources, relations, targets, weights, nodesrelations]

def findsimilarquestions(question, treshold):
        r = []
        model = SentenceTransformer('multi-qa-MiniLM-L6-cos-v1')
        chroma_client = chromadb.PersistentClient(path="chromadb")
        collectionfound = False
        try:
            collection = chroma_client.create_collection(name="qquestions")
            collectionfound = True
        except:
            try:
               collection = chroma_client.get_collection(name="qquestions")
               collectionfound = True
            except:
                print("Error opening collection")
        if collectionfound == False:
            print("!!! Error opening the collection")
            return False
        else:
            results = collection.query(
                n_results=5,
                query_embeddings = model.encode(question).tolist()
            )
            #print(results)
            n = len(results['documents'][0])
            #print(n)
            for i in range(0,n):
                #print("===============")
                #print(" Distance: " +str(results['distances'][0][i]))
                if results['distances'][0][i] <= treshold:
                    r.append(results['documents'][0][i])

        return r

def findanswers(qv):
        r = []
        dbfile = "questions.db"
        sqliteConnection = sqlite3.connect(dbfile)
        cursor = sqliteConnection.cursor()
        ssql = "SELECT DISTINCT b.answer FROM questions_variants a INNER JOIN questions_answers b ON a.questionid = b.questionid WHERE LOWER(TRIM(a.variant))='"+qv.lower().strip()+"' ORDER BY b.answerscore DESC"
        print(ssql)
        cursor= sqliteConnection.execute(ssql)
        recs = cursor.fetchall()
        #print(recs)
        if len(recs)>0:
            for rec in recs:
                #print(rec)
                r.append(rec[0])
        sqliteConnection.close()
        print(r)
        return r

def generate_answer():
    st.write("#" + request)

nm = 0
  

addnewvaraintsembeddings()
col1, col2= st.columns(2)
with col2:
    st.subheader("Graphs of concepts that you may want to explore deeper based on your question:")
    st.divider()
    placeholder1 = st.empty()
    st.divider()
    placeholder2 = st.empty()
    st.divider()

d3 = d3graph()
d3_2 = d3graph()

def formatnodelabel(x):
    x = x.strip()
    r = x
    if len(x) > 0:
        x = x.replace("_"," ").replace("  "," ").strip()
        x = x.replace(":"," ").replace("  "," ").strip()
        x = x.replace("-"," ").replace("  "," ").strip()
        x = x.replace(" "," ")
    return x


def fillcol2(_ph1, _ph2, sld, text, keywords, text2, keywords2):
    ph1 = _ph1
    ph2 = _ph2
    text = text.replace("\n", ' ').replace("  "," ")
    keywords = keywords.replace("\n", ' ').replace("  "," ")
    text2 = text2.replace("\n", ' ').replace("  "," ")
    keywords2 = keywords2.replace("\n", ' ').replace("  "," ")
    ph1.empty()
    ph2.empty()
    s1 = str(math.floor(100000000*random.random()))+str(math.floor(100000000*random.random()))+str(math.floor(100000000*random.random()))
    with ph1:
        source, relation, target, weight, nrelations = kgraph(text, keywords, 1, 100)
        adjmat = vec2adjmat(source, target, weight=weight)
        d3.graph(adjmat)
        cols = adjmat.columns.astype(str)
        ntooltips = []
        nlabels = []
        for column in cols:
            nlabels.append(column)
            for u in range(0, len(nrelations)):
                if nrelations[u][0].lower().strip().replace("_"," ")==column.lower().strip().replace("_"," "):
                    ntooltips.append(nrelations[u][1])
        d3.set_node_properties(tooltip = ntooltips, fontcolor='#544924', label=nlabels, fontsize=6)
        d3.set_edge_properties(directed=True, marker_end='arrow', edge_distance=5)
        d3.show(set_slider=sld)
        if len(text2)>0 or len(keywords2)>0:
            with ph2:
                try:
                    source2, relation2, target2, weight2, nrelations2 = kgraph(text2, keywords2, 1, 100)
                    adjmat2 = vec2adjmat(source2, target2, weight=weight2)
                    d3_2.graph(adjmat2)
                    cols2 = adjmat2.columns.astype(str)
                    ntooltips2 = []
                    nlabels2 = []
                    for column in cols2:
                        nlabels2.append(column)
                        for u in range(0, len(nrelations2)):
                            if nrelations2[u][0].lower().strip().replace("_"," ")==column.lower().strip().replace("_"," "):
                                ntooltips2.append(nrelations2[u][1])
                    d3_2.set_node_properties(tooltip = ntooltips2, fontcolor='#544924', label=nlabels2, fontsize=6)
                    d3_2.set_edge_properties(directed=True, marker_end='arrow', edge_distance=5)
                    d3_2.show(set_slider=sld)
                except:
                    st.write("Error building the graph")
        
    return [ph1, ph2]

with col1:
    st.subheader("Enter your question here:")
    text_input = st.text_input("")
    if text_input:
            st.divider()
            st.markdown(':orange[**' + str(text_input).strip() + '**]')
            st.markdown(':red[**Warning: the following answer comes directly from the AI and was not reviewed by an ECA expert. See the listbox below the answer for a list of questions similar to your that have answers that were reviewd and validated by ECA expertts**]')
            aanswer = asktheknowledgebase(docID, text_input, 500, "academic, simple")
            st.write(aanswer)
            st.divider()
            keywords = "seea, natural capital accounting"
            fquestion = text_input
            sa = findsimilarquestions(text_input, 0.9)
            st.markdown('**Here are questions with answers curated by experts that are close to your question. Select one to view the answer."**')
            option = st.selectbox(
               '',
               sa,
               index=None,
               placeholder="Select the question to see the curated answer ...",
            )
            try:
                st.write(st.session_state.np)
            except:
                pass
            #st.button("Not statisfied with the existing answers? Send your question to ACS and domain experts will add a curated answer.",type="primary", use_container_width=True)
            #st.button("Do you want to contribute to the knowledge base based on your personal or country's experience? Send questions with their answers to ACS.", type="primary", use_container_width=True)
            placeholder = fillcol2(placeholder1, placeholder2, 4, text_input + " @ " + aanswer, keywords, '', '')
            if option:
                answers = findanswers(option)
                st.markdown(':orange[**Question: '+option+'**]')
                st.markdown('*Answer reviewed and validated by ECA experts:*')
                txt2 = ""
                for a in answers:
                    print(a)
                    st.markdown(':blue['+str(a)+']')
                    txt2 = txt2 + " @ " + a
                #optionmore = st.selectbox(
                #"These are more questions that allow exploring deeper based on the answers above:",
                #sa,
                #index=None,
                #placeholder="Select the question to see the curated anser ...",
                #)
                if True:
                    placeholder = fillcol2(placeholder1, placeholder2, 5, fquestion + " @ " + aanswer, "seea", txt2, "seea")
                #except:
                    #print("Error building the graph")
