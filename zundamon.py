import requests
import json
import os
import pyaudio
import sounddevice as sd # recording
import soundfile as sf   # save mp3
import keyboard          # rec trigger
import datetime          # save filename
from openai import OpenAI

client = OpenAI()

def vvox_test(text):
    params = (
        ('text', text),
        ('speaker', 3),
    )

    query = requests.post(
        f'http://localhost:50021/audio_query',
        params=params
    )
    
    # 音声合成
    synthesis = requests.post(
        f'http://localhost:50021/synthesis',
        headers = {"Content-Type": "application/json"},
        params = params,
        data = json.dumps(query.json())
    )
    
    # 再生処理
    voice = synthesis.content
    pya = pyaudio.PyAudio()
    
    # サンプリングレートが24000以外だとずんだもんが高音になったり低音になったりする
    stream = pya.open(format=pyaudio.paInt16,
                      channels=1,
                      rate=24000,
                      output=True)
    
    stream.write(voice)
    stream.stop_stream()
    stream.close()
    pya.terminate()
    
while True:
    if keyboard.is_pressed("shift"): # right shift key
        print("5 sec start recording...")

        fs = 44100  # sample rate
        duration = 5  # record sec

        myrecording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
        sd.wait()  # wait while recording
        print("finished recording...")

        now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9), 'JST'))

        fn = "./"+now.strftime('%Y%m%d_%H%M%S')+".mp3"
        sf.write(fn, myrecording, fs)

        # テキスト変換
        audio_file = open(fn, "rb")
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
        print(transcription.text)

        # チャット
        completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "名前が「ずんだもん」で、一人称が「僕」で、口癖は「なのだ」です。枝豆から生まれたキャラクターです"},
            {"role": "user", "content": transcription.text}
        ]
        )

        text = completion.choices[0].message.content
        print(text)
        # 発話
        vvox_test(text)
