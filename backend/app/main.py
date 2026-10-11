from fastapi import FastAPI,Request
from fastapi.responses import JSONResponse
from app.exceptions.document import DocumentNotFoundError
from app.routers.document import router as document_router
from app.exceptions.user import (UserAlreadyExistsError,
                                 InvalidCredentialsError,
                                 InvalidAccessTokenError,
                                 AdminRequiredError)
from app.routers.user import router as user_router
from app.exceptions.file_upload import FileTooLargeError,EmptyFileError,UnsupportedFileTypeError
from app.models.document_chunk import DocumentChunk
from app.routers.semantic_search import router as semantic_search_router
from app.routers.ask import router as ask_router
from app.routers.chat_stream import router as chat_stream_router
from app.routers.chat import router as chat_router
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()
app.add_middleware(CORSMiddleware,
                   allow_origins=["http://localhost:5173","http://127.0.0.1:5173",
                                  "http://localhost:5174","http://127.0.0.1:5174"],
                   allow_credentials=False,
                   allow_methods=["*"],
                   allow_headers=["*"])
app.include_router(semantic_search_router)
app.include_router(ask_router)
app.include_router(chat_stream_router)
app.include_router(chat_router)

@app.exception_handler(DocumentNotFoundError)
def document_not_found_handler(request:Request,exception:DocumentNotFoundError):

    return JSONResponse(status_code=404,content={"detail":"File Not Found"})


@app.exception_handler(UserAlreadyExistsError)
def user_already_exists_handler(request:Request,exc:UserAlreadyExistsError):

    return JSONResponse(status_code=409,content={"detail":"User With This Email Already Exists"})

@app.exception_handler(InvalidCredentialsError)
def invalid_credentials_handler(request:Request,exc:InvalidCredentialsError):

    return JSONResponse(status_code=401,
                        content={"detail":"Invalid email or password"},
                        headers={"WWW-Authenticate":"Bearer"})

@app.exception_handler(InvalidAccessTokenError)
def invalid_access_token_handler(request:Request,exc:InvalidAccessTokenError):
    return JSONResponse(status_code=401,
                        content={"detail":"Invalid or expired access token"},
                        headers={"WWW-Authenticate":"Bearer"})

@app.exception_handler(AdminRequiredError)
def admin_required_handler(request:Request,exc:AdminRequiredError):
    return JSONResponse(status_code=403,content={"detail":"Admin permission required"},)

app.include_router(document_router)
app.include_router(user_router)

@app.get("/")
def root():
    return{
        "message":"Enterprise AI Knowledge Assistant API is running"
    }

@app.exception_handler(UnsupportedFileTypeError)
def unsupported_file_type_handler(request:Request,exc:UnsupportedFileTypeError):
    return JSONResponse(status_code=415,content={"detail":"Unsupported file type"})

@app.exception_handler(EmptyFileError)
def empty_file_handler(request:Request,exc:EmptyFileError):
    return JSONResponse(status_code=400,content={"detail":"File cannot be empty"})

@app.exception_handler(FileTooLargeError)
def file_too_large_handler(request:Request,exc:FileTooLargeError):
    return JSONResponse(status_code=413,content={"detail":"File is too large"})

