import whisper
import os 


_model=None

def load_model():
    global _model
    if _model is None:
        print("Loading model")
        _model=whisper.load_model("base", device="cuda")
        print("whisper model loaded successfully")
    return _model


def transcribe_chunk(chunk:str,translate:bool=False)->str:
    model=load_model()

    task="translate" if translate else "transcribe"
    result=model.transcribe(chunk,task=task)
    return result['text']

def transcribe_all(chunks:list,translate:bool=False)->str:
    full_transcript=""
    for i, chunk in enumerate(chunks):
        print(f"Transcribing {i+1} chunk")
        data=transcribe_chunk(chunk,translate=translate)
        full_transcript+=data+" "
    return full_transcript




