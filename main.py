# File: main.py
from fastapi import FastAPI, Depends, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2AuthorizationCodeBearer
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from azure.storage.blob import BlobServiceClient
from sqlalchemy.orm import Session
import models, schemas, crud
from database import get_db, Base, engine
import os
import uuid
from contextlib import asynccontextmanager
from fastapi.responses import StreamingResponse, Response
import json, asyncio
from magentic_one_helper import MagenticOneHelper
from autogen_agentchat.messages import MultiModalMessage, TextMessage, ToolCallExecutionEvent, ToolCallRequestEvent
from autogen_agentchat.base import TaskResult
from magentic_one_helper import generate_session_name

from datetime import datetime 

session_data = {}
MAGENTIC_ONE_DEFAULT_AGENTS = [
            {
            "input_key":"0001",
            "type":"MagenticOne",
            "name":"Coder",
            "system_message":"",
            "description":"",
            "icon":"👨‍💻"
            },
            {
            "input_key":"0002",
            "type":"MagenticOne",
            "name":"Executor",
            "system_message":"",
            "description":"",
            "icon":"💻"
            },
            {
            "input_key":"0003",
            "type":"MagenticOne",
            "name":"FileSurfer",
            "system_message":"",
            "description":"",
            "icon":"📂"
            },
            {
            "input_key":"0004",
            "type":"MagenticOne",
            "name":"WebSurfer",
            "system_message":"",
            "description":"",
            "icon":"🏄‍♂️"
            },
            ]

# Lifespan handler for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown code (optional)
    # engine.dispose()

app = FastAPI()

# Allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Azure AD Authentication (Mocked for example)
oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl="https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
    tokenUrl="https://login.microsoftonline.com/common/oauth2/v2.0/token"
)

async def validate_tokenx(token: str = Depends(oauth2_scheme)):
    # In production, implement proper token validation
    print("Token:", token)
    return {"sub": "user123", "name": "Test User"}  # Mocked user data

async def validate_token(token: str = None):
    # In production, implement proper token validation
    print("Token:", token)
    return {"sub": "user123", "name": "Test User"}  # Mocked user data

from openai import AsyncAzureOpenAI

# Azure OpenAI Client
async def get_openai_client():
    azure_credential = DefaultAzureCredential()
    token_provider = get_bearer_token_provider(
        azure_credential, "https://cognitiveservices.azure.com/.default"
    )
    
    return AsyncAzureOpenAI(
        api_version="2024-12-01-preview",
        # azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        azure_endpoint="https://aoai-eastus-mma-cdn.openai.azure.com/",
        azure_ad_token_provider=token_provider
    )


def write_log(path, log_entry):
    # check if the file exists if not create it
    if not os.path.exists(path):
        with open(path, "w") as f:
            f.write("")
    # append the log entry to a file
    with open(path, "a") as f:
        try:
            f.write(f"{json.dumps(log_entry)}\n")
        except Exception as e:
            # TODO: better handling of the error
            log_entry["content"] = f"Error writing log entry: {str(e)}"
            f.write(f"{json.dumps(log_entry)}\n")



def get_current_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
def get_agent_icon(agent_name) -> str:
    if agent_name == "MagenticOneOrchestrator":
        agent_icon = "🎻"
    elif agent_name == "WebSurfer":
        agent_icon = "🏄‍♂️"
    elif agent_name == "Coder":
        agent_icon = "👨‍💻"
    elif agent_name == "FileSurfer":
        agent_icon = "📂"
    elif agent_name == "Executor":
        agent_icon = "💻"
    elif agent_name == "user":
        agent_icon = "👤"
    else:
        agent_icon = "🤖"
    return agent_icon

async def summarize_plan(plan, client):
    prompt = "You are a project manager."
    text = f"""Summarize the plan for each agent into single-level only bullet points.

    Plan:
    {plan}
    """
    
    from autogen_core.models import UserMessage, SystemMessage
    messages = [
        UserMessage(content=text, source="user"),
        SystemMessage(content=prompt)
    ]
    result = await client.create(messages)
    # print(result.content)
    
    plan_summary = result.content
    return plan_summary
