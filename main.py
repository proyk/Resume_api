from fastapi import FastAPI,File, UploadFile
from pdfminer.high_level import extract_text
import re
import io
from difflib import SequenceMatcher
import nltk
from nltk.tokenize import word_tokenize
from nltk.chunk import conlltags2tree, tree2conlltags
import spacy

import pandas as pd
from datetime import datetime 
from dateutil import parser  

from fastapi.middleware.cors import CORSMiddleware
if not nltk.data.find('taggers/averaged_perceptron_tagger'):
  nltk.download('averaged_perceptron_tagger')

if not nltk.data.find('tokenizers/punkt'):
  nltk.download('punkt')

if not nltk.data.find('chunkers/maxent_ne_chunker'):
  nltk.download('maxent_ne_chunker')

if not nltk.data.find('corpora/words'):
  nltk.download('words')

if not nltk.data.find('corpora/stopwords'):
  nltk.download('stopwords')
app=FastAPI()
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get('/')
def index():
    return {"Message":"Api is working!!"}
    
@app.post("/upload")
async def upload(file: UploadFile = File(...)):
  data={}
  status=None
  message=None
  try:
      contents = await file.read()
      text = extract_text(io.BytesIO(contents))
      
      if len(text)>20:
        ResumeObj=ResumeExtractor(text)
        data=ResumeObj.getExtractedData()
        status="success"
        message="Resume Successfully Parsed!"
        
      else:
        status='failure'
        message="File does not contains text"

  except OSError as e:

    status='failure'
    message=f"Error extracting text: {e}"
  except Exception as e:
    status='failure'
    message=str(e)
    
  finally:
      await file.close()
      finalData={
          "status":status,
          'message':message,
          'data':data
        }
  
  return finalData
