# Coqui TTS
Text-to-speech extension for [Oobabooga's text-generation-webui](https://github.com/oobabooga/text-generation-webui) using [Coqui TTS](https://github.com/coqui-ai/TTS).

## Installation
Assuming you already have the WebUI set up:

1. Install [eSpeak-NG](https://github.com/espeak-ng/espeak-ng/releases) and ensure it is in your PATH
2. Activate the conda environment with the `cmd_xxx.bat` or using `conda activate textgen`
3. Enter the  `text-generation-webui/extensions/` directory and clone this repository
```
cd text-generation-webui/extensions/
git clone https://github.com/Fire-Input/text-generation-webui-coqui-tts coqui_tts
```
4. install the requirements
```
pip install -r extensions/coqui_tts/requirements.txt
```

## Notes
- The `coqui_tts` extension will automatically download the pretrained model `tts_models/en/vctk/vits` by default. It is less than 200MB in size, and will be downloaded to `\home\USER\.local\share\tts` for Linux and `C:\Users\USER\AppData\Local\tts` for Windows.
- When running oobabooga, the `tts` package (version `TTS==0.17.4`) may throw an error about `numpy` if you are using python < `3.11`, try `pip install numpy==1.24.4` and `pip install numba==0.57.1` to install the most compatible version of `numpy` and `numba` for this version. Ignore any error messages about incompatible package versions as the `tts` package needs to update its `requirements.txt` to later versions of `numpy` and `numba` and restart the WebUI.
- Custom models are not supported yet.
- Everytime you generate a new audio, Coqui will print out a log message to the console. This is normal and unfortunately cannot be disabled.
- Audio files are saved to `text-generation-webui/extensions/coqui_tts/outputs/`
- A lot of the code is copied from the [ElevenLabs extension](https://github.com/oobabooga/text-generation-webui/tree/main/extensions/elevenlabs_tts).
- And some code copied from [da3dsoul's fork](https://github.com/da3dsoul/text-generation-webui/tree/main/extensions/coqui_tts).
- I do not have a Coqui Studio API key, so I cannot test it. Therefore, it is not supported yet.

## Testing Environment
- Windows 11
- Conda Installation with WSL2
- WSL2 Ubuntu 22.04
- Python 3.9.16
- numpy==1.21.6
- Conda 23.3.1
- CUDA 11.7
- WebUI commit: 68dcbc7ebda3f0d9700dde43d0d29324f5c244b1
- eSpeak-NG 1.50