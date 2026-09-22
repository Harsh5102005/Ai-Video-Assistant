import yt_dlp
from pydub import AudioSegment

DOWNLOAD_DIR='downloads'
import os 
os.makedirs(DOWNLOAD_DIR,exist_ok=True)
def download_yt_audio(url: str) -> str:
    output_path = os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s")

    ydl_opts = {
        "outtmpl": output_path,
        "quiet": False,
        "noplaylist": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "192",
            }
        ],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        file = ydl.prepare_filename(info)

    file = os.path.splitext(file)[0] + ".wav"

    return file


def convert_to_wav(input_path:str)->str:
    output_path=os.path.splitext(input_path)[0]+"_converted.wav"
    audio=AudioSegment.from_file(input_path)
    audio=audio.set_channels(1).set_frame_rate(16000)
    audio.export(output_path,format="wav")
    return output_path


def chunk_audio(wav_path:str,chunk_minute:int=10)->list:
    audio=AudioSegment.from_wav(wav_path)
    chunk_ms=chunk_minute*60*1000
    chunks=[]
    for i,start in enumerate(range(0,len(audio),chunk_ms)):
        chunk=audio[start:start+chunk_ms]
        chunk_path=f"{wav_path}_chunk{i}.wav"
        chunk.export(chunk_path,format='wav')
        chunks.append(chunk_path)
    return chunks

def process_input(source:str)->list:
    if source.startswith("http://") or source.startswith("https://"):
        print("Detected Youtube URL. Downloading vido")
        wav_path=download_yt_audio(source)
    else:
        print("Deteced Local file. Converting to wav")
        wav_path=convert_to_wav(source)
    print("Chunking Video")
    chunks=chunk_audio(wav_path)
    print(f"Audio Ready = {len(chunks)} chunk(s) created")
    return chunks