async def display_log_message(log_entry, logs_dir, session_id, client=None):
    _log_entry_json = log_entry

    log_file_name = f"{session_id}.log"
    log_path = os.path.join(logs_dir, log_file_name)
    log_message_json = {
        "time": get_current_time(),
        "type": None,
        "source": None,
        "content": None,
        "stop_reason": None,
        "models_usage": None,
    }

    response = {
        "time": get_current_time(),
        "type": None,
        "source": None,
        "content": None,
        "stop_reason": None,
        "models_usage": None,
        "content_image": None,
        "session_id": session_id
    }

    # Check if the message is a TaskResult class
    if isinstance(_log_entry_json, TaskResult):
        _type = "TaskResult"
        _source = "TaskResult"
        _content = _log_entry_json.messages[-1]
        _stop_reason = _log_entry_json.stop_reason
        _timestamp = get_current_time()
        icon_result = "🎯"
        # Do not display the final answer just yet, only set it in the session state
        # st.session_state["final_answer"] = _content.content
        # st.session_state["stop_reason"] = _stop_reason

        log_message_json["type"] = _type
        log_message_json["source"] = _source
        log_message_json["content"] = _content.content
        log_message_json["stop_reason"] = _stop_reason

        response["type"] = _type
        response["source"] = _source
        response["content"] = _content.content
        response["stop_reason"] = _stop_reason

    elif isinstance(_log_entry_json, MultiModalMessage):
        _type = _log_entry_json.type
        _source = _log_entry_json.source
        _content = _log_entry_json.content
        _timestamp = get_current_time()

        log_message_json["type"] = _type
        log_message_json["source"] = _source
        log_message_json["content"] = _content[0]

        response["type"] = _type
        response["source"] = _source
        # response["content"] = {
        #     "text": _content[0],
        #     "image": _content[1].data_uri
        # }
        response["content"] = _content[0]
        response["content_image"] = _content[1].data_uri

    elif isinstance(_log_entry_json, TextMessage):
        _type = _log_entry_json.type
        _source = _log_entry_json.source
        _content = _log_entry_json.content
        _timestamp = get_current_time()

        # if _source == "MagenticOneOrchestrator" and not st.session_state["planned"]:
        #     plan_summary = await summarize_plan(_content, client)
        #     SESSION_INFO.write(f"Session ID: `{st.session_state.session_id}`")
        #     PLAN_PLACE.write(plan_summary)
        #     st.session_state["planned"] = True

        log_message_json["type"] = _type
        log_message_json["source"] = _source
        log_message_json["content"] = _content

        response["type"] = _type
        response["source"] = _source
        response["content"] = _content

    elif isinstance(_log_entry_json, ToolCallExecutionEvent):
        _type = _log_entry_json.type
        _source = _log_entry_json.source
        _content = _log_entry_json.content
        _timestamp = get_current_time()

        log_message_json["type"] = _type
        log_message_json["source"] = _source
        log_message_json["content"] = _content[0].content

        response["type"] = _type
        response["source"] = _source
        response["content"] = _content[0].content

    elif isinstance(_log_entry_json, ToolCallRequestEvent):
        _type = _log_entry_json.type
        _source = _log_entry_json.source
        _content = _log_entry_json.content
        _timestamp = get_current_time()
        _models_usage = _log_entry_json.models_usage

        log_message_json["type"] = _type
        log_message_json["source"] = _source
        log_message_json["content"] = _content[0].arguments

        response["type"] = _type
        response["source"] = _source
        response["content"] = _content[0].arguments
        response["models_usage"] = _models_usage

    else:
        log_message_json["type"] = "N/A"
        log_message_json["content"] = "Agents mumbling."

        response["type"] = "N/A"
        response["content"] = "Agents mumbling."

    write_log(log_path, log_message_json)
    return response



# Azure Services Setup (Mocked for example)
blob_service_client = BlobServiceClient.from_connection_string(
    "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;" + \
    "AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;" + \
    "BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;"
)

# Chat Endpoint
# @app.post("/chat", response_model=schemas.ChatMessageResponse)
@app.post("/chat")
async def chat_endpoint(
    message: schemas.ChatMessageCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(validate_token)
):
    # print("User:", user["sub"])
    # # Mock OpenAI response for demonstration
    # client = await get_openai_client()
    # response = await client.chat.completions.create(
    #     model="gpt-4o-mini",
    #     messages=[{"role": "user", "content": message.content}]
    # )
    # # mock_response = "This is a mock AI response"
    # mock_response = response.choices[0].message.content
    
    mock_response = """
This is a mock AI response in Mardown format.

## Heading 2

- List item 1
  - List item 2

**Bold text**


```python
print("Hello, World!")
```

    """
    
    # # Create user if not exists
    # db_user = crud.get_user(db, user["sub"])
    # if not db_user:
    #     db_user = models.User(
    #         id=user["sub"],
    #         username="test_user",
    #         email="test@example.com"
    #     )
    #     db.add(db_user)
    #     db.commit()
    #     db.refresh(db_user)
    
    # # Create chat message
    # db_message = crud.create_chat_message(
    #     db=db,
    #     message=message,
    #     user_id=user["sub"]
    # )
    # db_message.response = mock_response
    # db.commit()
    # db.refresh(db_message)

    db_message = schemas.ChatMessageResponse(
        id=uuid.uuid4(),
        content=message.content,
        response =  mock_response,
        timestamp = "2021-01-01T00:00:00",
        user_id =  user["sub"],
        orm_mode = True
    )
    response = {
        "time": get_current_time(),
        "type": "Muj",
        "source": "MagenticOneOrchestrator",
        "content": mock_response,
        "stop_reason": None,
        "models_usage": None,
        "content_image": None,
    }
    #  json_response["response"] = f'session {session_id} and message: {json_response["content"]}'
    #         yield f"data: {json.dumps(json_response)}\n\n"
    # return db_message
    return Response(content=json.dumps(response), media_type="application/json")


