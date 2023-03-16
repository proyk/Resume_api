## Resume API
This is a RESTful API developed using the FastAPI framework to handle resume information for a job board. This API allows users to create, retrieve, update and delete resumes. The API has been developed using Python 3.9.

### Setup
**1.  Clone the repository**
```
git clone https://github.com/your_username/resume-api.git
```
**2.  Create a virtual environment**
```
 python -m venv env 
```
**3.  Activate the virtual environment**

For Windows:

```
.\env\Scripts\activate
```
For Unix/Linux:

```
source env/bin/activate
```
**4.  Install dependencies**
```
pip install -r requirements.txt
```
**5.  Start the server**
```
hypercorn main.py --reload
```
> --reload is use for when you edit main.py file it reload api automatically

**All Endpoints of API is shown at `/docs` endpoint like this : http://localhost:8000/docs**

###### API endpoints
* / -> METHOD `GET`
  - Check Api is Working or Not
* /upload -> METHOD `POST`
  - request a `PDF` file and it will responde with `JSON` data.
## Response `JSON` data
```json
{
  "status": "success",
  "message": "Resume Successfully Parsed!",
  "data": {
    "first_name": "Yash",
    "last_name": "Ramanuj",
    "full_Name": "Yash Ramanuj ",
    "gender": "not_found",
    "email": "yashrmnj@gmail.com",
    "mobile": [
      "9574947065"
    ],
    "skills": [
      "Html",
      "Flask",
      "Python",
      "Coding",
      "Django",
      "Mysql",
      "Css"
    ],
    "total_exp": "0",
    "education_details": [
      {
        "course": "MCA",
        "institute": "GLS university Ahmedabad"
      },
      {
        "course": "BCA",
        "institute": "Saurashtra University University Rajkot"
      }
    ]
  }
}
```
