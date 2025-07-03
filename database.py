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
            host=os.getenv("DB_HOST"),  # XAMPP uses localhost
            user=os.getenv("DB_USER"),  # default user in XAMPP
            password=os.getenv("DB_PASSWORD"),  # default has no password
            database=os.getenv("DB_NAME"),  # replace with your DB name
        )

        # Create a cursor to interact
        self.cursor = self.conn.cursor()

    # 👇🏻 Inserting data in users table 👇🏻
    def inserting_data_in_users(self, username: str, email: str, password: str):
        """
        Inserts a new user into the 'users' table in the database.

        Args:
            username (str): The username of the new user.
            email (str): The email address of the new user.
            password (str): The hashed password of the new user.

        Returns:
            bool: True if the insertion was successful, False otherwise.
        """
        try:
            creation_date = datetime.now()
            formatted_date = creation_date.strftime(r"%Y-%m-%d")

            self.cursor.execute(
                "INSERT INTO users (user_name, email_id, user_password, creation_date) VALUES (%s, %s, %s, %s)",
                (username, email, password, formatted_date),
            )
            self.conn.commit()
            # Close the connection
            self.cursor.close()
            self.conn.close()
            return True
        except Exception as e:
            # Close the connection
            self.cursor.close()
            self.conn.close()
            print(f"Error is: {e}")
            return False

    def get_password(self, email_id: str):
        """
        Retrieves the password for a given username from the 'users' table.

        Args:
            username (str): The username whose password is to be retrieved.

        Returns:
            str or None: The password if found, None otherwise.
        """
        try:
            self.cursor.execute(
                "SELECT user_password FROM users WHERE email_id=%s", (email_id,)
            )
            result = self.cursor.fetchone()
            if result:
                return result[0]
            else:
                return None
        except Exception as e:
            print(f"Error is: {e}")
            return e

    def get_user_data(self, email_id: str):
        try:
            self.cursor.execute(
                "SELECT user_id, user_name FROM users WHERE email_id=%s", (email_id,)
            )
            result = self.cursor.fetchone()
            if result:
                return result[0], result[1]
            else:
                return None
        except Exception as e:
            print(f"Error is: {e}")
            return e

    def set_tokens(self, email: str, auth_token: str, refresh_token: str):
        """
        Updates the 'auth_token' and 'refresh_token' fields for all users in the 'users' table.

        Args:
            auth_token (str): The authentication token to be set.
            refresh_token (str): The refresh token to be set.

        Returns:
            int: 1 if the update was successful.
            Exception: The exception object if an error occurred.
        """
        try:
            self.cursor.execute(
                "UPDATE users SET auth_token = %s, refresh_token = %s WHERE email_id = %s",
                (auth_token, refresh_token, email),
            )
            self.conn.commit()
            return 1
        except Exception as e:
            print(f"Error is: {e}")
            return e

    def update_tokens(self, refresh_token: str):
        decoded_token = utils.verify_token(refresh_token)
        user_id = decoded_token["user_id"]
        email = decoded_token["email"]
        user_name = decoded_token["user_name"]

        new_auth_token = utils.authentication_token(
            user_id=user_id, user_email=email, user_name=user_name
        )

        new_refresh_token = utils.refresh_token(
            user_id=user_id, user_email=email, user_name=user_name
        )
        return new_auth_token, new_refresh_token

    def logout(self, refresh_token: str):
        "Delete auth tokens to logout user"
        decoded_token = utils.verify_token(token=refresh_token)
        user_id = decoded_token["user_id"]
        email = decoded_token["email"]
        user_name = decoded_token["user_name"]

        try:
            self.cursor.execute(
                "UPDATE users SET auth_token = NULL , refresh_token = NULL where user_id = %s AND email_id = %s AND user_name = %s",
                (user_id, email, user_name),
            )
            self.conn.commit()
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
    ):
        try:
            self.cursor.execute(
                "INSERT INTO input_contents (user_id, content_type, input_content, mask_character, output_content, modification_date) VALUES (%s, %s, %s, %s, %s, %s)",
                (
                    user_id,
                    content_type,
                    input_content,
                    mask_character,
                    output_content,
                    datetime.now(),
                ),
            )
            self.conn.commit()
            input_content_id = None
            try:
                self.cursor.execute(
                    "SELECT input_content_id FROM input_contents WHERE user_id=%s AND content_type=%s AND input_content=%s AND mask_character=%s AND output_content=%s",
                    (
                        user_id,
                        content_type,
                        input_content,
                        mask_character,
                        output_content,
                    ),
                )
                result = self.cursor.fetchone()
                if result:
                    input_content_id = int(result[0])
                    return input_content_id
                else:
                    input_content_id = None
                    return input_content_id

            except Exception as e:
                print(f"Error in fetching input content id is: {e}")
                return e

        except Exception as e:
            print(f"Error in inserting input content is: {e}")

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
            return 1
        except Exception as e:
            print(f"Error in inserting processed text is: {e}")

    def insert_custom_words(self, input_content_id: str, custom_word: str):
        try:
            self.cursor.execute(
                "INSERT INTO custom_words (input_content_id, custom_word) VALUES (%s, %s)",
                (input_content_id, custom_word),
            )
            self.conn.commit()
            return 1
        except Exception as e:
            print(f"Error in inserting custom words is: {e}")

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
                (input_content_id, start_time, end_time, is_flagged, original_word, filtered_word),
            )
            self.conn.commit()
            return 1
        except Exception as e:
            print(f"Error in inserting processed text is: {e}")

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
            return 1
        except Exception as e:
            print(f"Error in inserting processed image is: {e}")

    def insert_visual_content_features (self, input_content_id, blur_radius, fps):
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO visual_content_features (input_content_id, blur_radius, fps) VALUES (%s, %s, %s)",
                (input_content_id, blur_radius, fps),
            )
            self.conn.commit()
            return 1
        except Exception as e:
            print(f"Error in inserting insert_visual_content_features is: {e}")