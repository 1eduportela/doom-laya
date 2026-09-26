"""Graba en video (MP4 con sonido, compatible con WhatsApp) una partida jugada por main().

Uso (desde la raiz del proyecto):   python -m src.herramientas.grabadora
El video se guarda en la carpeta videos/
"""
import os
import shutil
import subprocess
import time
import wave

import cv2
import numpy as np


class Grabadora:
    def __init__(self, ruta, fps=35, escala=2, frecuencia_audio=22050):
        self.ruta = ruta                           # video final (H.264 + AAC)
        self.ruta_video_tmp = ruta + ".tmp.mp4"    # imagen sin sonido (lo que graba OpenCV)
        self.ruta_audio_tmp = ruta + ".tmp.wav"    # sonido sin imagen
        self.fps = fps
        self.escala = escala
        self.video = None          # el video se abre con la primera imagen
        self.fotogramas = 0

        self.frecuencia_audio = frecuencia_audio
        self.muestras_por_tic = frecuencia_audio // fps   # 22050 / 35 = 630
        self.trozos_audio = []     # aqui se van juntando los trozos de sonido

        # Crear la carpeta del video si no existe (por ejemplo "videos/")
        carpeta = os.path.dirname(ruta)
        if carpeta:
            os.makedirs(carpeta, exist_ok=True)

    # ------------------------------------------------------------------ imagen
    def _preparar(self, imagen):
        # ViZDoom puede dar la imagen como (colores, alto, ancho).
        # OpenCV la quiere como (alto, ancho, colores).
        if imagen.ndim == 3 and imagen.shape[0] == 3:
            imagen = np.transpose(imagen, (1, 2, 0))

        # ViZDoom usa el orden de colores RGB; OpenCV, BGR.
        imagen = cv2.cvtColor(imagen, cv2.COLOR_RGB2BGR)

        # Ampliar (320x240 se ve muy pequeno)
        alto, ancho = imagen.shape[:2]
        return cv2.resize(imagen, (ancho * self.escala, alto * self.escala),
                          interpolation=cv2.INTER_NEAREST)

    def agregar(self, imagen, repeticiones=1):
        imagen = self._preparar(imagen)

        # Con la primera imagen ya sabemos el tamano: abrimos el video
        if self.video is None:
            alto, ancho = imagen.shape[:2]
            codec = cv2.VideoWriter_fourcc(*"mp4v")
            self.video = cv2.VideoWriter(self.ruta_video_tmp, codec, self.fps, (ancho, alto))

        # Repetir la imagen tantas veces como tics ha durado la accion
        for _ in range(repeticiones):
            self.video.write(imagen)
        self.fotogramas += repeticiones

    # ------------------------------------------------------------------- audio
    def agregar_audio(self, audio, tics):
        if audio is None:          # el audio no esta activado en el entorno
            return
        # El bufer trae siempre los ultimos 4 tics; nos quedamos con los que duro la accion
        muestras = tics * self.muestras_por_tic
        self.trozos_audio.append(audio[-muestras:])

    def _guardar_wav(self):
        sonido = np.concatenate(self.trozos_audio)   # une todos los trozos en uno
        with wave.open(self.ruta_audio_tmp, "wb") as wav:
            wav.setnchannels(sonido.shape[1])        # 2 = estereo
            wav.setsampwidth(2)                      # 2 bytes por muestra (int16)
            wav.setframerate(self.frecuencia_audio)
            wav.writeframes(sonido.astype(np.int16).tobytes())

    # ------------------------------------------------------------------ cierre
    def cerrar(self):
        if self.video is None:
            return                                   # nunca llego ninguna imagen
        self.video.release()
        segundos = self.fotogramas / self.fps
        con_audio = len(self.trozos_audio) > 0
        if con_audio:
            self._guardar_wav()

        # Sin ffmpeg no se puede convertir ni juntar: nos quedamos con la imagen en mp4v
        if shutil.which("ffmpeg") is None:
            os.replace(self.ruta_video_tmp, self.ruta)
            print(f"Vídeo guardado: {self.ruta} ({segundos:.1f} s, sin sonido)")
            print("  Aviso: instala ffmpeg (sudo apt install ffmpeg) para el sonido y WhatsApp.")
            return

        comando = ["ffmpeg", "-y", "-i", self.ruta_video_tmp]
        if con_audio:
            comando += ["-i", self.ruta_audio_tmp, "-c:a", "aac", "-b:a", "128k"]
        comando += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart", self.ruta]

        resultado = subprocess.run(comando, capture_output=True)
        if resultado.returncode == 0:
            os.remove(self.ruta_video_tmp)
            if con_audio:
                os.remove(self.ruta_audio_tmp)
            sonido = "con sonido" if con_audio else "sin sonido"
            print(f"Vídeo guardado: {self.ruta} ({segundos:.1f} s, {sonido}, compatible con WhatsApp)")
        else:
            os.replace(self.ruta_video_tmp, self.ruta)
            print(f"Vídeo guardado: {self.ruta} ({segundos:.1f} s)")
            print("  Aviso: falló la conversión con ffmpeg; se guarda el vídeo sin convertir.")


if __name__ == "__main__":
    # Solo se ejecuta al lanzar este archivo directamente
    from src.main import main, ESCENARIO

    ruta = f"videos/{ESCENARIO}_{time.strftime('%Y%m%d_%H%M%S')}.mp4"
    grabadora = Grabadora(ruta)
    try:
        main(grabadora=grabadora)
    finally:
        grabadora.cerrar()
