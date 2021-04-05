def preprocess(text):
    text=text.replace(':(cid:9)',"")
    text=text.replace('(cid:9)',"")
    text=text.replace(':',"")
    return(text)

def process_input_file(data):
    for value in data['result'].items():
        text_list=data['result']['Page_1']['digitized_details']['logical_cells']
  
    sentences=[]
    for i in range(len(text_list)):
        sentences.append(text_list[i]["token"])
 
    sent=[]
    for i in range(len(sentences)):
        tokens=[]
        for j in range(len(sentences[i])):
            tokens.append(sentences[i][j]['text'])
        sent.append(tokens)

 
    for i in range(len(sent)):
        for j in range(len(sent[i])):
            text=preprocess(sent[i][j])
            sent[i][j]=text
    tokens=sent
    return(text_list,sentences,tokens)

def find_coordinates(sentences,text_list,word):
 
    for i in range(len(sentences)):
        for j in range(len(sentences[i])):
            text=sentences[i][j]['text']
            text=preprocess(text)
            if(text==word):
                coordinates={"top":sentences[i][j]['top'],"left":sentences[i][j]['left'],"width":sentences[i][j]['width'],"height":sentences[i][j]['height']}
             
                return(text_list[i]['token'][j]['id'],text_list[i]['id'],coordinates)