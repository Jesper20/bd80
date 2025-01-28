#!/usr/bin/python
#
# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os, subprocess, time
from google.cloud import vision
from google.cloud import speech
# from google.cloud.speech import RecognizeResponse, LongRunningRecognizeResponse
# from google.cloud.speech_v2 import SpeechClient
# from google.cloud.speech_v2.types import cloud_speech

# from google.cloud import videointelligence
from google.cloud import storage

import cv2
import csv
import numpy as np
# import urllib.request as req
# from decord import VideoReader
# from decord import cpu
# import firebase_admin
# from firebase_admin import credentials
# from firebase_admin import storage
import datetime
#from oauth2client.service_account import ServiceAccountCredentials
from moviepy import VideoFileClip

# Function to extract first 15 frames from a video
def extract_frames(video_path, frame_count=15):
    print(f"Extract frames {video_path}")
    cap = cv2.VideoCapture(video_path)
    frames = []
    count = 0
    while len(frames) < frame_count:
        success, frame = cap.read()
        if not success:
            print("Error!")
            break
        # else:
        #     print("Success!")
        count += 1
        if count % FRAME_INTERVAL == 0:
            #frame_path = os.path.join(TEMP_FRAME_FOLDER, f"{os.path.basename(video_path)}_frame_{frame_idx}.jpg")
            frame_path = os.path.join(TEMP_FRAME_FOLDER,f"frame_{count}.jpg")
            cv2.imwrite(frame_path, frame)
            frames.append(frame_path)
    cap.release()
    # # Path to video file 
    # vidObj = cv2.VideoCapture(video_path) 
  
    # # Used as counter variable 
    # frame_idx = 0
    # # checks whether frames were extracted 
    # success = 1
    # while success: 
    #     frame_idx += 1
    #     print(frame_idx)
    #     # vidObj object calls read 
    #     # function extract frames 
    #     success, frame = vidObj.read() 
  
    #     # Saves the frames with frame-count 
    #     frame_path = os.path.join(TEMP_FRAME_FOLDER,f"frame_{frame_idx}.jpg")
    #     cv2.imwrite(frame_path, frame)
    return frames

# def extract_frames_decord(video_path, frames_dir, overwrite=False, start=-1, end=-1, every=1):
#     """
#     Extract frames from a video using decord's VideoReader
#     :param video_path: path of the video
#     :param frames_dir: the directory to save the frames
#     :param overwrite: to overwrite frames that already exist?
#     :param start: start frame
#     :param end: end frame
#     :param every: frame spacing
#     :return: count of images saved
#     """

#     # load the VideoReader
#     vr = VideoReader(video_path, ctx=cpu(0))  # can set to cpu or gpu .. ctx=gpu(0)
                     
#     if start < 0:  # if start isn't specified lets assume 0
#         start = 0
#     if end < 0:  # if end isn't specified assume the end of the video
#         end = len(vr)

#     frames_list = list(range(start, end, every))
#     saved_count = 0

#     if every > 25 and len(frames_list) < 1000:  # this is faster for every > 25 frames and can fit in memory
#         frames = vr.get_batch(frames_list).asnumpy()

#         for index, frame in zip(frames_list, frames):  # lets loop through the frames until the end
#             save_path = os.path.join(frames_dir, video_filename, "{:010d}.jpg".format(index))  # create the save path
#             if not os.path.exists(save_path) or overwrite:  # if it doesn't exist or we want to overwrite anyways
#                 cv2.imwrite(save_path, cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))  # save the extracted image
#                 saved_count += 1  # increment our counter by one

#     else:  # this is faster for every <25 and consumes small memory
#         for index in range(start, end):  # lets loop through the frames until the end
#             frame = vr[index]  # read an image from the capture
            
#             if index % every == 0:  # if this is a frame we want to write out based on the 'every' argument
#                 save_path = os.path.join(frames_dir, video_filename, "{:010d}.jpg".format(index))  # create the save path
#                 if not os.path.exists(save_path) or overwrite:  # if it doesn't exist or we want to overwrite anyways
#                     cv2.imwrite(save_path, cv2.cvtColor(frame.asnumpy(), cv2.COLOR_RGB2BGR))  # save the extracted image
#                     saved_count += 1  # increment our counter by one

