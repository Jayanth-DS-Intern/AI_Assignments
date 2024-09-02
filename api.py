import io,json,uuid,os,firebase_admin,openai,PyPDF2,datetime
from fastapi import FastAPI, HTTPException,UploadFile,File
from pydantic import BaseModel
from firebase_admin import credentials, firestore
from anthropic import Client
from PIL import Image
from openai import OpenAI
from mcq import generate_assignment, chatgpt_url, chatgpt_headers,run_conversation,claude_brainbusters_generation,generate_answers_for_textbookquestions,generate_fill_in_the_blanks,claude_generate_activity_questions,generate_match_the_following_questions,generate_assertion_and_reason,claude_generate_case_based_questions,claude_generate_diagram_based_questions
from google.cloud import storage
from google.oauth2 import service_account
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

data_cred = {"type": "service_account",
    "project_id": os.getenv("project_id"),
    "private_key_id": os.getenv("private_key_id"),
    "private_key": os.getenv("private_key").replace('\\n', '\n'),
    "client_email": os.getenv("client_email"),
    "client_id": os.getenv("client_id"),
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": os.getenv("client_x509_cert_url"),
    "universe_domain":"googleapis.com"}

def initialize_firebase():
    if not firebase_admin._apps:
        cred = credentials.Certificate(data_cred)
        firebase_admin.initialize_app(cred)
    
    app = firebase_admin.initialize_app(credentials.Certificate(data_cred), name=str(uuid.uuid4()))
    
    return firestore.client(app)

db = initialize_firebase()

client = OpenAI(api_key=os.getenv("openaikey"))
anthropic_key = os.environ["anthropic_key"]
client_anthropic = Client(api_key=anthropic_key)

print("claude key--------->", anthropic_key)

chatgpt_url = "https://api.openai.com/v1/chat/completions"

claude_headers = {
    "content-type": "application/json",
    "Authorization":"Bearer {}".format(os.getenv("anthropic_key"))}

claude_url = 'https://api.anthropic.com/v1/messages'

chatgpt_headers = {
    "content-type": "application/json",
    "Authorization":"Bearer {}".format(os.getenv("openaikey"))}

app = FastAPI()

def initialize_gcs_client():
    credentials_dict = {
        "type": "service_account",
        "project_id": os.getenv("project_id_cloud"),
        "private_key_id": os.getenv("private_key_id_cloud"),
        "private_key": os.getenv("private_key_cloud").replace('\\n', '\n'),
        "client_email": os.getenv("client_email_cloud"),
        "client_id": os.getenv("client_id_cloud"),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": os.getenv("client_x509_cert_url")
    }
    
    credentials = service_account.Credentials.from_service_account_info(credentials_dict)
    return storage.Client(credentials=credentials, project=os.getenv("project_id_cloud"))

gcs_client = initialize_gcs_client()
bucket_name = "learninpad.appspot.com"

class AssignmentRequest(BaseModel):
    class_name: str
    subject_name: str
    lesson_name: str
    topic_assign: str
    prompt_topic_assign: str
    syllabus: str

