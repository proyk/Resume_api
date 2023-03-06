from fastapi import FastAPI,File, UploadFile
from pdfminer.high_level import extract_text
import re
import io
from difflib import SequenceMatcher
import nltk
from nltk.tokenize import word_tokenize
from nltk.chunk import conlltags2tree, tree2conlltags
import spacy
from tabula import read_pdf
import pandas as pd
from datetime import datetime 
from dateutil import parser  
nltk.download('averaged_perceptron_tagger')
nltk.download('punkt')
nltk.download('maxent_ne_chunker')
nltk.download('words')
nltk.download('stopwords')
app=FastAPI()
@app.get('/')
def index():
    return {"Message":"Api is working!!"}
    
@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        text = extract_text(io.BytesIO(contents))
        email = getEmail(text)
        name=getName(text)
        skills=getSkill(text)
        mobile=getPhone(text)
        education=getEduDetails(text,io.BytesIO(contents))
        total_experience=getExperience(text)
    except OSError as e:
        return {"message": f"Error extracting text: {e}"}
    except Exception as e:
        return {"message": str(e)}
    finally:
        await file.close()

    return {"Name":name,"Email": email,'Mobile':mobile,'Skills':skills,'Experience':total_experience,'Education':education}
#RESUME EXTRACTION
def getEduDetails(extractedText,path):
  import warnings
  warnings.filterwarnings("ignore", category=UserWarning, module='tabula')

  reserveWordForInstituteName={
      "university":"university",
      "college":"college",
      "collage":"collage",
      "institute":"institute"
      }
  degreeStartWord={
      "diploma":"diploma",
      "bachelor":"bachelor",
      "graduate":"graduate",
      "postgraduate":"postgraduate",
      "master":"master",
      "bca":"bca",
      "mca":"mca",
      "bba":"bba",
      "mba":"mba",
      }
  degreesWord=["B.E","BE","M.E","ME","B.Sc","Bsc","BTech"] 
  educationDict={}
  college=""
  degree=""
  stream=None
  clgFound=False
  degreeFound=False
  NoTable=False
  j=0
  df = read_pdf(path,pages="all")
  try:
    tableData=df[0].values.tolist()
    tableData=[data for data in tableData if data!="nan"]
  except:
    pass
  if not df:
    NoTable=True
  elif len(tableData)<=1:
   
    NoTable=True

  else:
    tableData=sum(tableData, [])
    
    for i in tableData:
      i=str(i)
      if re.search("\r",str(i)):
        i="".join(i).replace("\r"," ")
      clgData=[text for text in i.split() if text.lower() in reserveWordForInstituteName and not i.lower().startswith(tuple(reserveWordForInstituteName))]
      degData=[text for text in i.split() if i.lower().startswith(tuple(degreeStartWord))]
      degAbbData=[i.split() for text in i.split() if re.sub("\W+","",text) in degreesWord]

      if len(clgData)>0:
        college=i
        clgFound=True
      if len(degData)>0:
        degree=i
        degreeFound=True
      if len(degAbbData)>0:
        degree=degAbbData[0][0]
        stream=degAbbData[0][1]
        degreeFound=True
      if clgFound and degreeFound:
        
        j=j+1
        educationDict["data"+str(j)]={"college":college,"degree":degree,"stream":stream}
        if stream is not None:
          stream=None
        college=""
        degree=""
        clgFound=False
        degreeFound=False

  if NoTable or len(educationDict)==0:
    
    for no,line in enumerate(extractedText.split("\n")):
      # print(no)
    #institute extraction
      getEducationOrg=[word for word in line.split() if (re.sub('\W+','', word).lower() in reserveWordForInstituteName or word.lower().startswith(tuple(reserveWordForInstituteName))) and line.lower().startswith(tuple(reserveWordForInstituteName))==False ]
      if len(getEducationOrg)>0:
        college=line
        clgFound=True  
      #for Degree Extraction
      getDegreeNm="#".join([line for word in line.split() if re.sub('\W+','', word).lower().startswith(tuple(degreeStartWord))])
      if len(getDegreeNm)>0:
        if re.search("#",getDegreeNm,re.IGNORECASE):
          getDegreeNm=getDegreeNm.split("#")[0]
        if re.search(" in ",getDegreeNm,re.IGNORECASE):
          degree,inn,stream=getDegreeNm.partition(" in ")
        else:
          degree=getDegreeNm 
          
      else:
        getDegreeAndType="".join([line for word in line.split() if re.sub('\W+','', word) in degreesWord ])
        if len(getDegreeAndType)>0:
          degree=getDegreeAndType.split()
          stream=(re.sub('\W+',' ', " ".join(degree[1:]))).strip()
          degree=degree[0]
      if len(degree)>0:
        degreeFound=True
      
      if degreeFound and clgFound:
        
        if (len(degree)-len(degree.strip()))<=1:
          if stream is None:

            educationDict["data"+str(j)]={"college":re.sub("[\d\W]+"," ",college),"degree":re.sub("\W+"," ",degree),"stream":stream}
          
          elif stream is not None:
            stream=re.split(r"[,(]", stream)[0]
            educationDict["data"+str(j)]={"college":re.sub("[\d\W]+"," ",college),"degree":re.sub("\W+"," ",degree),"stream":re.sub("[\d\W]+"," ",stream)}
            stream=None
        degreeFound=False
        clgFound=False
        college=""
        degree=""
        j=j+1
  return educationDict
