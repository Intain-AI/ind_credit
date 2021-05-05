def preprocess(text):
    text=text.replace(':(cid:9)',"")
    text=text.replace(':',"")
    #text=text.replace(':',"")
    text=text.replace('(cid:9):',"")
    if(text.startswith(':(cid:9)')):
              text=text[len(':(cid:9)'):]
    return(text)

def process_input_file(data):
    for value in data['result'].items():
        text_list=data['result']['Page_1']['digitized_details']['logical_cells']
    sentences=[]
    for i in range(len(text_list)):
        sentences.append(text_list[i]["token"])
    #print(sentences)
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

def date_coordinates(date,sentences):
    if(' ' in date):
        date=date.split(' ')
        if('/' in date):
            date=date.split('/')
        if('-' in date):
            date=date.split('-')          
        for i in range(len(sentences)):
            for j in range(len(sentences[i])-2):
                text=sentences[i][j]['text']
                text=preprocess(text)
                            #print(date[0],text)
                if(date[0]==text.lower()):
                    #print("1st")
                    text=sentences[i][j+1]['text']
                    text=preprocess(text)
                    if(date[1]==text.lower()):
                        #print("2nd")
                        text=sentences[i][j+2]['text']
                        text=preprocess(text)
                        if(date[2]==text.lower()):
                            #print("found")
                            coordinates={"top":sentences[i][j]['top'],"left":sentences[i][j]['left'],"width":sentences[i][j]['width'],"height":sentences[i][j]['height']}
                            return(coordinates)
        return({"top":10,"left":10,"width":10,"height":10})
             
                                  
def account_holder_coordinates(person_name,data):
    temp=person_name.split(' ')
    coordinates={}
    #print(temp)
    if('' in temp):
        temp.remove('')
    
    for t in temp:
        for i in range(0,len(data)):
            for j in range(0,len(data[i]['token'])):
                text=data[i]['token'][j]['text']
                text=text.strip()
                text=preprocess(text)
                #print(text.lower())
                if (t).lower()==text.lower():
                    top = data[i]['token'][j]['top']
                    left = data[i]['token'][j]['left']
                    width = data[i]['token'][j]['width']
                    height = data[i]['token'][j]['height']
                    #coordinates={"top":top,"left":left,"width":width,"height":height}
                    coordinates[str(t)]=[top,left,width,height]
                    #print(coordinates[str(t)][1])
    #print("coor",coordinates)
    coordinates_list=list(coordinates.values())
    if(len(coordinates_list)>0):
            d_values=coordinates_list[0]
            coordinates={"top":d_values[0],"left":d_values[1],"width":d_values[2],"height":d_values[3]}
    #print(coordinates)
    return(coordinates,coordinates_list)     

def account_type_coordinates(sentences,text_list,word):
   
    for i in range(len(sentences)):
        for j in range(len(sentences[i])):
            text=sentences[i][j]['text']
            text=preprocess(text) 
            if(word.lower() in text.lower()):
                #print("found coordinates type")
                #print(word,text)
                coordinates={"top":sentences[i][j]['top'],"left":sentences[i][j]['left'],"width":sentences[i][j]['width'],"height":sentences[i][j]['height']} 
                print(coordinates)
                return(text_list[i]['token'][j]['id'],text_list[i]['id'],coordinates)
    return(0,0,{})
        
    
def find_coordinates(sentences,text_list,word):  
    for i in range(len(sentences)):
        for j in range(len(sentences[i])):
            text=sentences[i][j]['text']
            text=preprocess(text) 
            #print("words",text,word)
            if(text==word):
                #print("found coordinates")
                coordinates={"top":sentences[i][j]['top'],"left":sentences[i][j]['left'],"width":sentences[i][j]['width'],"height":sentences[i][j]['height']} 
                return(text_list[i]['token'][j]['id'],text_list[i]['id'],coordinates)
        
    #print("not found")
    return(0,0,{})

def rule_based_coordinates(result,dict_bank,sentences,text_list,data):
    for result_dict in result:
        result_dict['value']=dict_bank[result_dict['varname']]
        print(result_dict)
        val=dict_bank[result_dict['varname']]
        if(val!='NA'):
            if(result_dict['varname']!='account_holder_name' and result_dict['varname']!='joint_holders'):
                id,logical_id,coordinates=find_coordinates(sentences,text_list,result_dict['value'])
                # print("here",coordinates)
                if(coordinates=={}):
                    coordinates={"top":10,"left":10,"width":10,"height":10}
                result_dict['coordinates']=coordinates
                #Finding coordinates for account open date
                if(coordinates=={} and result_dict['varname']=='ac_open_date'):
                    date=result_dict['value']
                    coordinates=date_coordinates(date,sentences)
                    # print("acc opening date",coordinates)
                result_dict['coordinates']=coordinates
                #print(coordinates)
            elif(result_dict['varname']=='joint_holders'):
                result_dict['value']=dict_bank[result_dict['varname']]
                value=result_dict['value'].split(" ")[0]
                id,logical_id,coordinates=account_type_coordinates(sentences,text_list,value)
                if(coordinates=={} or value=="Individual"):
                  
                    result_dict['coordinates']={"top":10,"left":10,"width":10,"height":10}
                else:
                    #print("joint")
                    result_dict['coordinates']=coordinates
            #Finding coordinates for account holder name
            elif(result_dict['varname']=='account_holder_name'):
                person_name=dict_bank[result_dict['varname']]
                #print("person",person_name)
                coordinates,coordinates_list=account_holder_coordinates(person_name,data)
                if(len(coordinates_list)==0):
                    result_dict['value']='NA'
                    result_dict['coordinates']={"top":10,"left":10,"width":10,"height":10}
                else:
                    result_dict['coordinates']=coordinates
        else:
            result_dict['coordinates']={"top":10,"left":10,"width":10,"height":10}
        # print("result_dict\n",result_dict)
    # print("result",result)
    return(result)