#     return saved_count  # and return the count of the images we saved

# def detect_labels(uri):
#     client = vision.ImageAnnotatorClient()
#     image = vision.Image()
#     image.source.image_uri = uri

#     response = client.label_detection(image=image)
#     labels = response.label_annotations
#     print("Labels:")

#     for label in labels:
#         print(label.description)

#     if response.error.message:
#         raise Exception(
#             "{}\nFor more info on error messages, check: "
#             "https://cloud.google.com/apis/design/errors".format(response.error.message)
#         )

def detect_safe_search(uri):
    """Detects unsafe features in the file."""
    client = vision.ImageAnnotatorClient()
    with open(uri, "rb") as image_file:
        content = image_file.read()
        image = vision.Image(content=content)
    
    #image = vision.Image()
    #image.source.image_uri = uri

    response = client.safe_search_detection(image=image)
    safe = response.safe_search_annotation

    # Names of likelihood from google.cloud.vision.enums
    likelihood_name = (
        "UNKNOWN",
        "VERY_UNLIKELY",
        "UNLIKELY",
        "POSSIBLE",
        "LIKELY",
        "VERY_LIKELY",
    )
    print("Safe search:")

    print(f"adult: {likelihood_name[safe.adult]}")
    # print(f"medical: {likelihood_name[safe.medical]}")
    # print(f"spoofed: {likelihood_name[safe.spoof]}")
    print(f"violence: {likelihood_name[safe.violence]}")
    # print(f"racy: {likelihood_name[safe.racy]}")

    if response.error.message:
        raise Exception(
            "{}\nFor more info on error messages, check: "
            "https://cloud.google.com/apis/design/errors".format(response.error.message)
        )

# def sync_recognize_with_profanity_filter_gcs() -> RecognizeResponse:
#     """Recognizes speech from an audio file in Cloud Storage and filters out profane language.
#     Args:
#         audio_uri (str): The Cloud Storage URI of the input audio, e.g., gs://[BUCKET]/[FILE]
#     Returns:
#         cloud_speech.RecognizeResponse: The full response object which includes the transcription results.
#     """
#     # Define the audio source
#     print("in sync")
#     audio_uri = "gs://media-bd80-448911-64ca/test_frames/w7.mp4"
#     audio = {"uri": audio_uri}

#     client = speech.SpeechClient()
#     config = speech.RecognitionConfig(
#         encoding=speech.RecognitionConfig.AudioEncoding.FLAC,  # Audio format
#         sample_rate_hertz=16000,
#         language_code="en-US",
#         # Enable profanity filter
#         profanity_filter=True,
#     )

#     response = client.recognize(config=config, audio=audio)

#     for result in response.results:
#         alternative = result.alternatives[0]
#         print(f"Transcript: {alternative.transcript}")

#     return response.results

# def transcribe_profanity_filter_v2(
#     audio_file: str,
# ) -> cloud_speech.RecognizeResponse:
#     """Transcribe an audio file with profanity filtering enabled.
#     Args:
#         audio_file (str): Path to the local audio file to be transcribed.
#             Example: "resources/audio.wav"
#     Returns:
#         cloud_speech.RecognizeResponse: The response containing the transcription results.
#     """
#     # Instantiates a client
#     client = SpeechClient()

#     # Reads a file as bytes
#     with open(audio_file, "rb") as f:
#         audio_content = f.read()

#     config = cloud_speech.RecognitionConfig(
#         auto_decoding_config=cloud_speech.AutoDetectDecodingConfig(),
#         language_codes=["en-US"],
#         model="long",
#         features=cloud_speech.RecognitionFeatures(
#             profanity_filter=True,  # Enable profanity filtering
#         ),
#     )
#     request = cloud_speech.RecognizeRequest(
#         #recognizer=f"projects/{PROJECT_ID}/locations/global/recognizers/_",
#         config=config,
#         content=audio_content,
#     )
#     # Transcribes the audio into text
#     response = client.recognize(request=request)

#     for result in response.results:
#         print(f"Transcript: {result.alternatives[0].transcript}")

#     return response

