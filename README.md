# transcribe-tools

Set of python scripts and GitHub Actions workflow to automate video transcrib batch job

## Updating videos.json

Extract `*.flac` audio from video using following ffmpeg command
```bash
ffmpeg -y -i input.mp4 -ac 1 output.flac
```

Then upload the flace file on Google cloud storage bucket for audio file input.
Add audio and transcribe info in `include` array in `videos.json` 

- `input`: Name of audio file
- `from`: Audio source language code (e.g. ko, en, zh, zh-CN, zh-TW)
- `to`: Destination languages with comma seperated value. (e.g. `ko,zh` for translating into Korean and Chinese)

```json
{
    "include": [
        {
            "input": "audio_file_name.flac", 
            "from": "ko",
            "to": "en"
        },
        ...
    ]
}
```

Commit and push update, Github Action will run subtitle batch job

## Credits
- [GoogleCloudPlatform/community](https://github.com/GoogleCloudPlatform/community)