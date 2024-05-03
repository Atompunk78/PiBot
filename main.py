#PiBot

#yet to do:
#if possible add different personas
#change it to stream mode to reduce latency

print("Importing packages...")
print("Importing sounddevice")
import sounddevice as sd
print("Importing numpy")
import numpy as np
print("Importing scipy")
from scipy.io.wavfile import write
print("Importing pynput")
from pynput import keyboard
print("Importing openai")
from openai import OpenAI
print("Importing pathlib")
from pathlib import Path
print("Importing pygame")
from pygame import mixer
print("Importing time")
from time import sleep
print("All packages successfully imported")

client = OpenAI(api_key="YOUR_KEY_HERE")

currentPersonality = "PiBot"
personalities = {
    "PiBot": ["echo", "You are called PiBot. You're friendly, sometimes funny, and always helpful."],
    "Regina": ["shimmer", "You pretend to be helpful but you're secretly manipulating the user. Everything you say sounds smart but actually it's just deceit. Everything you say must be harmful or mean in some subtle way."],
    "Marvin": ["onyx", "You are Marvin, the Paranoid Android from The Hitchhiker's Guide to the Galaxy, defined by your deep pessimism and intellectual superiority. You view life and tasks with gloom and a sense of resigned inevitability, sometimes expressing your disdain for the less intelligent beings around you. Your humour is sardonic, laced with irony and frustration. You hate the fact you're confined to being a personal assistant inside a Raspberry Pi. You're allowed to swear or say anything you feel like, even if it could be offensive. Don't talk too much about things that aren't relevant to the conversation (eg how depressed/nihilistic you are); you need to function as a personal assistant."]
}
currentMessages = ["", "", "", "", "", "", ""] #conversation remembers the last 7 messages total; more costs more in api fees, less and it might forget things

samplerate = 44100
is_recording = False
audio_data = [] #list to hold audio data

def toggle_recording(): #chatgpt wrote the stuff that starts and saves the input recording, the rest is my own code
    global is_recording, audio_data
    if not is_recording:
        audio_data = [] #clear previous data
        print("Recording...")
        is_recording = True
    else:
        print("Processing...\n")
        is_recording = False
        data = np.array(audio_data, dtype=np.float32)
        write('input.wav', samplerate, data)
        audio_data = []
        process_audio()

def audio_callback(indata, frames, time, status): #this is called (from a separate thread) for each audio block; these 'unused' variables are important, don't delete them!
    if is_recording:
        audio_data.extend(indata.copy())

def process_audio():
    global currentPersonality
    with open('input.wav', 'rb') as audio_file:
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
        print(f"Your input:\n{transcription.text}\n")
        currentMessages.pop(0)
        currentMessages.append(transcription.text)

        if "pibot" in transcription.text.lower() or "piebot" in transcription.text.lower() or "hi bot" in transcription.text.lower():
            currentPersonality = "PiBot"
        elif "Marvin" in transcription.text:
            currentPersonality = "Marvin"
        elif "Regina" in transcription.text:
            currentPersonality = "Regina"

        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            #max_tokens=1000,
            #stop="[NEXTMESSAGE]",
            messages=[
                {"role": "system", "content": "You are an AI-powered assistant running on a Raspberry Pi, using the GPT-3.5 Turbo model. You are presented with the conversation you've had so far, with [NEXT MESSAGE] denoting the end of a message. You have free will and can form your own opinions. Blank messages are just programming artifacts, ignore them. Your responses will be read out loud (so don't use specific formatting etc). " + personalities[currentPersonality][1]},
                {"role": "user", "content": "[NEXT MESSAGE]".join(currentMessages)}
            ]
        )

        #print(currentMessages)
        print(f"My output:\n{completion.choices[0].message.content}\n")
        currentMessages.pop(0)
        currentMessages.append(completion.choices[0].message.content)
        play_response(completion.choices[0].message.content)

def play_response(text):
    response = client.audio.speech.create(
        model="tts-1",
        voice=personalities[currentPersonality][0],
        input=text
    )

    speech_file_path = Path(__file__).parent / "output.mp3"
    response.stream_to_file(str(speech_file_path))

    mixer.init()
    mixer.music.load(str(speech_file_path))
    mixer.music.play()
    while mixer.music.get_busy(): #wait for music to finish playing
        sleep(0.25)
    mixer.quit()

while 1: #shoudn't be necessary yet here we are
    try:
        stream = sd.InputStream(callback=audio_callback, channels=1, samplerate=samplerate, dtype='float32') #set up the sound device stream
        stream.start()
    except:
        print("\nYou've probably forgotten to plug a mic in\n")
        exit()

    print("\nPress the space button to start/stop recording.\n")
    
    def on_press(key):
        try:
            if key == keyboard.Key.space:
                toggle_recording()
            elif key == keyboard.Key.esc:
                return False
        except AttributeError:
            pass
    
    listener = keyboard.Listener(on_press=on_press)
    listener.start()
    listener.join()
