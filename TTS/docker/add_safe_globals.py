import torch.serialization
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import XttsAudioConfig

# Add both XttsConfig and XttsAudioConfig to the list of safe globals
torch.serialization.add_safe_globals([XttsConfig, XttsAudioConfig])
print("Added XttsConfig and XttsAudioConfig to PyTorch safe globals")