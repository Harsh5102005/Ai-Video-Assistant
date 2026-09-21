from core.transcribe import transcribe_all
from utils.audio_processing import process_input

source="https://youtu.be/AIVajHzjySo?si=d6OQ60ncjrGMd5B_"
chunks=process_input(source)

print(transcribe_all(chunks))