# def detect_profanity(uri):
#     """Recognizes speech from an audio file in Cloud Storage and filters out profane language.
#     Args:
#         audio_uri (str): The Cloud Storage URI of the input audio, e.g., gs://[BUCKET]/[FILE]
#     Returns:
#         cloud_speech.RecognizeResponse: The full response object which includes the transcription results.
#     """
#     # Define the audio source
#     # Reads a file as bytes
#     with open(uri, "rb") as f:
#         audio = f.read()
#     # if GCS URI is used
#     # audio_uri = uri
#     # audio = {"uri": audio_uri}
    
#     client = speech.SpeechClient()
  
#     config = speech.RecognitionConfig(
#         encoding=speech.RecognitionConfig.AudioEncoding.FLAC,  # Audio format
#         sample_rate_hertz=16000,
#         language_code="en-US",
#         # Enable profanity filter
#         profanity_filter=True,
#     )
#     response = client.recognize(config=config, audio=audio)
#     # for result in response.results:
#     #     alternative = result.alternatives[0]
#     #     print(f"Transcript: {alternative.transcript}")
#     # return response.results
  
#     # Check for birthday wishes and profanity
#     transcripts = [result.alternatives[0].transcript for result in response.results]

#     result =  {
#         'transcripts': transcripts,
#         'has_birthday_wishes': any('happy birthday' in text.lower() for text in transcripts),
#         'contains_profanity': any('xxx' in text() for text in transcripts)  # Profanity filter is enabled in the API config
#     }
#     return result

# def transcribe_gcs(uri):
#     """Asynchronously transcribes the audio file from Cloud Storage
#     Args:
#         gcs_uri: The Google Cloud Storage path to an audio file.
#             E.g., "gs://storage-bucket/file.flac".
#     Returns:
#         The generated transcript from the audio file provided.
#     """
#     client = speech.SpeechClient()

#     audio = speech.RecognitionAudio(uri=uri)
#     config = speech.RecognitionConfig(
#         encoding=speech.RecognitionConfig.AudioEncoding.FLAC,
#         sample_rate_hertz=44100,
#         language_code="en-US",
#         #language_code="my-MM",
#         # Enable profanity filter
#         profanity_filter=True,
#     )
#     operation = client.long_running_recognize(config=config, audio=audio)

#     print("Waiting for operation to complete...")
#     response = operation.result(timeout=180)

#     # Check for birthday wishes and profanity
#     transcripts = [result.alternatives[0].transcript for result in response.results]

#     result =  {
#         'transcripts': transcripts,
#         'has_birthday_wishes': any('happy birthday' in text.lower() for text in transcripts),
#         'contains_profanity': any('***' in text.lower() for text in transcripts) 
#     }
#     return result

# def analyze_frames_for_nudity(uri):
#     """ Extracts frames and checks for nudity using Google Cloud Vision API. """
#     frame_dir = "./frames"
#     os.makedirs(frame_dir, exist_ok=True)
#     subprocess.run(["ffmpeg", "-i", uri, "-vf", "fps=1", os.path.join(frame_dir, "frame_%04d.jpg")], check=True)
#     frames = sorted(os.listdir(frame_dir))
    
#     # nudity_count = 0
#     # for frame in frames:
#     #     frame_path = os.path.join(frame_dir, frame)
#     #     with open(frame_path, "rb") as frame_file:
#     #         content = frame_file.read()
        
#     #     image = Image(content=content)
#     #     response = vision_client.safe_search_detection(image=image)
#     #     annotation = response.safe_search_annotation
#     #     if annotation.adult >= Likelihood.LIKELY:
#     #         nudity_count += 1
#     #     if nudity_count >= 2:
#     #         break
    
#     # return nudity_count < 2, nudity_count
#     return frames

# def video_intelligence(uri):
#     video_client = videointelligence.VideoIntelligenceServiceClient()
#     features = [videointelligence.Feature.SPEECH_TRANSCRIPTION, 
#                     videointelligence.Feature.EXPLICIT_CONTENT_DETECTION]

#     config = videointelligence.SpeechTranscriptionConfig(
#         language_code="en-US", enable_automatic_punctuation=True
#     )
#     video_context = videointelligence.VideoContext(speech_transcription_config=config)

