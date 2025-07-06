from text import TextProfanityFilter
from predict import ProfanityDetectionModel
from faster_whisper import WhisperModel
from pydub import AudioSegment


class AudioProfanityFilter:
    def __init__(self, textpf):
        self.textpf = textpf
        self.tpf = TextProfanityFilter()  # Initializing badwords
        self.pdm = ProfanityDetectionModel()  # Initializing ML model

    def transcribeAndModerate(
        self, audio: str, custom_words: list, mask_char="*", model_size="tiny"
    ) -> list:
        moderated_json = []

        model = WhisperModel(model_size, device="cpu", compute_type="int8")

        segments, _ = model.transcribe(audio=audio, word_timestamps=True)

        for segment in segments:
            for word in segment.words:
                if self.textpf.isGoodWord(word.word.lower()):
                    moderated_json.append(
                        {
                            "OriginalWord": word.word,
                            "IsProfane": False,
                            "FilteredWord": word.word,
                            "Start": word.start,
                            "End": word.end,
                        }
                    )
                # Check if word is profane using ML model or exists in bad words list
                elif self.textpf.predict_text(text=word.word) or self.textpf.isBadWord(
                    word=word.word, custom_words=custom_words
                ):
                    # If profane, mask the word and mark as profane
                    moderated_json.append(
                        {
                            "OriginalWord": word.word,
                            "IsProfane": True,
                            "FilteredWord": len(word.word) * mask_char,
                            "Start": word.start,
                            "End": word.end,
                        }
                    )
                else:
                    # If not profane, keep original word and mark as clean
                    moderated_json.append(
                        {
                            "OriginalWord": word.word,
                            "IsProfane": False,
                            "FilteredWord": word.word,
                            "Start": word.start,
                            "End": word.end,
                        }
                    )
        return moderated_json

    # Run this function
    def audioProfanityFilteration(
        self,
        audio_path: str,
        output_file_name: str,
        mask_char: str,
        custom_words: list,
        beep_path=None,
    ):
        profanity_data = self.transcribeAndModerate(
            audio=audio_path, custom_words=custom_words, mask_char=mask_char
        )
        # Load the main audio
        audio = AudioSegment.from_file(audio_path)

        # Create or load beep sound (default: 500ms tone)
        if beep_path:
            beep = AudioSegment.from_file(beep_path)
        else:
            # Generate 1000Hz beep for 500ms
            from pydub.generators import Sine

            beep = Sine(500).to_audio_segment(duration=500).apply_gain(-5)

        for word in profanity_data:
            if word["IsProfane"]:
                start_ms = int(float(word["Start"]) * 1000)
                end_ms = int(float(word["End"]) * 1000)
                duration = end_ms - start_ms

                # Resize beep to match duration
                adjusted_beep = (
                    beep[:duration]
                    if len(beep) >= duration
                    else beep * (duration // len(beep) + 1)
                )
                adjusted_beep = adjusted_beep[:duration]

                # Replace segment with beep
                audio = audio[:start_ms] + adjusted_beep + audio[end_ms:]

        # Export censored audio
        audio.export("storage/files/" + output_file_name, format="wav")

        return output_file_name, profanity_data
