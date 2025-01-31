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

from google.cloud import vision, speech, storage
from google.cloud.speech import RecognizeResponse
#from oauth2client.service_account import ServiceAccountCredentials

from decimal import Decimal

from colorfield.fields import ColorField
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

import os, csv, re
import numpy as np
import datetime
import cv2
from moviepy import VideoFileClip

# newly added class
class Video(models.Model):
    title = models.CharField(max_length=255)
    video = models.FileField(upload_to="videos/")  # Google Cloud Storage will handle this path
    uploaded_at = models.DateTimeField(auto_now_add=True)


class Product(models.Model):
    # video
    # TODO: need to handle max file size
    video = models.FileField(upload_to="uploads", null=True)
    
    name = models.CharField(max_length=64, unique=True)
    image = models.ImageField(upload_to="photos", blank=True, null=True)
    description = models.CharField(max_length=1000)
    price = models.DecimalField(decimal_places=2, max_digits=10)
    active = models.BooleanField()
    discount_percent = models.IntegerField()
    inventory_count = models.IntegerField()
    product_we_love = models.BooleanField(default=False)

    @property
    def discount_saving(self):
        return Decimal(round(float(self.price) * (self.discount_percent / 100), 2))

    @property
    def discount_price(self):
        return "{0:.2f}".format(self.price - self.discount_saving)

    def __str__(self):
        return self.name

    ## If product is active, set all other products as inactive
    def save(self, *args, **kwargs):
        if self.active:
            qs = type(self).objects.filter(active=True)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            qs.update(active=False)

        super(Product, self).save(*args, **kwargs)

    def detect_safe_search(self, frames, threshold=2):
        result = { "violations_detected" : False, "violation_count": 0, "violations": []  }
        for frame in frames:
            violation = {'frame': frame, 'adult': False, 'violence': False}
            """Detects unsafe features in the file."""
            client = vision.ImageAnnotatorClient()
            with open(frame, "rb") as image_file:
                content = image_file.read()
                image = vision.Image(content=content)
            # image = vision.Image()
            # image.source.image_uri = uri
            # new_path = self.image.name
            # image.source.image_uri = new_path
            # image.source.image_uri = "gs://media-bd80-448911-64ca/test_frames/test1.png"

            response = client.safe_search_detection(image=image)
            safe = response.safe_search_annotation

            # Names of likelihood from google.cloud.vision.enums
            likelihood_name = ("UNKNOWN","VERY_UNLIKELY","UNLIKELY","POSSIBLE","LIKELY","VERY_LIKELY")
            # print("Safe search:")
            # print(f"adult: {likelihood_name[safe.adult]}")
            # print(f"medical: {likelihood_name[safe.medical]}")
            # print(f"spoofed: {likelihood_name[safe.spoof]}")
            # print(f"violence: {likelihood_name[safe.violence]}")
            # print(f"racy: {likelihood_name[safe.racy]}")

            if response.error.message:
                raise Exception(
                    "{}\nFor more info on error messages, check: "
                    "https://cloud.google.com/apis/design/errors".format(response.error.message)
                )
            else:
                if likelihood_name[safe.adult] == "LIKELY" or likelihood_name[safe.adult] == "VERY LIKELY":
                    result["violation_count"] += 1
                    violation['adult'] = True 
                if likelihood_name[safe.violence] == "LIKELY" or likelihood_name[safe.violence] == "VERY LIKELY":
                    result["violation_count"] += 1
                    violation['violence'] = True 
            result["violations"].append(violation)
            if result["violation_count"] >= threshold:
                print("Detected unsafe content!!!")
                result["violations_detected"] = True
                break

        return result

    def detect_profanity_bdmsg(self,audio_path):
        has_happy_birthday = False
        contains_swear_words = False
        searchMsg = "happy birthday"

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
        
        for result in response.results:
            transcript = result.alternatives[0].transcript
            transcript = transcript.lower()
            # search for msg 'happy birthday' in transcript
            if re.search(searchMsg, transcript) != None:
                has_happy_birthday = True
            if config.profanity_filter and "****" in transcript:
                contains_swear_words = True

        return {"has_happy_birthday": has_happy_birthday, "contain_swear_words": contains_swear_words}

    # Function to download video in Google Bucket to a local temp folder for processing
    def download_blob(self, bucket_name, source_blob_name, destination_file_name):
        """Downloads a blob from the bucket."""
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        
        blob = bucket.blob(source_blob_name)
        with open(destination_file_name, "wb") as file_obj:
            blob.download_to_file(file_obj)

    # Function to extract first 15 frames from a video
    def extract_frames(self, video_path, TEMP_FRAME_FOLDER, frame_interval=3, max_frame=15):
        print(f"Extract frames {video_path}")
        cap = cv2.VideoCapture(video_path)
        frames = []
        count = 0
        while len(frames) < max_frame:
            success, frame = cap.read()
            if not success:
                print("Error!")
                break
            # else:
            #     print("Success!")
            count += 1
            if count % frame_interval == 0:
                frame_path = os.path.join(TEMP_FRAME_FOLDER,f"frame_{count}.jpg")
                cv2.imwrite(frame_path, frame)
                frames.append(frame_path)
        cap.release()
        return frames
    
    # Function to extract audio (.wav) from video
    def extract_audio(self,video_path, nm, TEMP_FRAME_FOLDER):
        # Define the input video file and output audio file
        name = nm[nm.find("/")+1:]
        audio_path = os.path.join(TEMP_FRAME_FOLDER,f"{name}_audio.wav")

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

    def analysis2(self, video_path):
        outcome = False
        check_video = True
        check_audio = True
        frames = []
        #setting Google credential
        #os.environ['GOOGLE_APPLICATION_CREDENTIALS']= 'google_secret_key.json'
        # initialize
        violation_threshold = 2
        max_frame = 15
    
        TEMP_FRAME_FOLDER = "./temp_frames"
        OUTPUT_FOLDER = "video_reports"
        local_video_path = "/tmp/temp" # without extension ".mp4"
        os.makedirs(TEMP_FRAME_FOLDER, exist_ok=True)
        os.makedirs(OUTPUT_FOLDER, exist_ok=True)

        # bucket_name = "media-bd80-448911-64ca" #bucket name
        # source_blob_name = "test_frames/happybirthday.mp4" # "path/file in Google Cloud Storage bucket"
        # source_blob_name = "test_frames/swear.mp4"
        # video_name = source_blob_name[source_blob_name.rfind("/")+1: source_blob_name.rfind(".")]
        video_name = video_path[video_path.rfind("/")+1 : ]
        # video_path = os.path.join(f"/home/sharlwinkhin/bd80/server/",video_path)
        video_path = f"/home/sharlwinkhin/bd80/server/{video_path}"
        if check_video:
            frame_interval = 3
            print(f"Extract frames {video_path}")
            cap = cv2.VideoCapture(video_path)
            frames = []
            count = 0
            while len(frames) < max_frame:
                success, frame = cap.read()
                if not success:
                    print("Error!")
                    break
                # else:
                #     print("Success!")
                count += 1
                if count % frame_interval == 0:
                    frame_path = os.path.join(TEMP_FRAME_FOLDER,f"frame_{count}.jpg")
                    cv2.imwrite(frame_path, frame)
                    frames.append(frame_path)
            cap.release()

            result2 = self.detect_safe_search(frames)
            print(result2)
            if result2["violations_detected"]:
                print("Video violations detected")
        if check_audio:
            #local_audio_path = self.extract_audio(video_path, video_name, TEMP_FRAME_FOLDER)
           
            local_audio_path = os.path.join(TEMP_FRAME_FOLDER,f"{video_name}_audio.wav")

            # Load the video clip
            video_clip = VideoFileClip(video_path)

            # Extract the audio from the video clip
            audio_clip = video_clip.audio

            # Write the audio to a separate file
            audio_clip.write_audiofile(local_audio_path)

            # Close the video and audio clips
            audio_clip.close()
            video_clip.close()
            print("Audio extraction successful!")

            result1 = self.detect_profanity_bdmsg(local_audio_path)
            print(result1)

        # analyze audio
        # self.download_blob(bucket_name, source_blob_name, local_video_path)
        #local_audio_path = self.extract_audio(video_path, video_name, TEMP_FRAME_FOLDER)
        #result1 = self.detect_profanity_bdmsg(local_audio_path)
        # print(result1)
       
        # if result1["has_happy_birthday"] and not result1["contain_swear_words"]:
        #     # analyze video
        #     frames = self.extract_frames(video_path, TEMP_FRAME_FOLDER)
        #     result2 = self.detect_safe_search(frames)
        #     print(result2)
        #     if result2["violations_detected"]:
        #         print("Video violations detected")
        
        # else:
        #     print("Audio violations detected")
        # Clean up temporary video, audio, frames
        # os.remove(local_audio_path)
        # os.remove(local_video_path)
        if frames != []:
            for frame in frames:
                os.remove(frame)

 
    # def detect_safe_search_not_use(self):
    #     """Detects unsafe features in the file."""
    #     print("safe search")
    #     client = vision.ImageAnnotatorClient()
    #     image = vision.Image()

    #     # new_path = self.image.name

    #     #image.source.image_uri = new_path
    #     image.source.image_uri = "gs://media-bd80-448911-64ca/test_frames/test1.png"
    #     print(image.source.image_uri)
    #     response = client.safe_search_detection(image=image)
    #     safe = response.safe_search_annotation

    #     # Names of likelihood from google.cloud.vision.enums
    #     likelihood_name = (
    #         "UNKNOWN",
    #         "VERY_UNLIKELY",
    #         "UNLIKELY",
    #         "POSSIBLE",
    #         "LIKELY",
    #         "VERY_LIKELY",
    #     )
    #     print("Safe search:")

    #     print(f"adult: {likelihood_name[safe.adult]}")
    #     print(f"violence: {likelihood_name[safe.violence]}")
    #     # print(f"racy: {likelihood_name[safe.racy]}")

    #     if response.error.message:
    #         raise Exception(
    #             "{}\nFor more info on error messages, check: "
    #             "https://cloud.google.com/apis/design/errors".format(response.error.message)
    #         )

    # def sync_recognize_with_profanity_filter_gcs_not_use(self, uri) -> RecognizeResponse:
    #     """Recognizes speech from an audio file in Cloud Storage and filters out profane language.
    #     Args:
    #         audio_uri (str): The Cloud Storage URI of the input audio, e.g., gs://[BUCKET]/[FILE]
    #     Returns:
    #         cloud_speech.RecognizeResponse: The full response object which includes the transcription results.
    #     """
    #     # Define the audio source
    #     #audio_uri = uri
    #     #audio = {"uri": audio_uri}
    #     # client = speech.SpeechClient()
    #     # config = speech.RecognitionConfig(
    #     #     encoding=speech.RecognitionConfig.AudioEncoding.FLAC,  # Audio format
    #     #     sample_rate_hertz=16000,
    #     #     language_code="en-US",
    #     #     # Enable profanity filter
    #     #     profanity_filter=True,
    #     # )
    #     # response = client.recognize(config=config, audio=audio)
    #     # for result in response.results:
    #     #     alternative = result.alternatives[0]
    #     #     print(f"Transcript: {alternative.transcript}")
    #     # return response.results

    #     with open(uri, "rb") as audio_file:
    #         content = audio_file.read()

    #     audio = speech_v1p1beta1.RecognitionAudio(content=content)
    
    #     # Set sample_rate_hertz to 16000 to match the WAV header
    #     config = speech_v1p1beta1.RecognitionConfig(
    #         encoding=speech_v1p1beta1.RecognitionConfig.AudioEncoding.LINEAR16,
    #         sample_rate_hertz=16000,  # Use 16000 Hz sample rate
    #         language_code="en-US",
    #         profanity_filter=True,
    #         enable_word_confidence=True
    #     )
        
    #     response = speech_client.recognize(config=config, audio=audio)
        
    #     # Check for birthday wishes and profanity
    #     transcripts = [result.alternatives[0].transcript for result in response.results]

    #     result =  {
    #         'transcripts': transcripts,
    #         'has_birthday_wishes': any('happy birthday' in text.lower() for text in transcripts),
    #         'contains_profanity': False  # Profanity filter is enabled in the API config
    #     }

    #     print(result)

    #     return result

    #  def sync_recognize_with_profanity_filter_gcs_not_use(self, uri) -> RecognizeResponse:
    #     """Recognizes speech from an audio file in Cloud Storage and filters out profane language.
    #     Args:
    #         audio_uri (str): The Cloud Storage URI of the input audio, e.g., gs://[BUCKET]/[FILE]
    #     Returns:
    #         cloud_speech.RecognizeResponse: The full response object which includes the transcription results.
    #     """
    #     # Define the audio source
    #     #audio_uri = uri
    #     #audio = {"uri": audio_uri}
    #     # client = speech.SpeechClient()
    #     # config = speech.RecognitionConfig(
    #     #     encoding=speech.RecognitionConfig.AudioEncoding.FLAC,  # Audio format
    #     #     sample_rate_hertz=16000,
    #     #     language_code="en-US",
    #     #     # Enable profanity filter
    #     #     profanity_filter=True,
    #     # )
    #     # response = client.recognize(config=config, audio=audio)
    #     # for result in response.results:
    #     #     alternative = result.alternatives[0]
    #     #     print(f"Transcript: {alternative.transcript}")
    #     # return response.results

    #     with open(uri, "rb") as audio_file:
    #         content = audio_file.read()

    #     audio = speech_v1p1beta1.RecognitionAudio(content=content)
    
    #     # Set sample_rate_hertz to 16000 to match the WAV header
    #     config = speech_v1p1beta1.RecognitionConfig(
    #         encoding=speech_v1p1beta1.RecognitionConfig.AudioEncoding.LINEAR16,
    #         sample_rate_hertz=16000,  # Use 16000 Hz sample rate
    #         language_code="en-US",
    #         profanity_filter=True,
    #         enable_word_confidence=True
    #     )
        
    #     response = speech_client.recognize(config=config, audio=audio)
        
    #     # Check for birthday wishes and profanity
    #     transcripts = [result.alternatives[0].transcript for result in response.results]

    #     result =  {
    #         'transcripts': transcripts,
    #         'has_birthday_wishes': any('happy birthday' in text.lower() for text in transcripts),
    #         'contains_profanity': False  # Profanity filter is enabled in the API config
    #     }

    #     print(result)

    #     return result

    def analysis(self):
        outcome = False
        #setting Google credential
        #os.environ['GOOGLE_APPLICATION_CREDENTIALS']= 'google_secret_key.json'
        # initialize
        violation_threshold = 2
        max_frame = 15
    
        TEMP_FRAME_FOLDER = "./temp_frames"
        OUTPUT_FOLDER = "video_reports"
        local_video_path = "/tmp/temp" # without extension ".mp4"
        os.makedirs(TEMP_FRAME_FOLDER, exist_ok=True)
        os.makedirs(OUTPUT_FOLDER, exist_ok=True)

        bucket_name = "media-bd80-448911-64ca" #bucket name
        source_blob_name = "test_frames/happybirthday.mp4" # "path/file in Google Cloud Storage bucket"
        # source_blob_name = "test_frames/swear.mp4"
        video_name = source_blob_name[source_blob_name.rfind("/")+1: source_blob_name.rfind(".")]

        # analyze audio
        self.download_blob(bucket_name, source_blob_name, local_video_path)
        local_audio_path = self.extract_audio(local_video_path, video_name, TEMP_FRAME_FOLDER)
        result1 = self.detect_profanity_bdmsg(local_audio_path)
        print(result1)
        frames = []
        if result1["has_happy_birthday"] and not result1["contain_swear_words"]:
            # analyze video
            frames = self.extract_frames(local_video_path, TEMP_FRAME_FOLDER)
            result2 = self.detect_safe_search(frames)
            print(result2)
            if result2["violations_detected"]:
                print("Video violations detected")
        
        else:
            print("Audio violations detected")
        # Clean up temporary video, audio, frames
        os.remove(local_audio_path)
        os.remove(local_video_path)
        if frames != []:
            for frame in frames:
                os.remove(frame)

 
