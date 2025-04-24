import chainlit as cl
import speech_recognition as sr
from dataclasses import dataclass
import os
from utils import *

# This is where the frontend chainlit part starts............
os.environ["CHAINLIT_AUTH_SECRET"]="my_secret_key"

@dataclass
class UIConfig:
    """Configuration for the Chainlit UI"""
    app_name: str = "JANVI - JIRA AI Assistant"
    theme_color: str = "#1E88E5"  
    support_audio: bool = True
    max_input_length: int = 500
    default_placeholder: str = "Enter your JIRA query here... 💡"

# as we are using welcome messages at the start ..these starters wont matter
@cl.set_starters
async def set_starters():
    return [
        cl.Starter(
            label="Total number of story points assigned to David in Sprint 8",
            message="Total number of story points assigned to David in Sprint 8",
            icon="/public/icon.svg",
            ),

        cl.Starter(
            label="Total number of backlogs assigned Sprint 8",
            message="Total number of backlogs assigned Sprint 8",
            icon="/public/icon.svg",
            ),
        cl.Starter(
            label="Feature readiness for APS board",
            message="How are the quality of features in APS board",
            icon="/public/icon.svg",
            ),
        ]


@cl.on_chat_start
async def start():
    """Initialize the chat interface"""
   
    welcome_message="Please enter yoyur prompt : "
    await cl.Message(
        content=welcome_message,
        author="Assistant"
    ).send() 
     

@cl.step(type="tool")
async def process1(message):
    await process_query(message)

    with open("generated_files/output.txt", "r") as f:
        output_content = f.read()
    try:
        df = pd.read_csv("generated_files/output.csv")
        csv_download = "generated_files/output.csv"
    except FileNotFoundError:
        df = "output.csv not found."
        csv_download = None

    await cl.Message(
        content=f'''We found that...
        {output_content}''',
    ).send()

    await cl.Message(
            content="Here's the processed data:",
            elements=[
                cl.Dataframe(
                    data=df, 
                    display="inline",
                    name="JIRA Data",
                
                )
            ]
            ).send()
    image = cl.Image(path='jira_hygiene_dashboard2.png', name="Jira Hygene", display="inline")
    await cl.Message(
        content="Jira Hygene Dashboard",
        elements=[image],
    ).send()

    return "Process1 completed successfully"

@cl.step(type="tool")
async def speech_to_text(audio_file):
    """Enhanced speech to text processing using Google's speech recognition"""
    # Create a temporary file with a unique name
    temp_file_path = None
    try:
        # Create a temp file that won't be auto-deleted when closed
        with NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_file_path = temp_file.name
            temp_file.write(audio_file[1])
            # Make sure file is written and closed properly
            temp_file.flush()
            os.fsync(temp_file.fileno())
        
        # Initialize the recognizer
        recognizer = sr.Recognizer()
        
        # Now open the fully written file with SpeechRecognition
        with sr.AudioFile(temp_file_path) as source:
            audio_data = recognizer.record(source)
            
            try:
                # Use Google's speech recognition
                text = recognizer.recognize_google(audio_data)
                return text
            except sr.UnknownValueError:
                return "Google Speech Recognition could not understand audio"
            except sr.RequestError as e:
                return f"Could not request results from Google Speech Recognition service; {e}"
    except Exception as e:
        return f"Error processing audio: {str(e)}"
    finally:
        # Clean up the temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except:
                pass  # If we can't delete it now, it will be cleaned up later

@cl.on_audio_start
async def on_audio_start():
    """Initialize audio session variable"""
    
    cl.user_session.set("audio_chunks", [])
    return True

@cl.on_audio_chunk
async def on_audio_chunk(chunk: cl.InputAudioChunk):
    """Process incoming audio chunks"""
    audio_chunks = cl.user_session.get("audio_chunks")

    if audio_chunks is not None:
        audio_chunk = np.frombuffer(chunk.data, dtype=np.int16)
        audio_chunks.append(audio_chunk)
        cl.user_session.set("audio_chunks", audio_chunks)

@cl.on_audio_end
async def on_audio_end():
    """Process the audio chunk when the audio ends"""
    await process_audio()
        