#     operation = video_client.annotate_video(
#         request={
#             "features": features,
#             "input_uri": uri,
#             "video_context": video_context,
#         }
#     )

#     print("\nProcessing video for speech transcription and explicit content detection.")
#     result = operation.result(timeout=180)
#     print("\nFinished processing.")

#     # Retrieve first result because a single video was processed
#     annotation_results = result.annotation_results[0]
#     for frame in annotation_results.explicit_annotation.frames:
#         likelihood = videointelligence.Likelihood(frame.pornography_likelihood)
#         frame_time = frame.time_offset.seconds + frame.time_offset.microseconds / 1e6
#         print("Time: {}s".format(frame_time))
#         print("\tpornography: {}".format(likelihood.name))

#     for speech_transcription in annotation_results.speech_transcriptions:
#         # The number of alternatives for each transcription is limited by
#         # SpeechTranscriptionConfig.max_alternatives.
#         # Each alternative is a different possible transcription
#         # and has its own confidence score.
#         for alternative in speech_transcription.alternatives:
#             print("Alternative level information:")

#             print("Transcript: {}".format(alternative.transcript))
#             print("Confidence: {}\n".format(alternative.confidence))

#             print("Word level information:")
#             for word_info in alternative.words:
#                 word = word_info.word
#                 start_time = word_info.start_time
#                 end_time = word_info.end_time
#                 print(
#                     "\t{}s - {}s: {}".format(
#                         start_time.seconds + start_time.microseconds * 1e-6,
#                         end_time.seconds + end_time.microseconds * 1e-6,
#                         word,
#                     )
#                 )


def download_blob(bucket_name, source_blob_name, destination_file_name):
    """Downloads a blob from the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    
    blob = bucket.blob(source_blob_name)
    with open(destination_file_name, "wb") as file_obj:
        blob.download_to_file(file_obj)

# def generate_image_url(blob_path):
#     """ generate signed URL of a video stored on google storage. 
#         Valid for 300 seconds in this case. You can increase this 
#         time as per your requirement. 
#     """       
#     #keyfile = "./avocano_api/service-account.json"
#     #keyfile = "./avocano_api/firebasekey.json"
#     #credentials = ServiceAccountCredentials.from_json_keyfile_name(keyfile)
#     #url = blob.generate_signed_url(expiration, method="GET",credentials=credentials) 

#     bucket_name = "media-bd80-448911-64ca" #bucket name
#     source_blob_name = "test_frames/w7.mp4" # "path/file in Google Cloud Storage bucket"
#     destination_file_name = "/tmp/temp"#(without extension, for example in my case ".mp4")"

#     storage_client = storage.Client()
#     bucket = storage_client.bucket(bucket_name)                                                 
#     blob = bucket.blob(blob_path) 
#     #return blob.generate_signed_url(datetime.timedelta(seconds=300), method='GET', credentials=credentials)
#     return blob.generate_signed_url(datetime.timedelta(seconds=300), method='GET')

# def test(uri):
#     url = generate_image_url(uri)
#     req.urlretrieve(url, uri)
#     cap = cv2.VideoCapture(uri)

#     if cap.isOpened():
#         print ("File Can be Opened")
#         while(True):
#             # Capture frame-by-frame
#             ret, frame = cap.read()
#             #print cap.isOpened(), ret
#             if frame is not None:
#                 # Display the resulting frame
#                 cv2.imshow('frame',frame)
#                 # Press q to close the video windows before it ends if you want
#                 if cv2.waitKey(22) & 0xFF == ord('q'):
#                     break
#             else:
#                 print("Frame is None")
#                 break
#         # When everything done, release the capture
#         cap.release()
#         cv2.destroyAllWindows()
#         print ("Video stop")
#     else:
#         print("Not Working")

def extract_audio(video_path, source_blob_name):
    # Define the input video file and output audio file
    nm = source_blob_name[source_blob_name.rfind("/")+1: source_blob_name.rfind(".")]
    audio_path = os.path.join(TEMP_FRAME_FOLDER,f"{nm}_audio.wav")

    # Load the video clip
    video_clip = VideoFileClip(video_path)

    # Extract the audio from the video clip
    audio_clip = video_clip.audio

    # Write the audio to a separate file
    audio_clip.write_audiofile(audio_path)

    # Close the video and audio clips
    audio_clip.close()
    video_clip.close()
    print("Audio extraction successful!")
    return audio_path