@app.post("/generate-assignment")
async def create_assignment(request: AssignmentRequest):
    if request.syllabus == "CBSE":
        subject_collection = db.collection('cbse_subjects')
    elif request.syllabus == "SSC":
        subject_collection = db.collection('ssc_subjects')
    else:
        raise HTTPException(status_code=400, detail="Invalid syllabus")

        # Get subject_id
    subject_data = subject_collection.where("subject_name", "==", request.subject_name).limit(1).get()
    if not subject_data:
        raise HTTPException(status_code=404, detail="Subject not found")
    subject_id = subject_data[0].to_dict()['subject_id']

        # Get lesson_id
    lesson_collection = db.collection('lessons')
    lesson_document = lesson_collection.where("lesson_name", "==", request.lesson_name) \
                                       .where("subject_id", "==", subject_id) \
                                       .where("class", "==", request.class_name) \
                                       .limit(1).get()
    if not lesson_document:
        raise HTTPException(status_code=404, detail="Lesson not found")
    lesson_id = lesson_document[0].id
    lp = generate_assignment(request.topic_assign, chatgpt_url, chatgpt_headers, request.prompt_topic_assign)
    if not lp:
        raise HTTPException(status_code=500, detail="Failed to generate assignment")

    lp_json = json.loads(lp)
    final_data = []

    for j in lp_json['questions']:
        json_struct = {
            'class': request.class_name,
            'subject': request.subject_name,
            'lesson': request.lesson_name,
            'options': [],
            'question': j['question'],
            'answer': j['answer'],
            'level': j['question_level'],
            'question_type': j['question_type'],
            'type': 'single-line',
            'marks': '2' if j['question_type_short_or_long'] == 'Short Question' else '6',
            'syllabus': request.syllabus,
            'subject_id': subject_id,
            'lesson_id': lesson_id,
            'access': "public",
            'metadata': {"tags": [request.class_name, request.lesson_name, request.subject_name, j['question_type_short_or_long']]}
        }
        final_data.append(json_struct)

    collection = db.collection("question-library")
    for item in final_data:
        doc = collection.document()
        item['question_id'] = doc.id
        doc.set(item)

    bucket = gcs_client.bucket(bucket_name)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"ai_generated_files/assignments/{request.class_name}_{request.subject_name}_{request.lesson_name}_{timestamp}.json"
    blob = bucket.blob(filename)
    
    blob.upload_from_string(
        data=json.dumps(final_data),
        content_type='application/json'
    )
    
    gcs_file_url = f"https://storage.cloud.google.com/{bucket_name}/{filename}"
    
    return {
        "message": "Assignment generated and saved successfully",
        "data": final_data,
        "gcs_file_url": gcs_file_url
    }