async def process_audio():
    try:
        # Get the audio buffer from the session
        if audio_chunks := cl.user_session.get("audio_chunks"):
            # Concatenate all chunks
            concatenated = np.concatenate(list(audio_chunks))

            # Create an in-memory binary stream
            wav_buffer = io.BytesIO()

            # Create WAV file with proper parameters
            with wave.open(wav_buffer, "wb") as wav_file:
                wav_file.setnchannels(1)  # mono
                wav_file.setsampwidth(2)  # 2 bytes per sample (16-bit)
                wav_file.setframerate(24000)  # sample rate (24kHz PCM)
                wav_file.writeframes(concatenated.tobytes())

            # Reset buffer position
            wav_buffer.seek(0)

            cl.user_session.set("audio_chunks", [])

            audio_buffer = wav_buffer.getvalue()

            input_audio_el = cl.Audio(content=audio_buffer, mime="audio/wav")

            input = ("audio.wav", audio_buffer, "audio/wav")
            transcription = await speech_to_text(input)

            # Store the conversation
            message_history = cl.user_session.get("message_history")
            if not message_history:
                message_history = []
            message_history.append({"role": "user", "content": transcription})
            cl.user_session.set("message_history", message_history)

            # Send the transcribed text
            message = await cl.Message(
                author="You",
                type="user_message",
                content=transcription,
                elements=[input_audio_el],
            ).send()

            res = await cl.AskActionMessage(
                content='''Is our transcription accurate? ✅ If not, feel free to cancel it. ❌ Did you know that reducing unnecessary API calls helps save energy ⚡and lower carbon emissions 🌍? Let's contribute to a greener environment together! 🍃''',
                actions=[
                    cl.Action(name="continue", payload={"value": "continue"}, label="✅ Continue"),
                    cl.Action(name="cancel", payload={"value": "cancel"}, label="❌ Cancel"),
                ],
            ).send()

            if res and res.get("payload").get("value") == "continue":
                await process_message(message)
            else:
                await cl.Message(content="❌ Cancelled. Thank you. Lets create a sustainable environment 🌍 for our future generations").send()
            
    except Exception as e:
        # Handle any exceptions that might occur during processing
        await cl.Message(content=f"Error processing audio: {str(e)}").send()

@cl.action_callback("missing_epic")
async def show_missing_entries1(action: cl.Action):
    data=load_data()

    df= filter_missing(data,"epic_id")
    if(df.empty):
        await cl.Message(content="No missing epic entries found").send()
    else:
        await cl.Message(
            content="Entries missing the epic ID's",
            elements=[
                cl.Dataframe(
                    data=df, 
                    display="inline",
                    name="Missing epic ids",
                )
            ]
            ).send()
       
@cl.action_callback("missing_desc")
async def show_missing_entries2(action: cl.Action):
    data=load_data()
    df= filter_missing(data,"description")
    if(df.empty):
        await cl.Message(content="No missing desciption entries found").send()
    else:
        await cl.Message(
            content="Entries missing the description:",
            elements=[
                cl.Dataframe(
                    data=df, 
                    display="inline",
                    name="Missing Descriptions",
                )
            ]
            ).send()


@cl.action_callback("missing_criteria")
async def show_missing_entries3(action: cl.Action):
    
    data=load_data()

    df= filter_missing(data, "acceptance_criteria")
    if(df.empty):
        await cl.Message(content="No missing acceptance criteria entries found").send()
    else:
        await cl.Message(
            content="Entries missing the acceptance criteria:",
            elements=[
                cl.Dataframe(
                    data=df, 
                    display="inline",
                    name="Missing criteria",
                )
            ]
        ).send()








@cl.on_message
async def process_message(message):
    """Main message processing handler"""
    # Validate input length
    if len(message.content) > 500:
        await cl.Message(
            content=f"⚠️ Input too long. Maximum 500 characters allowed.",
            author="System"
        ).send()

    # if is_jira_related(message):
    #     tool_res = await process1(message)
    # else:
    #     await cl.Message(
    #         content="❌ Not a valid JIRA query.",
    #         author="System"
    #     ).send()

    tool_res = await process1(message.content)

    await cl.Message(
        content="Click to view specific missing entries:",
        actions=[
            cl.Action(name="missing_epic", icon="mouse-pointer-click",payload={"value": "EPIC ?"},label="missing epic ID's"),
            cl.Action(name="missing_desc", icon="mouse-pointer-click",payload={"value": " Description ?"},label="missing description"),
            cl.Action(name="missing_criteria",icon="mouse-pointer-click",payload={"value": "Criteria ?"},label="missing acceptance criteria"),
        ]
    ).send()

   



    
def configure_chainlit_app():
    """Configure Chainlit application settings"""
    cl.App.config(
        name=UIConfig().app_name,
        theme=cl.Theme(
            primary_color=UIConfig().theme_color,
            font_family="Inter, sans-serif"
        ),
        enable_audio=True
    )
if __name__ == "__main__":
    # Make sure the generated_files directory exists
    if not os.path.exists("generated_files"):
        os.makedirs("generated_files")
    configure_chainlit_app()













# eg: if query is about backlog health for sprint 8 or how is backlog looking for sprint 8 for CDF board
# data_to_query: All issues in Sprint 8 for CDF board  
# specific_need: Count of all issues in Sprint 8 for CDF board and RTB and CTB issue counts seperately for CDF board in Sprint 8.


# eg3 if query is total number of backlogs in CDF board in Sprint 8
# data_to_query: All backlogs in CDF board in Sprint 8
# specific_need: Number of backlogs in CDF board in Sprint 8