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

#from google.cloud import vision
from google.cloud import speech
from google.cloud.speech import RecognizeResponse

def detect_labels(uri):
    client = vision.ImageAnnotatorClient()
    image = vision.Image()
    image.source.image_uri = uri

    response = client.label_detection(image=image)
    labels = response.label_annotations
    print("Labels:")

    for label in labels:
        print(label.description)

    if response.error.message:
        raise Exception(
            "{}\nFor more info on error messages, check: "
            "https://cloud.google.com/apis/design/errors".format(response.error.message)
        )

def detect_safe_search(uri):
    """Detects unsafe features in the file."""
    client = vision.ImageAnnotatorClient()
    # with open(path, "rb") as image_file:
    #     content = image_file.read()
    # image = vision.Image(content=content)
    
    image = vision.Image()
    image.source.image_uri = uri

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

def sync_recognize_with_profanity_filter_gcs() -> RecognizeResponse:
    """Recognizes speech from an audio file in Cloud Storage and filters out profane language.
    Args:
        audio_uri (str): The Cloud Storage URI of the input audio, e.g., gs://[BUCKET]/[FILE]
    Returns:
        cloud_speech.RecognizeResponse: The full response object which includes the transcription results.
    """
    # Define the audio source
    print("in sync")
    audio_uri = "gs://media-bd80-448911-64ca/test_frames/w7.mp4"
    audio = {"uri": audio_uri}

    client = speech.SpeechClient()
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.FLAC,  # Audio format
        sample_rate_hertz=16000,
        language_code="en-US",
        # Enable profanity filter
        profanity_filter=True,
    )

    response = client.recognize(config=config, audio=audio)

    for result in response.results:
        alternative = result.alternatives[0]
        print(f"Transcript: {alternative.transcript}")

    return response.results

def main():
    uri = "gs://media-bd80-448911-64ca/test_frames/test1.png"
    # detect_labels(uri)
    # detect_safe_search(uri)

    result = sync_recognize_with_profanity_filter_gcs()
    print(f"Result: {result}")

if __name__ == "__main__":
    main()