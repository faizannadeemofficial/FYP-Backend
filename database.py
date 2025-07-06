from datetime import datetime
import mysql.connector
from dotenv import load_dotenv
import os

import utils

load_dotenv()


class DatabaseOPS:

    def __init__(self) -> None:
        # Connect to the database
        self.conn = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
        )
        self.cursor = self.conn.cursor()

    def close(self):
        self.cursor.close()
        self.conn.close()

    # 👇🏻 Inserting data in users table 👇🏻
    def inserting_data_in_users(self, username: str, email: str, password: str):
        """
        Inserts a new user into the 'users' table in the database.
        """
        try:
            creation_date = datetime.now().strftime(r"%Y-%m-%d")
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO users (user_name, email_id, user_password, creation_date) VALUES (%s, %s, %s, %s)",
                (username, email, password, creation_date),
            )
            self.conn.commit()
            cursor.close()
            return True
        except Exception as e:
            print(f"Error is: {e}")
            return False

    def get_password(self, email_id: str):
        """
        Retrieves the password for a given email from the 'users' table.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT user_password FROM users WHERE email_id=%s", (email_id,)
            )
            result = cursor.fetchone()
            cursor.close()
            if result:
                return result[0]
            else:
                return None
        except Exception as e:
            print(f"Error is: {e}")
            return e

    def get_user_data(self, email_id: str):
        """
        Retrieves user_id and user_name for a given email.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT user_id, user_name FROM users WHERE email_id=%s", (email_id,)
            )
            result = cursor.fetchone()
            cursor.close()
            if result:
                return result[0], result[1]
            else:
                return None
        except Exception as e:
            print(f"Error is: {e}")
            return e

    def set_tokens(self, email: str, auth_token: str, refresh_token: str):
        """
        Updates the 'auth_token' and 'refresh_token' fields for a user.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "UPDATE users SET auth_token = %s, refresh_token = %s WHERE email_id = %s",
                (auth_token, refresh_token, email),
            )
            self.conn.commit()
            cursor.close()
            return 1
        except Exception as e:
            print(f"Error is: {e}")
            return e

    def logout(self, refresh_token: str):
        """
        Delete auth tokens to logout user.
        """
        decoded_token = utils.verify_token(token=refresh_token)
        user_id = decoded_token["user_id"]
        email = decoded_token["email"]
        user_name = decoded_token["user_name"]

        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "UPDATE users SET auth_token = NULL , refresh_token = NULL where user_id = %s AND email_id = %s AND user_name = %s",
                (user_id, email, user_name),
            )
            self.conn.commit()
            cursor.close()
            return 1
        except Exception as e:
            print(f"Error is: {e}")
            return e

    # 👇🏻 Inserting data in input_contents table 👇🏻
    def insert_input_content(
        self,
        user_id: str,
        content_type: str,
        input_content: str,
        mask_character: str,
        output_content: str,
        project_name: str,
    ):
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO input_contents (user_id, content_type, input_content, mask_character, output_content, modification_date, project_name) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (
                    user_id,
                    content_type,
                    input_content,
                    mask_character,
                    output_content,
                    datetime.now(),
                    project_name,
                ),
            )
            self.conn.commit()
            # Get the last inserted id
            input_content_id = cursor.lastrowid
            cursor.close()
            return input_content_id
        except Exception as e:
            print(f"Error in inserting input content is: {e}")
            return e

    def insert_processed_text(
        self,
        input_content_id: str,
        original_word: str,
        is_flagged: str,
        filtered_word: str,
    ):
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO processed_text (input_content_id, original_word, is_flagged, filtered_word) VALUES (%s, %s, %s, %s)",
                (input_content_id, original_word, is_flagged, filtered_word),
            )
            self.conn.commit()
            cursor.close()
            return 1
        except Exception as e:
            print(f"Error in inserting_processed_text is: {e}")
            return e

    def insert_custom_words(self, input_content_id: str, custom_word: str):
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO custom_words (input_content_id, custom_word) VALUES (%s, %s)",
                (input_content_id, custom_word),
            )
            self.conn.commit()
            cursor.close()
            return 1
        except Exception as e:
            print(f"Error in inserting custom words is: {e}")
            return e

    def insert_processed_audio(
        self,
        input_content_id: str,
        start_time: str,
        end_time: str,
        is_flagged: str,
        original_word: str,
        filtered_word: str,
    ):
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO processed_audio (input_content_id, start_time, end_time, is_flagged, original_word, filtered_word) VALUES (%s, %s, %s, %s, %s, %s)",
                (
                    input_content_id,
                    start_time,
                    end_time,
                    is_flagged,
                    original_word,
                    filtered_word,
                ),
            )
            self.conn.commit()
            cursor.close()
            return 1
        except Exception as e:
            print(f"Error in inserting processed audio is: {e}")
            return e

    def insert_processed_image(
        self,
        input_content_id: str,
        detected_content: str,
        is_flagged: str,
    ):
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO processed_image (input_content_id, detected_content, is_flagged) VALUES (%s, %s, %s)",
                (input_content_id, detected_content, is_flagged),
            )
            self.conn.commit()
            cursor.close()
            return 1
        except Exception as e:
            print(f"Error in inserting processed image is: {e}")
            return e

    def insert_visual_content_features(self, input_content_id, blur_radius, fps):
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO visual_content_features (input_content_id, blur_radius, fps) VALUES (%s, %s, %s)",
                (input_content_id, blur_radius, fps),
            )
            self.conn.commit()
            cursor.close()
            return 1
        except Exception as e:
            print(f"Error in inserting insert_visual_content_features is: {e}")
            return e

    def insert_processed_video_detection(
        self, input_content_id, start_second, end_second
    ):
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO processed_video (input_content_id, start_second, end_second) VALUES (%s, %s, %s)",
                (input_content_id, start_second, end_second),
            )
            self.conn.commit()
            inserted_id = cursor.lastrowid
            cursor.close()
            return inserted_id
        except Exception as e:
            print(f"Error in inserting processed_video_detection is: {e}")
            return e

    def insert_video_content_detections(self, processed_video_id, detected_content):
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO video_content_detections (processed_video_id, detected_content) VALUES (%s, %s)",
                (processed_video_id, detected_content),
            )
            self.conn.commit()
            cursor.close()
            return 1
        except Exception as e:
            print(f"Error in inserting insert_video_content_detections is: {e}")
            return e