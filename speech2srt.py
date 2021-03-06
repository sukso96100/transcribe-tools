# -*- coding: utf-8 -*-
#
# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from google.cloud.storage import blob
import srt
import time
from google.cloud import speech, storage


def long_running_recognize(args):
    """
    Transcribe long audio file from Cloud Storage using asynchronous speech
    recognition

    Args:
      storage_uri URI for audio file in GCS, e.g. gs://[BUCKET]/[FILE]
    """

    print("Transcribing {} ...".format(args.storage_uri))
    client = speech.SpeechClient()

    # Encoding of audio data sent.
    encoding = speech.RecognitionConfig.AudioEncoding.ENCODING_UNSPECIFIED
    config = {
        "enable_word_time_offsets": True,
        "enable_automatic_punctuation": True,
        "sample_rate_hertz": args.sample_rate_hertz,
        "language_code": args.language_code,
        "encoding": encoding,
    }
    audio = {"uri": args.storage_uri}

    operation = client.long_running_recognize(
        request={
            "config": config,
            "audio": audio,
            }
    )
    response = operation.result()

    subs = []

    for result in response.results:
        # First alternative is the most probable result
        subs = break_sentences(args, subs, result.alternatives[0])

    print("Transcribing finished")
    return subs


def break_sentences(args, subs, alternative):
    firstword = True
    charcount = 0
    idx = len(subs) + 1
    content = ""

    for w in alternative.words:
        if firstword:
            # first word in sentence, record start time
            start_hhmmss = time.strftime('%H:%M:%S', time.gmtime(
                w.start_time.seconds))
            start_ms = int(w.start_time.microseconds / 1000)
            start = start_hhmmss + "," + str(start_ms)

        charcount += len(w.word)
        content += " " + w.word.strip()

        if ("." in w.word or "!" in w.word or "?" in w.word or
                charcount > args.max_chars or
                ("," in w.word and not firstword)):
            # break sentence at: . ! ? or line length exceeded
            # also break if , and not first word
            end_hhmmss = time.strftime('%H:%M:%S', time.gmtime(
                w.end_time.seconds))
            end_ms = int(w.end_time.microseconds / 1000)
            end = end_hhmmss + "," + str(end_ms)
            subs.append(srt.Subtitle(index=idx,
                        start=srt.srt_timestamp_to_timedelta(start),
                        end=srt.srt_timestamp_to_timedelta(end),
                        content=srt.make_legal_content(content)))
            firstword = True
            idx += 1
            content = ""
            charcount = 0
        else:
            firstword = False
    return subs


def write_srt(args, subs):
    srt_file = args.out_file + ".srt"
    print("Writing {} subtitles to: {}".format(args.language_code, srt_file))
    content = srt.compose(subs)
    # f = open(srt_file, 'w')
    # f.writelines(srt.compose(subs))
    # f.close()
    return content


def write_txt(args, subs):
    txt_file = args.out_file + ".txt"
    print("Writing text to: {}".format(txt_file))
    content = ""
    # f = open(txt_file, 'w')
    for s in subs:
        # f.write(s.content.strip() + "\n")
        content += s.content.strip() + "\n"
    # f.close()
    return content

def upload_to_bucket(content, bucket_obj, dest_filename):
    blob = bucket_obj.blob(dest_filename)
    blob.upload_from_string(content)


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--storage_uri",
        type=str,
        default="gs://cloud-samples-data/speech/brooklyn_bridge.raw",
    )
    parser.add_argument(
        "--language_code",
        type=str,
        default="en-US",
    )
    parser.add_argument(
        "--sample_rate_hertz",
        type=int,
        default=44100,
    )
    parser.add_argument(
        "--out_file",
        type=str,
        default="en",
    )
    parser.add_argument(
        "--out_storage",
        type=str,
        default="gs://cloud-samples-data/speech/brooklyn_bridge.raw",
    )
    parser.add_argument(
        "--max_chars",
        type=int,
        default=40,
    )
    args = parser.parse_args()

    input_filename = args.storage_uri.split("/")[-1]
    out_srt = "{}/{}.{}".format(input_filename, args.language_code, "srt")
    out_txt = "{}/{}.{}".format(input_filename, args.language_code, "txt")

    storage_client = storage.Client()
    bucket = storage_client.bucket(args.out_storage)
    if((not bucket.blob(out_srt).exists()) and (not bucket.blob(out_txt).exists())):

        subs = long_running_recognize(args)
        srt_str = write_srt(args, subs)
        txt_str = write_txt(args, subs)
        
        upload_to_bucket(srt_str, bucket, out_srt)
        upload_to_bucket(txt_str, bucket, out_txt)
    else:
        print("Skipped batch speech to text job as output path is not empty")


if __name__ == "__main__":
    main()