class Testimonial(models.Model):
    product_id = models.ForeignKey(Product, on_delete=models.CASCADE)
    reviewer_name = models.CharField(max_length=64)
    reviewer_location = models.CharField(max_length=100)
    rating = models.IntegerField(
        default=5, validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    summary = models.CharField(max_length=1000)
    description = models.CharField(max_length=5000)

    def __str__(self):
        return f"{self.rating} star review on {self.product_id.name} from {self.reviewer_name}"


class Transaction(models.Model):
    datetime = models.DateTimeField()
    product_id = models.ForeignKey(Product, on_delete=models.CASCADE)
    unit_price = models.DecimalField(decimal_places=2, max_digits=10)

    def __str__(self):
        return f"{self.datetime} - {self.product_id}"


def google_font_help():
    return "Any valid <a href='https://fonts.google.com/' target='_blank'>Google Font name</a>. Dynamically loaded at runtime."


class SiteConfig(models.Model):
    active = models.BooleanField(default=True)
    color_primary = ColorField(
        default="#C200C2", help_text="For the site banner gradient"
    )
    color_secondary = ColorField(default="#BE0000", help_text="For headings")
    color_action = ColorField(default="#00AFAF", help_text="Fill for buttons")
    color_action_text = ColorField(default="#000000", help_text="Text for buttons")
    site_name = models.CharField(max_length=200, default="Simulatum")
    site_name_color = ColorField(default="#0D8645")
    site_name_font = models.CharField(
        max_length=100, default="Pacifico", help_text=google_font_help()
    )
    base_font = models.CharField(
        max_length=100, default="Tahoma", help_text=google_font_help()
    )

    def __str__(self):
        return f"{self.site_name} configuration"

    ## Only allow one active SiteConfig
    def save(self, *args, **kwargs):
        if self.active:
            qs = type(self).objects.filter(active=True)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            qs.update(active=False)

        super(SiteConfig, self).save(*args, **kwargs)