def analyze_audio_yn(audio_path):
    with open(audio_path, "rb") as audio_file:
        content = audio_file.read()
        
    client = speech.SpeechClient()
    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        #encoding=speech.RecognitionConfig.AudioEncoding.FLAC,
        #sample_rate_hertz=16000,
        language_code="en-US",
        audio_channel_count = 2,
        enable_word_time_offsets=True,
        profanity_filter=True
    )
    
    response = client.recognize(config=config, audio=audio)
    has_happy_birthday = False
    contains_swear_words = False
    
    for result in response.results:
        transcript = result.alternatives[0].transcript
        if "Happy Birthday" in transcript[:30]:
            has_happy_birthday = True
        if config.profanity_filter and "****" in transcript:
            contains_swear_words = True

    return {"has_happy_birthday": has_happy_birthday, "contain_swear_words": contains_swear_words}

def main():
    #setting Google credential
    #os.environ['GOOGLE_APPLICATION_CREDENTIALS']= 'google_secret_key.json'
    bucket_name = "media-bd80-448911-64ca" #bucket name
    source_blob_name = "test_frames/happybirthday.mp4" # "path/file in Google Cloud Storage bucket"
    #bucket_name = "https://console.cloud.google.com/storage/browser/media-bd80-448911-64ca"
    local_video_path = "/tmp/temp"#(without extension, for example in my case ".mp4")"

    # img_uri = "gs://media-bd80-448911-64ca/test_frames/test1.png"
    # video_uri = "gs://media-bd80-448911-64ca/test_frames/swear.mp4"
    # video_uri = "gs://media-bd80-448911-64ca/test_frames/2.mp4"
    #video_uri = "gs://media-bd80-448911-64ca/test_frames/w7.mp4"
    # video_uri = "gs://media-bd80-448911-64ca/test_frames/happybirthday.mp4"
    # detect_labels(uri)
    # detect_safe_search(img_uri)
    #result = sync_recognize_with_profanity_filter_gcs(video_uri)

    # result = detect_profanity(video_uri)
    # result = transcribe_gcs(video_uri)
    # print(result)
    # video_intelligence(video_uri)

    #frames =  analyze_frames_for_nudity(video_uri)
    # print(f"Detect explicit content: {result}")

    
    #frames = extract_frames_decord(video_uri, TEMP_FRAME_FOLDER)
    #test(video_uri)
    download_blob(bucket_name, source_blob_name, local_video_path)
    frames = extract_frames(local_video_path)
    for frame in frames:
        detect_safe_search(frame)

    local_audio_path = extract_audio(local_video_path, source_blob_name)
    #result = detect_profanity(local_audio_path)
    #result = transcribe_profanity_filter_v2(local_audio_path)
    result = analyze_audio_yn(local_audio_path)
    print(result)

    # Clean up temporary video, audio, frames
    os.remove(local_audio_path)
    os.remove(local_video_path)
    for frame in frames:
        os.remove(frame)
    
    
if __name__ == "__main__":
    # speech_client = speech.SpeechClient()
    # vision_client = vision.ImageAnnotatorClient()
    FRAME_INTERVAL = 2
    VIDEO_FOLDER = "./testing_"
    TEMP_FRAME_FOLDER = "./temp_frames"
    OUTPUT_FOLDER = "video_reports"
    os.makedirs(TEMP_FRAME_FOLDER, exist_ok=True)
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    # cred = credentials.Certificate('Path\to\your\google-credential-file.json')
    # app = firebase_admin.initialize_app(cred, {'storageBucket': 'cnc-designs.appspot.com'}, name='storage')
    # bucket = storage.bucket(app=app)
    # bucket_name = "media-bd80-448911-64ca" #bucket name
    # source_blob_name = "test_frames/w7.mp4" # "path/file in Google Cloud Storage bucket"
    # destination_file_name = "/tmp/temp"#(without extension, for example in my case ".mp4")"

    # storage_client = storage.Client()
    # bucket = storage_client.bucket(bucket_name)

    main()