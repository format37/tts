# NeMo
Docker server, receives text over http post request  
And responses with audio/wav data  
### Installation
```
git clone https://github.com/format37/tts.git
cd tts/nemo/
```
### Settings
It available to define used models in docker-compose.yml:
* SPECTROGRAM_GENERATOR  
Available values: ["tacotron2", "fastpitch", "mixertts", "mixerttsx", None]  
* AUDIO_GENERATOR
Available values: ["waveglow", "hifigan", "univnet", "griffin-lim", None]
### Build
```
sudo docker-compose up --build -d
```
### Using
[nemo.ipynb](https://github.com/format37/client/nemo.ipynb)
### Example
```
SPECTROGRAM_GENERATOR=tacotron2
AUDIO_GENERATOR=waveglow
```
Text:  
```
Hello! Is it a test message? Thank you.
```
[audio.wav](https://github.com/format37/client/audio.wav)
### Based on
[NVIDIA NeMo](https://github.com/NVIDIA/NeMo)