def getExperience(inputString):
    extractedText=inputString
    total_exp=0
    if re.search(r"experience|work history|employment",extractedText,flags=re.IGNORECASE):
      lengthOfSplit=len(re.findall(r"experience|work history|employment",extractedText,flags=re.IGNORECASE))
      experienceAfterText=re.split(r"experience|work history|employment",extractedText,flags=re.IGNORECASE,maxsplit=lengthOfSplit)[lengthOfSplit]
      experience_text_for_No_date_mention=re.split(r"experience|work history|employment",extractedText,flags=re.IGNORECASE,maxsplit=1)[1]
      experienceText=re.split(r"education|hobbies|language|ACADEMIC QUALIFICATIONS",experienceAfterText,flags=re.IGNORECASE,maxsplit=1)[0]  
      experienceText=re.split(r"\s{3,}|:|-|–|to|from|[(|)]|\n",experienceText,flags=re.IGNORECASE)
      experience_list = []
      sectionWords=""
      desired_format = "%Y-%m-%d"
      for word in experienceText:
        try:
          word=re.sub("\W",' ',word).strip()
          sectionWords+=word+" "
          if re.search(r"dob|d.o.b|date of birth|birthdate",sectionWords,re.IGNORECASE):
            break
          else:
            convertStringInDate=datetime.strptime(parser.parse(word).strftime(desired_format), desired_format)
          experience_list.append(convertStringInDate)
        except Exception as e:
          pass
      try:
        if len(experience_list)>0:
          min_date=min(experience_list)
          if re.search(r"present|current",sectionWords,flags=re.IGNORECASE):
            max_date=datetime.today()
          else:
            max_date=max(experience_list)
          if max_date>datetime.today() or min_date>datetime.today():
            total_exp=0.0
          else:  
            diff = max_date - min_date
            years = int(diff.days / 365)
            months = int((diff.days % 365) / 30)
            if months==12:
              total_exp = str(years+1)+".0"
            else:
              total_exp= str(years)+"."+str(months)
        if re.search(r"year|month",experience_text_for_No_date_mention,re.IGNORECASE) and total_exp==0.0:
          year_pattern = r"\b(\d+(?:\.\d+)?)(?: year(s)?)"
          month_pattern = r"\b(\d+(?:\.\d+)?)(?: month(s)?)"
          year_matches = re.findall(year_pattern, experience_text_for_No_date_mention,re.IGNORECASE)
          month_matches = re.findall(month_pattern, experience_text_for_No_date_mention,re.IGNORECASE)
          yearList=[0]
          monthList=[0]
          if len(year_matches)>0:
            for i in year_matches:
              yearList.append(float(i[0]))
          if len(month_matches)>0:
            for i in month_matches:
              monthList.append(float("0."+i[0]))
          total_exp=str(sum(yearList)+sum(monthList))
        return total_exp
      except Exception as e:
        print(e)
    else:
      print("No EXP Found!")
