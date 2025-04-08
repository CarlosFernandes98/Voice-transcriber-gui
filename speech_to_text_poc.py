import customtkinter as ctk
from tkinter import filedialog
import whisper
import threading
import sounddevice as sd
from scipy.io.wavfile import write
from pydub import AudioSegment
import os
import numpy as np

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.recording = False
        self.gravacao = None
        self.fs = 44100
        self.stream = None
        self.tempo_gravacao = 0
        self.timer_label = ctk.CTkLabel(self, text="Tempo de gravação: 0.0 s", font=("Arial", 12))
        self.timer_label.pack(pady=5)
        self.timer_loop_id = None


        self.title("POC - Speech to Text com Whisper")
        self.geometry("700x500")

        # self.modelo = whisper.load_model("small") modelo mais leve
        # self.modelo = whisper.load_model("base") modelo mais leve
        self.modelo = whisper.load_model("large")

        self.caminho_audio = ""

        self.label = ctk.CTkLabel(self, text="Selecione ou grave um áudio", font=("Arial", 18))
        self.label.pack(pady=10)

        self.label = ctk.CTkLabel(self, text="Selecionar dispositivo de audio", font=("Arial", 10))
        self.label.pack(pady=0)
        # Lista de dispositivos de entrada
        self.devices = self.listar_dispositivos_de_entrada()
        self.device_names = [d['name'] for d in self.devices]
        self.selected_device_index = ctk.StringVar(value=self.device_names[0] if self.device_names else "Nenhum")

        self.dropdown_dispositivos = ctk.CTkOptionMenu(self, values=self.device_names, variable=self.selected_device_index)
        self.dropdown_dispositivos.pack(pady=5)

        self.label = ctk.CTkLabel(self, text="Carregar audio", font=("Arial", 10))
        self.label.pack(pady=0)
        self.botao_selecionar = ctk.CTkButton(self, text="Carregar ficheiro de Áudio", command=self.selecionar_audio)
        self.botao_selecionar.pack(pady=5)

                
        self.label = ctk.CTkLabel(self, text="Gravar enquanto pressiona", font=("Arial", 10))
        self.label.pack(pady=0)

        self.botao_gravar = ctk.CTkButton(self, text="🎙️ Pressione para Gravar")
        self.botao_gravar.pack(pady=5)
        self.botao_gravar.bind("<ButtonPress>", self.iniciar_gravacao)
        self.botao_gravar.bind("<ButtonRelease>", self.parar_gravacao)

        self.label = ctk.CTkLabel(self, text="Fazer transcrição", font=("Arial", 10))
        self.label.pack(pady=0)
        
        self.botao_transcrever = ctk.CTkButton(self, text="Transcrever ficheiro", command=self.iniciar_transcricao)
        self.botao_transcrever.pack(pady=5)

        self.textbox_resultado = ctk.CTkTextbox(self, width=600, height=300)
        self.textbox_resultado.pack(pady=20)

    def listar_dispositivos_de_entrada(self):
        dispositivos = sd.query_devices()
        return [d for d in dispositivos if d['max_input_channels'] > 0]

    def get_device_index(self, device_name):
        for i, d in enumerate(self.devices):
            if d["name"] == device_name:
                return sd.default.device[0] if d == sd.default.device[0] else d["index"]
        return None

    def selecionar_audio(self):
        caminho = filedialog.askopenfilename(filetypes=[("Áudios", "*.mp3 *.wav *.m4a")])
        if caminho:
            self.caminho_audio = caminho
            self.label.configure(text=f"Áudio selecionado: {os.path.basename(caminho)}")

    
    def atualizar_cronometro(self):
        if self.recording:
            self.tempo_gravacao += 0.1
            self.timer_label.configure(text=f"Tempo: {self.tempo_gravacao:.1f} s")
            self.timer_loop_id = self.after(100, self.atualizar_cronometro)


    def iniciar_gravacao(self, event=None):
        self.textbox_resultado.delete("1.0", "end")
        self.textbox_resultado.insert("end", "🎙️ A Gravar... Solte o botão para parar.\n")
        self.update()

        self.frames = []
        self.recording = True
        device_name = self.selected_device_index.get()
        device_index = self.get_device_index(device_name)

        if device_index is None:
            self.textbox_resultado.insert("end", "Erro: Dispositivo de entrada inválido.\n")
            return

        def audio_callback(indata, frames, time, status):
            if status:
                print(f"Status: {status}")
            if self.recording:
                self.frames.append(indata.copy())

        try:
            self.stream = sd.InputStream(
                samplerate=self.fs,
                channels=1,
                callback=audio_callback,
                device=device_index
            )
            self.stream.start()
            self.tempo_gravacao = 0
            self.atualizar_cronometro()
        except Exception as e:
            self.textbox_resultado.insert("end", f"Erro ao iniciar gravação: {str(e)}\n")

    def parar_gravacao(self, event=None):
        if not self.recording:
            return
        self.recording = False
        if self.timer_loop_id:
            self.after_cancel(self.timer_loop_id)
            self.timer_loop_id = None
        try:
            self.stream.stop()
            self.stream.close()

            audio_array = np.concatenate(self.frames, axis=0)

            # Guarda como WAV temporário
            wav_temp = "temp_gravacao.wav"
            write(wav_temp, self.fs, audio_array)

            # Converte para MP3
            os.makedirs("audios", exist_ok=True)
            mp3_output = "audios/gravacao_microfone.mp3"
            audio = AudioSegment.from_wav(wav_temp)
            audio.export(mp3_output, format="mp3")
            os.remove(wav_temp)

            self.caminho_audio = mp3_output
            self.label.configure(text=f"Áudio gravado: {mp3_output}")
            self.textbox_resultado.insert("end", "✅ Gravação finalizada.\n")
            self.transcrever_audio()
            

        except Exception as e:
            self.textbox_resultado.insert("end", f"Erro ao finalizar gravação: {str(e)}\n")
            
    def iniciar_transcricao(self):
        if self.caminho_audio:
            self.textbox_resultado.insert("end", "A transcrever, aguarde...\n")
            threading.Thread(target=self.transcrever_audio).start()
        else:
            self.textbox_resultado.insert("end", "Por favor, carregue ou grave um áudio primeiro.\n")

    def transcrever_audio(self):
        try:
            # resultado = self.modelo.transcribe(self.caminho_audio) //sem passar a linguagem
            resultado = self.modelo.transcribe(self.caminho_audio, language="pt")
            texto = resultado["text"]
            self.textbox_resultado.insert("end", f"\n--- Transcrição ---\n{texto}\n")
        except Exception as e:
            self.textbox_resultado.insert("end", f"Erro na transcrição: {str(e)}\n")

if __name__ == "__main__":
    app = App()
    app.mainloop()
