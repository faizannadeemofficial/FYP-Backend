import time
from moviepy import VideoFileClip
import os

from image import ImageProfanityFilter
from audio import AudioProfanityFilter
from text import TextProfanityFilter


class VideoProfanityDetection:
    def __init__(
        self, input_video: str, custom_words: list = [], mask_char: str = "🤬"
    ):
        # Initialize profanity filters for text, image, and audio
        self.text = TextProfanityFilter()
        self.image = ImageProfanityFilter()
        self.audio = AudioProfanityFilter(textpf=self.text)

        # Store input video path, mask character and custom_words for profanity detection
        self.input_video = input_video
        self.mask_character = mask_char
        self.custom_words = custom_words

    def extract_audio(self, input_video: str) -> str:
        """
        Extracts audio from the given video file and saves it as an mp3 file.
        Returns the path to the saved audio file.
        """
        try:
            video = VideoFileClip(input_video)  # Load the video file
            audio = video.audio  # Extract the audio track
            audio_output_path = (
                f"storage/audio/{str(int(time.time()))}.mp3"  # Generate output path
            )
            audio.write_audiofile(audio_output_path)  # Save audio to file
            audio.close()  # Release audio resources
            video.close()  # Release video resources
            return audio_output_path  # Return path to saved audio
        except Exception as e:
            print(f"An error occurred: {str(e)}")

    def middle_frame(self):
        """
        Extracts the middle frame of every second of the video and saves them in
        storage/imgs/{timestamp}/ with the filename as the second number (e.g., 0.jpg, 1.jpg, ...).
        Returns a list of file paths for the extracted frames.
        """
        timestamp = str(int(time.time()))  # Unique directory for this extraction
        output_dir = f"storage/imgs/{timestamp}"
        os.makedirs(output_dir, exist_ok=True)  # Ensure output directory exists

        video = VideoFileClip(self.input_video)  # Load the video
        duration = int(video.duration)  # Get video duration in seconds

        frame_paths = []
        for sec in range(duration):
            t = sec + 0.5  # Middle of the current second
            if t > video.duration:
                t = video.duration
            frame = video.get_frame(t)  # Extract frame at time t
            frame_path = os.path.join(output_dir, f"{sec}.jpg")  # Output path for frame
            import imageio

            imageio.imwrite(frame_path, frame)  # Save frame as image
            frame_paths.append(frame_path)  # Collect frame path

        video.close()  # Release video resources
        return frame_paths  # Return list of frame paths

    def blur_and_audio(self, blur_seconds: list, audio_path: str):
        """
        Blurs the specified seconds of the video and overlays the provided audio.
        Returns the output video path.
        Uses ffmpeg via subprocess for processing.
        """
        import subprocess

        input_video = self.input_video
        output_path = f"storage/output/{int(time.time())}.mp4"  # Output video path

        # Build ffmpeg filter for selective blur using boxblur
        blur_exprs = []
        for sec in blur_seconds:
            blur_exprs.append(f"between(t,{sec},{sec+1})")
        if blur_exprs:
            enable_expr = "+".join(blur_exprs)
            vf = f"boxblur=lr=6:lp=6:cr=6:cp=6:enable='{enable_expr}'"
            vf_arg = ["-vf", vf]
        else:
            vf_arg = []

        # Construct ffmpeg command for video and audio processing
        cmd = [
            "ffmpeg",
            "-y",  # Overwrite output file if exists
            "-i",
            input_video,
            "-i",
            audio_path,
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            *vf_arg,
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            "-shortest",
            output_path,
        ]

        # Execute ffmpeg command and handle errors
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            print(f"ffmpeg failed: {e}")
            return None

        return output_path  # Return path to processed video

    def video_moderation(self, blur_video: bool):
        """
        Main moderation pipeline:
        - Extracts audio from video and applies audio profanity filtering.
        - Extracts middle frames for each second and applies image profanity detection.
        - Blurs video segments where image profanity is detected (if blur_video is True).
        - Combines moderated audio and video, and returns moderation data.
        """
        # Extract audio from the input video
        audio_path = self.extract_audio(input_video=self.input_video)

        # Apply audio profanity filtering and get filtered audio and text moderation data
        moderated_audio_output_path, text_profanity_data = (
            self.audio.audioProfanityFilteration(
                audio_path=audio_path,
                output_path=f"storage/audio/{str(int(time.time()))}.mp3",
                mask_char=self.mask_character,
                custom_words=self.custom_words,
            )
        )

        # Extract middle frames for each second of the video
        middle_frame_paths = self.middle_frame()

        image_detection_data = []  # Store image moderation results
        seconds_to_blur = []  # Store seconds to blur in video
        for i, frame_path in enumerate(middle_frame_paths):
            data = self.image.detect(frame_path)  # Detect profanity in frame
            if data["isFlagged"] and blur_video:
                data["second"] = i
                image_detection_data.append(data)
                seconds_to_blur.append(i)  # Mark second for blurring
            else:
                data["second"] = i
                image_detection_data.append(data)

        # Apply blur to flagged seconds and combine with moderated audio
        final_moderated_output = self.blur_and_audio(
            blur_seconds=seconds_to_blur, audio_path=moderated_audio_output_path
        )

        # Prepare final moderation data dictionary
        final_data = {
            "moderated_video_path": final_moderated_output,
            "text_moderated_data": text_profanity_data,
            "image_detections": image_detection_data,
        }

        return final_data  # Return moderation results