def getPhone(inputString):
    number = ''
    try:
        pattern = re.compile(r'([+(]?\d+[)\-]?[ \t\r\f\v]*[(]?\d{2,}[()\-]?[ \t\r\f\v]*\d{2,}[()\-]?[ \t\r\f\v]*\d*[ \t\r\f\v]*\d*[ \t\r\f\v]*)')
        match = pattern.findall(inputString)
        match = [re.sub(r'[()\,.]', '', el).strip() for el in match if len(re.sub(r'[()\-.,\D+]', '', el))>9 and len(re.sub(r'[()\-.,\D+]','',el)) <= 15]
        number = match
    except:
        pass
    return number
def getSkill(inputString):
	nlp = spacy.load('en_core_web_sm')
	text=inputString
	if re.search("skill",text,re.IGNORECASE):
		text=re.split(r"skill",text,flags=re.IGNORECASE,maxsplit=1)[1]
	nlp_text=nlp(text)
	nlp_noun_chunks=list(nlp_text.noun_chunks)
	tokens = [token.text for token in nlp_text if not token.is_stop]
	data = pd.read_csv("./skillsOmkar.csv")
	skills = list(data.columns.values)
	skillset = []
	for token in tokens:
		if token.lower() in skills:
			skillset.append(token)
        # print(token)
	for token in nlp_noun_chunks:
		token = token.text.lower().strip()
		if token in skills:
			skillset.append(token)
	return [i.capitalize() for i in set([i.lower() for i in skillset])]
def getEmail(inputString): 
    email = None
    try:
        pattern = re.compile(r"[a-z0-9\.\-+_]+@[a-z0-9\.\-+_]+\.[a-z]+")
        matches = pattern.findall(inputString) # Gets all email addresses as a list
        email = matches
    except Exception as e:
        print(e)
    return email
def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()
def getName(inputString):
  name=""
  NameFound=False
  nameList=[]
  if re.search("Name","\n".join(inputString.split("\n")[:7])):
    before,key,after=inputString.partition("Name")
    name +=re.sub("[^A-Z]", " ", after.strip().split("\n")[0],0,re.IGNORECASE).strip()
  else:
    firstLines=inputString.split("\n")
    email=getEmail(inputString)
    checkStrForName=re.sub('[^A-Za-z]','',email[0].split("@")[0])
    # print(checkStrForName)
    newtext=[line.strip() for line in firstLines if len(line.split("\t"))==1 and len(line.split())<=5 and len(line.split())!=0]
    sent=nltk.pos_tag(word_tokenize(" - ".join(newtext)))
    pattern = 'PROPER: {<NNP|NNPS>+}'

    cp = nltk.RegexpParser(pattern)
    cs = cp.parse(sent)
    iob_tagged = tree2conlltags(cs)
    chunk_tree = conlltags2tree(iob_tagged)
    n=len(iob_tagged)
    
    for i in range(0,n):
      if (iob_tagged[i][2]=="B-PROPER" or iob_tagged[i][2]=="I-PROPER") and re.fullmatch(r"^[a-zA-Z.]+$",iob_tagged[i][0]):
        name+=iob_tagged[i][0]+" "
      if iob_tagged[i][2]=="O" and len(name)>2:
        nameList.append(name)
        name=""
  processDict={}
  for iTerName in nameList:
    name=iTerName
    possibility=similar(iTerName.lower(),checkStrForName)
    if possibility>0.58:
      Name=iTerName
      NameFound=True
    elif possibility>0.2 and len(name.split())>1 :
      cheker=[name for val in name.split() if checkStrForName.startswith(val.lower())]
      processDict[name]=possibility

  if not NameFound:
    return "Name Not Found"
  if NameFound:
    return Name