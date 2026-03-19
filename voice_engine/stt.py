"""
Speech-to-Text (STT) Module using Whisper.

M1 Mac Cihazları İçin En İyi Deneyim: mlx-whisper
------------------------------------------------
Apple Silicon (M1/M2/M3) işlemcilerde inanılmaz hızlı ve verimli çalışması için
Apple'ın kendi makine öğrenimi kütüphanesi olan MLX tabanlı `mlx-whisper` kullanılması tavsiye edilir.

Kurulum:
pip install mlx-whisper

Örnek Kullanım:
"""

class WhisperSTT:
    def __init__(self, model_path="mlx-community/whisper-base-mlx"):
        self.model_path = model_path
        # Model ilk kullanımda otomatik indirilir (base model, tiny'den daha iyi, turbo'dan daha hafiftir)
    
    def transcribe(self, audio_file_path: str) -> str:
        """
        Verilen ses dosyasını metne çevirir.
        """
        try:
            import mlx_whisper
        except ImportError:
            raise ImportError("mlx-whisper kütüphanesi eksik. Lütfen 'pip install mlx-whisper' komutunu çalıştırın.")
        
        print(f"[{audio_file_path}] işleniyor...")
        result = mlx_whisper.transcribe(audio_file_path, path_or_hf_repo=self.model_path)
        return result["text"]

# # Örnek test kodu:
# if __name__ == "__main__":
#     stt = WhisperSTT()
#     text = stt.transcribe("test_audio.wav")
#     print("Çıktı:", text)