#RESUME EXTRACTION
class ResumeExtractor:
  def __init__(self,inputResumeText):
    self.inputString=inputResumeText


    #required fileds variable
    self.first_name="not_found"
    self.last_name="not_found"
    self.full_name="not_found"
    self.gender='not_found'
    self.email='not_found'
    self.mobile=[]
    self.skills=[]
    self.total_exp='0'
    self.education_details=[]

    #variable that use in operations
    self.degreeStartWord={
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
    self.degreesWord={
          "B.E":"B.E",
          "BE":"BE",
          "M.E":"M.E",
          "ME":"ME",
          "B.SC":"B.SC",
          "BSC":"BSC",
          "MSC":"MSC",
          "BTECH":"BTECH",
          "BCA":"BCA",
          "MCA":"MCA",
          "BBA":"BBA",
          "MBA":"MBA",
          }
    self.reserveWordForInstituteName={
        "university":"university",
        "college":"college",
        "collage":"collage",
        "institute":"institute"
        }

    #extract Data
    self.extractAllData()



  def extractAllData(self):
    self.getEmail(self.inputString)
    self.getName(self.inputString)
    self.getPhone(self.inputString)
    self.getSkill(self.inputString)
    self.getExperience(self.inputString)
    self.getEducationDetails(self.inputString)
    



  def getName(self,inputString):
    name=""
    dict={}
    NameFound=False
    nameList=[]
    
    
    firstLines=inputString.split("\n")
    
    if len(self.email)>0:

      checkStrForName=re.sub('[^A-Za-z]','',self.email.split("@")[0])
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
    
      
      Name=''
      for iTerName in nameList:
        if len(Name.split())<=3:
          
          name=iTerName
          possibility=SequenceMatcher(None, iTerName.lower(), checkStrForName).ratio()
          if possibility>=0.50:
            
            if iTerName not in Name:
              Name+=iTerName
            NameFound=True
      
      if NameFound :
        name=" ".join(set(Name.split()))
        name=Name.split()
        if len(name)==1:
          self.full_name=name
          self.first_name=name
        elif len(name)>1:
          self.first_name=name[0]
          self.last_name=name[len(name)-1]
          self.full_name=Name

  def getEmail(self,inputString): 
    email = None
    try:
        pattern = re.compile(r"[a-z0-9\.\-+_]+@[a-z0-9\.\-+_]+\.[a-z]+")
        matches = pattern.findall(inputString) # Gets all email addresses as a list
        email = matches
    except Exception as e:
        print(e)
    self.email=" ".join(email)
  def getPhone(self,inputString):
    number = ''
    try:
        pattern = re.compile(r'([+(]?\d+[)\-]?[ \t\r\f\v]*[(]?\d{2,}[()\-]?[ \t\r\f\v]*\d{2,}[()\-]?[ \t\r\f\v]*\d*[ \t\r\f\v]*\d*[ \t\r\f\v]*)')
        match = pattern.findall(inputString)
        match = [re.sub(r'[()\,.]', '', el).strip() for el in match if len(re.sub(r'[()\-.,\D+]', '', el))>9 and len(re.sub(r'[()\-.,\D+]','',el)) <= 15]
        number = match
    except:
        pass
    self.mobile=number
  def getSkill(self,inputString):
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
    self.skills=[i.capitalize() for i in set([i.lower() for i in skillset])]
  def getExperience(self,inputString):
    extractedText=inputString
    total_exp=0
    wordsOfStartPoint="experience|work history|employment"
    wordsOfEndPoint="education|hobbies|language|ACADEMIC QUALIFICATIONS"
    if re.search(r""+wordsOfStartPoint+"",extractedText,flags=re.IGNORECASE):
      lengthOfSplit=len(re.findall(r""+wordsOfStartPoint+"",extractedText,flags=re.IGNORECASE))
      experienceAfterText=re.split(r""+wordsOfStartPoint+"",extractedText,flags=re.IGNORECASE,maxsplit=lengthOfSplit)[lengthOfSplit]
      experience_text_for_No_date_mention=re.split(r""+wordsOfStartPoint+"",extractedText,flags=re.IGNORECASE,maxsplit=1)[1]
      experienceText=re.split(r""+wordsOfEndPoint+"",experienceAfterText,flags=re.IGNORECASE,maxsplit=1)[0]  
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
        self.total_exp=total_exp
      except Exception as e:
        self.total_exp=e
  def getEducationDetails(self,inputString):
      institute_name=[]
      degreeL=[]
      educationSection="Education|Qualification summary|Educational Qualification|Qualification|Degrees and Qualifications|ACADEMIC QUALIFICATIONS" 
      if re.search(r""+educationSection+"",inputString,flags=re.IGNORECASE):
        splitText=re.split(r""+educationSection+"",inputString,flags=re.IGNORECASE,maxsplit=1)[1]
        nlp = spacy.load('en_core_web_sm')
        institute=""
        degree=""
        institute_found=False
        degree_found=False
        for line in inputString.split("\n"):
          line=str(line).strip("• ")
          for word in line.split():
            if (re.sub('\W+','', word).lower() in self.reserveWordForInstituteName or word.lower().startswith(tuple(self.reserveWordForInstituteName))) and line.lower().startswith(tuple(self.reserveWordForInstituteName))==False:
              line=line.strip()

              index = line.lower().find(word.lower())
              before_text=line[:index]
              if len(before_text)>0:
                tagLine=nlp(line)
                for test in tagLine.ents:
                  if re.search(r"[^A-Za-z0-9\s]", str(test)):
                    pass
                  else:

                    if test.label_=="ORG":
                      before_text=str(test)
                    else:
                      before_text=re.split(r'(?<![\s\n])\W{2,}|\W{2,}(?![\s\n])', before_text)[-1]

                
                after_text=re.split(r'(?<!\s)\W{2,}|\W{2,}(?!\s)', line[index:])[0]
                if after_text in before_text:
                  final_text=before_text
                else:
                  final_text=before_text+" "+after_text
                if bool(re.search(r'^([a-zA-Z.,]|\s){0,1}([a-zA-Z.,]|\s)*$', final_text)):
                  institute_found=True
                  institute=final_text.rstrip(',')
                  institute_name.append(institute)

          if line.lower().startswith(tuple(self.degreeStartWord)):
            text=re.split(r"[^a-zA-Z' ]+", line)[0]
            degree_found=True
            degree=text
            degreeL.append(degree)
          if re.search(r"^(b\.|m\.)", line, flags=re.IGNORECASE):
            
            if re.sub('\W+','', line).upper().startswith(tuple(self.degreesWord)):
              match = re.search(r"[)\]]", line)
              if match:
                degree=line[:match.end()]
                degreeL.append(degree)
                degree_found=True
              else:
                degree=line
                degreeL.append(degree)
                degree_found=True
          for word in re.split(',| |:',line):
            
            if (re.sub('\W+','', word) in self.degreesWord) and not word.islower():
              degree=word
              degreeL.append(degree)
              degree_found=True
            if word.startswith(tuple(self.degreesWord)):

            
              splitWord=re.split(r"\s*[[(]|\sin\s*", word)
              if len(splitWord)>1:
                degree=line
                degreeL.append(degree)
                degree_found=True
          
          if degree_found and institute_found:
            
            self.education_details.append({"course":degree,"institute":institute})
            degreeL=list(set(degreeL))
            institute_name=list(set(institute_name))
            if degree in degreeL:
              degreeL.remove(degree)
            if institute in institute_name:
              institute_name.remove(institute)
            degree=''
            institute=''
            degree_found=False
            institute_found=False
        degreeL=list(set(degreeL))
        institute_name=list(set(institute_name))
        for degreeWithoutInstitute in degreeL:
          self.education_details.append({"course":degreeWithoutInstitute,"institute":'not_found'})
        for instituteWithoutDegree in institute_name:
          self.education_details.append({"course":'not_found',"institute":instituteWithoutDegree})
  def getExtractedData(self):
    return {"first_name":self.first_name,
    "last_name":self.last_name,
    "full_Name":self.full_name,
    "gender":self.gender,
    "email":self.email,
    "mobile":self.mobile,
    "skills":self.skills,
    "total_exp":self.total_exp,
    "education_details":self.education_details,
    }