@app.post("/generate-mcq")
async def generate_mcq(
    syllabus: str,
    class_name: str,
    subject_name: str,
    lesson_name: str,
    paragraph: str,
    prompt_mcq: str,
    image: Optional[UploadFile] = File(None),
    pdf: Optional[UploadFile] = File(None)
):
    if syllabus == "CBSE":
        subject_collection = db.collection('cbse_subjects')
    elif syllabus == "SSC":
        subject_collection = db.collection('ssc_subjects')
    else:
        raise HTTPException(status_code=400, detail="Invalid syllabus")

    subject_data = subject_collection.where("subject_name", "==", subject_name).limit(1).get()
    if not subject_data:
        raise HTTPException(status_code=404, detail="Subject not found")
    subject_id = subject_data[0].to_dict()['subject_id']

    lesson_collection = db.collection('lessons')
    lesson_document = lesson_collection.where("lesson_name", "==", lesson_name) \
                                       .where("subject_id", "==", subject_id) \
                                       .where("class", "==", class_name) \
                                       .limit(1).get()
    if not lesson_document:
        raise HTTPException(status_code=404, detail="Lesson not found")
    lesson_id = lesson_document[0].id
    try:
        if image:
            img_contents = await image.read()
            img = Image.open(io.BytesIO(img_contents))
            extracted_text = "Extracted text from image"  # Placeholder
            paragraph += "\n" + extracted_text

        if pdf:
            pdf_contents = await pdf.read()
            pdf_file = io.BytesIO(pdf_contents)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            pdf_text = ""
            for page in pdf_reader.pages:
                pdf_text += page.extract_text()
            paragraph += "\n" + pdf_text

        mcqs = run_conversation(paragraph, prompt_mcq)
        mcq_json = json.loads(mcqs)

        final_data = []
        for j in mcq_json['questions']:
            json_struct = {
                'class': class_name,
                'subject': subject_name,
                'lesson': lesson_name,
                'question': j['question'],
                'options': j['options'],
                'answer': j['answer'],
                'level': j['question_level'],
                'question_type': j['question_type'],
                'type': 'multi-choice',
                'subject_id': subject_id,
                'lesson_id': lesson_id,
                'access': "public",
                'marks': '1',
                'syllabus': syllabus,
                'metadata': {"tags": [class_name, lesson_name, subject_name, j['question_type']]}
            }
            final_data.append(json_struct)

        collection = db.collection("question-library")
        for item in final_data:
            doc = collection.document()
            item['question_id'] = doc.id
            doc.set(item)

        bucket = gcs_client.bucket(bucket_name)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ai_generated_files/mcqs/{class_name}_{subject_name}_{lesson_name}_{timestamp}.json"
        blob = bucket.blob(filename)
        
        blob.upload_from_string(
            data=json.dumps(final_data),
            content_type='application/json'
        )
        
        gcs_file_url = f"https://storage.cloud.google.com/{bucket_name}/{filename}"

        return {
            "message": "Assignment generated and saved successfully",
            "data": final_data,
            "gcs_file_url": gcs_file_url
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
class BrainBusterRequest(BaseModel):
    syllabus: str
    class_name: str
    subject: str
    lesson: str
    topic_name: str
    topic_id: str
    paragraph_brain: str
    prompt_brain: str

@app.post("/generate-brain-busters")
async def generate_brain_busters(request: BrainBusterRequest):
    try:
        brain_busters = claude_brainbusters_generation(request.paragraph_brain, request.prompt_brain)
        brain_busters_json = json.loads(brain_busters)
        
        cards = []
        for idx, question in enumerate(brain_busters_json['questions']):
            options = question['options']
            formatted_options = '\n'.join(f"{chr(97 + i)}. {option}" for i, option in enumerate(options))
            
            card = {
                'front_text': f"{idx+1}) {question['question']}\n{formatted_options}",
                'back_text': question['answer'],
                'back_image': None,
                'front_image': None
            }
            cards.append(card)

        json_struct = {
            'cards': cards,
            'topic_id': request.topic_id
        }

        collection = db.collection("brain_busters")
        doc = collection.document()
        doc.set(json_struct)

        bucket = gcs_client.bucket(bucket_name)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ai_generated_files/brain_busters/{request.class_name}_{request.subject}_{request.lesson}_{request.topic_name}_{timestamp}.json"
        blob = bucket.blob(filename)
        
        blob.upload_from_string(
            data=json.dumps(json_struct),
            content_type='application/json'
        )
        
        gcs_file_url = f"https://storage.cloud.google.com/{bucket_name}/{filename}"

        return {
            "message": "Brain Busters generated and saved successfully",
            "firebase_doc_id": doc.id,
            "gcs_file_url": gcs_file_url,
            "data": json_struct
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
class TextbookQuestionRequest(BaseModel):
    syllabus: str
    class_name: str
    subject_name: str
    lesson_name: str
    textbook_questions: str
    prompt: str

@app.post("/generate-textbook-answers")
async def generate_textbook_answers(request: TextbookQuestionRequest):
    if request.syllabus == "CBSE":
        subject_collection = db.collection('cbse_subjects')
    elif request.syllabus == "SSC":
        subject_collection = db.collection('ssc_subjects')
    else:
        raise HTTPException(status_code=400, detail="Invalid syllabus")

    subject_data = subject_collection.where("subject_name", "==", request.subject_name).limit(1).get()
    if not subject_data:
        raise HTTPException(status_code=404, detail="Subject not found")
    subject_id = subject_data[0].to_dict()['subject_id']

    lesson_collection = db.collection('lessons')
    lesson_document = lesson_collection.where("lesson_name", "==", request.lesson_name) \
                                       .where("subject_id", "==", subject_id) \
                                       .where("class", "==", request.class_name) \
                                       .limit(1).get()
    if not lesson_document:
        raise HTTPException(status_code=404, detail="Lesson not found")
    lesson_id = lesson_document[0].id
    try:
        answers = generate_answers_for_textbookquestions(request.textbook_questions, chatgpt_url, chatgpt_headers, request.prompt)
        answers_json = json.loads(answers)

        final_data = []
        for question in answers_json['questions']:
            json_struct = {
                'class': request.class_name,
                'subject': request.subject_name,
                'lesson': request.lesson_name,
                'question': question['question'],
                'options': question['options'],
                'answer': question['answer'],
                'level': question['question_level'],
                'question_type': question['question_type'],
                'type': 'multi-choice' if question['question_type_mcq_or_short_or_long'] == 'MCQ' else 'single-line',
                'marks': '1' if question['question_type_mcq_or_short_or_long'] == 'MCQ' else '2' if question['question_type_mcq_or_short_or_long'] == 'Short Question' else '6',
                'syllabus': request.syllabus,
                'subject_id': subject_id,
                'lesson_id': lesson_id,
                'access': "public",
                'metadata': {"tags": [request.class_name, request.lesson_name, request.subject_name, question['question_type_mcq_or_short_or_long'], "textbook-question"]}
            }
            final_data.append(json_struct)

        collection = db.collection("question-library")
        for item in final_data:
            doc = collection.document()
            item['question_id'] = doc.id
            doc.set(item)

        bucket = gcs_client.bucket(bucket_name)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ai_generated_files/textbook_answers/{request.class_name}_{request.subject_name}_{request.lesson_name}_{timestamp}.json"
        blob = bucket.blob(filename)
        
        blob.upload_from_string(
            data=json.dumps(final_data),
            content_type='application/json'
        )
        
        gcs_file_url = f"https://storage.cloud.google.com/{bucket_name}/{filename}"

        return {
            "message": "Textbook answers generated and saved successfully",
            "data": final_data,
            "gcs_file_url": gcs_file_url
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))   
    
class TextbookActivityRequest(BaseModel):
    syllabus: str
    class_name: str
    subject_name: str
    lesson_name: str
    textbook_text: str
    prompt: str

@app.post("/generate-textbook-activity-questions")
async def generate_textbook_activity_questions(request: TextbookActivityRequest):
    try:
        # Determine the correct subject collection
        if request.syllabus == "CBSE":
            subject_collection = db.collection('cbse_subjects')
        elif request.syllabus == "SSC":
            subject_collection = db.collection('ssc_subjects')
        else:
            raise HTTPException(status_code=400, detail="Invalid syllabus")

        subject_data = subject_collection.where("subject_name", "==", request.subject_name).limit(1).get()
        if not subject_data:
            raise HTTPException(status_code=404, detail="Subject not found")
        subject_id = subject_data[0].to_dict()['subject_id']

        lesson_collection = db.collection('lessons')
        lesson_document = lesson_collection.where("lesson_name", "==", request.lesson_name) \
                                           .where("subject_id", "==", subject_id) \
                                           .where("class", "==", request.class_name) \
                                           .limit(1).get()
        if not lesson_document:
            raise HTTPException(status_code=404, detail="Lesson not found")
        lesson_id = lesson_document[0].id

        lp = claude_generate_activity_questions(paragraph=request.textbook_text, headers=claude_headers, url=claude_url, prompt=request.prompt)
        lp_json = json.loads(lp)

        final_data = []
        for j in lp_json['questions']:
            json_struct = {
                'class': request.class_name,
                'subject': request.subject_name,
                'lesson': request.lesson_name,
                'question': j['question'],
                'options': j['options'],
                'answer': j['answer'],
                'level': j['question_level'],
                'question_type': j['question_type'],
                'type': 'multi-choice' if j['question_type_mcq_or_short_or_long'] == 'MCQ' else 'single-line',
                'marks': '1' if j['question_type_mcq_or_short_or_long'] == 'MCQ' else '2' if j['question_type_mcq_or_short_or_long'] == 'Short Question' else '4',
                'syllabus': request.syllabus,
                'subject_id': subject_id,
                'lesson_id': lesson_id,
                'access': "public",
                'metadata': {"tags": [request.class_name, request.lesson_name, request.subject_name, j['question_type_mcq_or_short_or_long'], "activity-questions"]}
            }
            final_data.append(json_struct)

        collection = db.collection("question-library")
        for item in final_data:
            doc = collection.document()
            item['question_id'] = doc.id
            doc.set(item)

        bucket = gcs_client.bucket(bucket_name)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ai_generated_files/textbook_activity/{request.class_name}_{request.subject_name}_{request.lesson_name}_{timestamp}.json"
        blob = bucket.blob(filename)
        
        blob.upload_from_string(
            data=json.dumps(final_data),
            content_type='application/json'
        )
        
        gcs_file_url = f"https://storage.cloud.google.com/{bucket_name}/{filename}"

        return {
            "message": "Textbook activity questions generated and saved successfully",
            "data": final_data,
            "gcs_file_url": gcs_file_url
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
class FillInTheBlanksRequest(BaseModel):
    syllabus: str
    class_name: str
    subject_name: str
    lesson_name: str
    textbook_text: str
    prompt: str

@app.post("/generate-fill-in-the-blanks")
async def generate_fill_in_the_blanks_for_prompt(request: FillInTheBlanksRequest):
    try:
        # Determine the correct subject collection
        if request.syllabus == "CBSE":
            subject_collection = db.collection('cbse_subjects')
        elif request.syllabus == "SSC":
            subject_collection = db.collection('ssc_subjects')
        else:
            raise HTTPException(status_code=400, detail="Invalid syllabus")

        # Get subject_id
        subject_data = subject_collection.where("subject_name", "==", request.subject_name).limit(1).get()
        if not subject_data:
            raise HTTPException(status_code=404, detail="Subject not found")
        subject_id = subject_data[0].to_dict()['subject_id']

        # Get lesson_id
        lesson_collection = db.collection('lessons')
        lesson_document = lesson_collection.where("lesson_name", "==", request.lesson_name) \
                                           .where("subject_id", "==", subject_id) \
                                           .where("class", "==", request.class_name) \
                                           .limit(1).get()
        if not lesson_document:
            raise HTTPException(status_code=404, detail="Lesson not found")
        lesson_id = lesson_document[0].id

        lp = generate_fill_in_the_blanks(request.textbook_text, chatgpt_url, chatgpt_headers, request.prompt)
        lp_json = json.loads(lp)

        final_data = []
        for j in lp_json['questions']:
            json_struct = {
                'class': request.class_name,
                'subject': request.subject_name,
                'lesson': request.lesson_name,
                'question': j['question'],
                'answer': j['answer'],
                'level': j['question_level'],
                'question_type': j['question_type'],
                'type': 'blank',
                'marks': '1',
                'syllabus': request.syllabus,
                'subject_id': subject_id,
                'lesson_id': lesson_id,
                'access': "public",
                'metadata': {"tags": [request.class_name, request.lesson_name, request.subject_name, j['question_type'], "Fill-in-the-blank"]}
            }
            final_data.append(json_struct)

        collection = db.collection("question-library")
        for item in final_data:
            doc = collection.document()
            item['question_id'] = doc.id
            doc.set(item)

        bucket = gcs_client.bucket(bucket_name)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ai_generated_files/fill_in_the_blanks/{request.class_name}_{request.subject_name}_{request.lesson_name}_{timestamp}.json"
        blob = bucket.blob(filename)
        
        blob.upload_from_string(
            data=json.dumps(final_data),
            content_type='application/json'
        )
        
        gcs_file_url = f"https://storage.cloud.google.com/{bucket_name}/{filename}"

        return {
            "message": "Fill in the blanks questions generated and saved successfully",
            "data": final_data,
            "gcs_file_url": gcs_file_url
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

class QuestionRequest(BaseModel):
    syllabus: str
    class_name: str
    subject_name: str
    lesson_name: str
    textbook_text: str
    prompt: str

@app.post("/generate-match-the-following")
async def generate_match_the_following(request: QuestionRequest):
    try:
        # Determine the correct subject collection
        if request.syllabus == "CBSE":
            subject_collection = db.collection('cbse_subjects')
        elif request.syllabus == "SSC":
            subject_collection = db.collection('ssc_subjects')
        else:
            raise HTTPException(status_code=400, detail="Invalid syllabus")

        # Get subject_id
        subject_data = subject_collection.where("subject_name", "==", request.subject_name).limit(1).get()
        if not subject_data:
            raise HTTPException(status_code=404, detail="Subject not found")
        subject_id = subject_data[0].to_dict()['subject_id']

        # Get lesson_id
        lesson_collection = db.collection('lessons')
        lesson_document = lesson_collection.where("lesson_name", "==", request.lesson_name) \
                                           .where("subject_id", "==", subject_id) \
                                           .where("class", "==", request.class_name) \
                                           .limit(1).get()
        if not lesson_document:
            raise HTTPException(status_code=404, detail="Lesson not found")
        lesson_id = lesson_document[0].id

        # Generate match the following questions
        lp = generate_match_the_following_questions(request.textbook_text, chatgpt_url, chatgpt_headers, request.prompt)
        lp_json = json.loads(lp)

        final_data = []
        for j in lp_json['questions']:
            json_struct = {
                'class': request.class_name,
                'subject': request.subject_name,
                'lesson': request.lesson_name,
                'question': j['question'],
                'options': j['options'],
                'answer': j['answer'],
                'level': j['question_level'],
                'question_type': j['question_type'],
                'type': 'match',
                'marks': '1',
                'syllabus': request.syllabus,
                'subject_id': subject_id,
                'lesson_id': lesson_id,
                'access': "public",
                'metadata': {"tags": [request.class_name, request.lesson_name, request.subject_name, j['question_type'], "Match-the-following"]}
            }
            final_data.append(json_struct)

        # Save to Firestore
        collection = db.collection("question-library")
        for item in final_data:
            doc = collection.document()
            item['question_id'] = doc.id
            doc.set(item)

        # Save to Google Cloud Storage
        bucket = gcs_client.bucket(bucket_name)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ai_generated_files/match_the_following/{request.class_name}_{request.subject_name}_{request.lesson_name}_{timestamp}.json"
        blob = bucket.blob(filename)
        
        blob.upload_from_string(
            data=json.dumps(final_data),
            content_type='application/json'
        )
        
        gcs_file_url = f"https://storage.cloud.google.com/{bucket_name}/{filename}"

        return {
            "message": "Match the following questions generated and saved successfully",
            "data": final_data,
            "gcs_file_url": gcs_file_url
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
class AssertionRequest(BaseModel):
    syllabus: str
    class_name: str
    subject_name: str
    lesson_name: str
    content: str
    prompt: str

@app.post("/generate-assertion-and-reason")
async def generate_assertion_and_reason_(request: AssertionRequest):
    try:
        if request.syllabus == "CBSE":
            subject_collection = db.collection('cbse_subjects')
        elif request.syllabus == "SSC":
            subject_collection = db.collection('ssc_subjects')
        else:
            raise HTTPException(status_code=400, detail="Invalid syllabus")

        # Get subject_id
        subject_data = subject_collection.where("subject_name", "==", request.subject_name).limit(1).get()
        if not subject_data:
            raise HTTPException(status_code=404, detail="Subject not found")
        subject_id = subject_data[0].to_dict()['subject_id']

        # Get lesson_id
        lesson_collection = db.collection('lessons')
        lesson_document = lesson_collection.where("lesson_name", "==", request.lesson_name) \
                                           .where("subject_id", "==", subject_id) \
                                           .where("class", "==", request.class_name) \
                                           .limit(1).get()
        if not lesson_document:
            raise HTTPException(status_code=404, detail="Lesson not found")
        lesson_id = lesson_document[0].id

        lp = generate_assertion_and_reason(request.content, chatgpt_url, chatgpt_headers, request.prompt)
        lp_json = json.loads(lp)

        final_data = []
        for j in lp_json['questions']:
            json_struct = {
                'class': request.class_name,
                'subject': request.subject_name,
                'lesson': request.lesson_name,
                'question': j['question'],
                'options': j['options'],
                'answer': j['answer'],
                'level': j['question_level'],
                'question_type': j['question_type'],
                'type': 'assertion-reason',
                'marks': '1',
                'syllabus': request.syllabus,
                'subject_id': subject_id,
                'lesson_id': lesson_id,
                'access': "public",
                'metadata': {"tags": [request.class_name, request.lesson_name, request.subject_name, j['question_type'], "Assertion and Reason"]}
            }
            final_data.append(json_struct)

        collection = db.collection("question-library")
        for item in final_data:
            doc = collection.document()
            item['question_id'] = doc.id
            doc.set(item)

        bucket = gcs_client.bucket(bucket_name)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ai_generated_files/assertion_and_reason/{request.class_name}_{request.subject_name}_{request.lesson_name}_{timestamp}.json"
        blob = bucket.blob(filename)
        
        blob.upload_from_string(
            data=json.dumps(final_data),
            content_type='application/json'
        )
        
        gcs_file_url = f"https://storage.cloud.google.com/{bucket_name}/{filename}"

        return {
            "message": "Assertion and Reason questions generated and saved successfully",
            "data": final_data,
            "gcs_file_url": gcs_file_url
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
class CaseBasedRequest(BaseModel):
    syllabus: str
    class_name: str
    subject_name: str
    lesson_name: str
    topic: str
    prompt: str
    

@app.post("/generate-case-based-questions")
async def generate_case_based_questions_(request: CaseBasedRequest):
    try:
        if request.syllabus == "CBSE":
            subject_collection = db.collection('cbse_subjects')
        elif request.syllabus == "SSC":
            subject_collection = db.collection('ssc_subjects')
        else:
            raise HTTPException(status_code=400, detail="Invalid syllabus")

        # Get subject_id
        subject_data = subject_collection.where("subject_name", "==", request.subject_name).limit(1).get()
        if not subject_data:
            raise HTTPException(status_code=404, detail="Subject not found")
        subject_id = subject_data[0].to_dict()['subject_id']

        # Get lesson_id
        lesson_collection = db.collection('lessons')
        lesson_document = lesson_collection.where("lesson_name", "==", request.lesson_name) \
                                           .where("subject_id", "==", subject_id) \
                                           .where("class", "==", request.class_name) \
                                           .limit(1).get()
        if not lesson_document:
            raise HTTPException(status_code=404, detail="Lesson not found")
        lesson_id = lesson_document[0].id

        lp = claude_generate_case_based_questions(request.topic,request.prompt)
        lp_json = json.loads(lp)

        final_data = []
        for j in lp_json['questions']:
            json_struct = {
                'class': request.class_name,
                'subject': request.subject_name,
                'lesson': request.lesson_name,
                'case_study':j['case_study'],
                'question': j['question'],
                'options': j['options'],
                'answer': j['answer'],
                'topic': j.get('topic', request.topic),
                'level': j['question_level'],
                'question_type': j['question_type'],
                'type': 'assertion-reason',
                'marks': '1',
                'syllabus': request.syllabus,
                'subject_id': subject_id,
                'lesson_id': lesson_id,
                'access': "public",
                'metadata': {"tags": [request.class_name, request.lesson_name, request.subject_name, j['question_type'], "case-based-question"]}
            }
            final_data.append(json_struct)

        collection = db.collection("question-library")
        for item in final_data:
            doc = collection.document()
            item['question_id'] = doc.id
            doc.set(item)

        bucket = gcs_client.bucket(bucket_name)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ai_generated_files/Case_Based_Questions/{request.class_name}_{request.subject_name}_{request.lesson_name}_{timestamp}.json"
        blob = bucket.blob(filename)
        
        blob.upload_from_string(
            data=json.dumps(final_data),
            content_type='application/json'
        )
        
        gcs_file_url = f"https://storage.cloud.google.com/{bucket_name}/{filename}"

        return {
            "message": "Case Based Question Saved Successfully",
            "data": final_data,
            "gcs_file_url": gcs_file_url
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@app.post("/generate/diagram/based/questions")
async def generate_diagram_based_questions(
    syllabus: str,
    class_name: str,
    subject_name: str,
    lesson_name: str,
    prompt: str,
    temp_image: Optional[UploadFile] = File(None),
):
    try:
        if syllabus not in ["CBSE", "SSC"]:
            raise HTTPException(status_code=400, detail="Invalid syllabus")

        subject_collection = db.collection(f'{syllabus.lower()}_subjects')
        subject_data = subject_collection.where("subject_name", "==", subject_name).limit(1).get()
        if not subject_data:
            raise HTTPException(status_code=404, detail="Subject not found")
        subject_id = subject_data[0].to_dict()['subject_id']

        lesson_collection = db.collection('lessons')
        lesson_document = lesson_collection.where("lesson_name", "==", lesson_name) \
                                           .where("subject_id", "==", subject_id) \
                                           .where("class", "==", class_name) \
                                           .limit(1).get()
        if not lesson_document:
            raise HTTPException(status_code=404, detail="Lesson not found")
        lesson_id = lesson_document[0].id

        image_url = None
        if temp_image:
            image_content = await temp_image.read()
            bucket = storage.bucket(bucket_name)
            image_path = f"questions_library/{temp_image.filename}"
            blob = bucket.blob(image_path)
            blob.upload_from_string(image_content, content_type=temp_image.content_type)
            image_url = blob.public_url

        lp = claude_generate_diagram_based_questions(temp_image, prompt)
        lp_json = json.loads(lp)

        final_data = []
        for j in lp_json['questions']:
            json_struct = {
        'class': class_name,
        'subject': subject_name,
        'lesson': lesson_name,
        'image_url': image_url,
        'question': j['question'],
        'answer': j['answer'],
        'topic': lp_json['topic'],
        'level': j['question_level'],
        'question_type': j['question_type'],
        'type': 'diagram',
        'marks': '1' if j['question_type_mcq_or_short_or_long'] == 'MCQ' else '2' if j['question_type_mcq_or_short_or_long'] == 'Short Question' else '4',
        'syllabus': syllabus,
        'subject_id': subject_id,
        'lesson_id': lesson_id,
        'access': "public",
        'metadata': {"tags": [class_name, lesson_name, subject_name, j['question_type'], "diagram-based-question"]}
    }
        final_data.append(json_struct)

        collection = db.collection("question-library")
        for item in final_data:
            doc = collection.document()
            item['question_id'] = doc.id
            doc.set(item)

        bucket = gcs_client.bucket(bucket_name)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ai_generated_files/Diagram_Based_Questions/{class_name}_{subject_name}_{lesson_name}_{timestamp}.json"
        blob = bucket.blob(filename)
        
        blob.upload_from_string(
            data=json.dumps(final_data),
            content_type='application/json'
        )
        
        gcs_file_url = f"https://storage.cloud.google.com/{bucket_name}/{filename}"

        return {
            "message": "Diagram Based Questions Saved Successfully",
            "data": final_data,
            "gcs_file_url": gcs_file_url
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
