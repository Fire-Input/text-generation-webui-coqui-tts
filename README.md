# coqui_tts
Text-to-speech extension for oobabooga's text-generation-webui using Coqui.

## How to install
Assuming you already have the webui set up:

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