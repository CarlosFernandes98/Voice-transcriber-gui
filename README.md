# Whisper Voice Transcriber GUI 🎙️

Aplicação em Python com interface gráfica para gravar áudio via microfone ou carregar ficheiros, transcrevendo automaticamente a fala para texto utilizando o modelo Whisper da OpenAI.

## Funcionalidades
- Gravação de voz em tempo real enquanto o botão está pressionado
- Upload de ficheiros de áudio (.mp3, .wav, .m4a)
- Transcrição automática com Whisper (versão local, sem API)
- Cronômetro em tempo real durante a gravação
- Seleção de dispositivos de entrada de áudio
- Interface moderna com `customtkinter`

## Tecnologias
- Python 3.10+
- [Whisper (openai-whisper)](https://github.com/openai/whisper)
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)
- sounddevice
- pydub + ffmpeg
- scipy + numpy