# File Upload Endpoint
@app.post("/upload-file", response_model=schemas.FileResponse)
async def upload_file(
    file: UploadFile,
    db: Session = Depends(get_db),
    user: dict = Depends(validate_token)
):
    # Mock file storage
    blob_url = f"https://example.com/files/{uuid.uuid4()}-{file.filename}"
    
    # Create file record
    db_file = crud.create_file(
        db=db,
        filename=file.filename,
        user_id=user["sub"],
        blob_url=blob_url,
        size=1024  # Mock size
    )
    
    return db_file





# Chat Endpoint
@app.post("/start", response_model=schemas.ChatMessageResponse)
async def chat_endpoint(
    message: schemas.ChatMessageCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(validate_token)
):
    print("User:", user["sub"])
    _agents = json.loads(message.agents) if message.agents else MAGENTIC_ONE_DEFAULT_AGENTS
   
    # Mock OpenAI response for demonstration
    # client = await get_openai_client()
    # response = await client.chat.completions.create(
    #     model="gpt-4o-mini",
    #     messages=[{"role": "user", "content": message.content}]
    # )
    # # mock_response = "This is a mock AI response"
    # mock_response = response.choices[0].message.content
    
    # # Create user if not exists
    # db_user = crud.get_user(db, user["sub"])
    # if not db_user:
    #     db_user = models.User(
    #         id=user["sub"],
    #         username="test_user",
    #         email="test@example.com"
    #     )
    #     db.add(db_user)
    #     db.commit()
    #     db.refresh(db_user)
    
    # # Create chat message
    # db_message = crud.create_chat_message(
    #     db=db,
    #     message=message,
    #     user_id=user["sub"]
    # )
    # db_message.response = mock_response
    # db.commit()
    # db.refresh(db_message)
    _session_id = generate_session_name()
    session_data[_session_id] = {
        "user_id": user["sub"],
        "user_message": message.content,
        "messages": [],

        "agents": _agents,
        "run_mode_locally" : False
    }

    db_message = schemas.ChatMessageResponse(
        id=uuid.uuid4(),
        content=message.content,
        response =  _session_id,
        timestamp = "2021-01-01T00:00:00",
        user_id =  user["sub"],
        orm_mode = True
    )
    
    return db_message


# Streaming Chat Endpoint
@app.get("/chat-stream")
async def chat_stream(
    session_id: str = Query(...),
    db: Session = Depends(get_db),
    user: dict = Depends(validate_token)
):
    # create folder for logs if not exists
    logs_dir="./logs"
    if not os.path.exists(logs_dir):    
        os.makedirs(logs_dir)
    
    task = session_data[session_id]["user_message"]
    # TODO DBG - Remove
    # task = "Generate a python script and execute Fibonacci series below 1000"
    
     # Initialize the MagenticOne system
    magentic_one = MagenticOneHelper(logs_dir=logs_dir, save_screenshots=False, run_locally=session_data[session_id]["run_mode_locally"])
    await magentic_one.initialize(agents=session_data[session_id]["agents"], session_id=session_id)


    stream, cancellation_token = magentic_one.main(task = task)
    
    session_data[session_id]["cancellation_token"] = cancellation_token

    # async for log_entry in stream:
    #     yield f"data: {json.dumps({'response': f'session {session_id} and message: {log_entry.content}'})}\n\n"


    async def event_generator(stream):

        async for log_entry in stream:
            json_response = await display_log_message(log_entry=log_entry, logs_dir=logs_dir, session_id=magentic_one.session_id, client=magentic_one.client)
            # yield f"data: {json.dumps({'response': f'session {session_id} and message: {log_entry.content}'})}\n\n"
            json_response["response"] = f'session {session_id} and message: {json_response["content"]}'
            yield f"data: {json.dumps(json_response)}\n\n"

        
        # for i in range(3):
        #     # Replace with real background logic
        #     yield f"data: {json.dumps({'response': f'Chunk {i} from server in session {session_id} and message: {task}'})}\n\n"
        #     await asyncio.sleep(1)
    return StreamingResponse(event_generator(stream), media_type="text/event-stream")

@app.get("/stop")
async def stop(session_id: str = Query(...)):
    try:
        print("Stopping session:", session_id)
        cancellation_token = session_data[session_id].get("cancellation_token")
        if cancellation_token:
            cancellation_token.cancel()
            return {"status": "success", "message": f"Session {session_id} cancelled successfully."}
        else:
            return {"status": "error", "message": "Cancellation token not found."}
    except Exception as e:
        print(f"Error stopping session {session_id}: {str(e)}")
        return {"status": "error", "message": f"Error stopping session: {str(e)}"}