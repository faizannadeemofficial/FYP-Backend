create table users
(
    user_id     bigint          primary key,
    user_name   varchar(200),
    email_id    varchar(200),
    user_password varchar(200),
    auth_token  varchar(4000),
    refresh_token varchar(4000),
    creation_date   date
)

create table input_contents
(
    input_content_id    bigint      primary key,
    user_id             bigint      references      users(user_id),
    content_type        varchar(20),  -- TEXT, AUDIO, VIDEO , IMAGE
    input_content       varchar(4000),
    mask_character      varchar(50),             -- 😈
    output_content      varchar(4000),
    modification_date       datetime
)

create table custom_words
(
    custom_word_id      bigint      primary key,
    input_content_id    bigint      references      input_contents(input_content_id),
    custom_word         varchar(100)
)

create table visual_content_features
(
        visual_content_feature_id   int         primary key,
        input_content_id            bigint      references      input_contents(input_content_id),
        blur_radius                 int,
        fps                         int,        -- for image = 1 ,  for video >= 15
)

create table processed_text
(
    processed_text_id       bigint      primary key,
    input_content_id        bigint      references              input_contents(input_content_id),
    original_word           varchar(100),
    is_flagged              varchar(5),         -- true , false
    filtered_word           varchar(100)
)

create table processed_audio
(
    processed_audio_id      bigint      primary key,
    input_content_id        bigint      references              input_contents(input_content_id),
    start_time              bigint,
    end_time                bigint,
    is_flagged              varchar(5),         -- true  ,  false
    original_word           varchar(100),
    filtered_word           varchar(100)
)

create table processed_image
(
        processed_image_id      bigint      primary key,
        input_content_id        bigint      references              input_contents(input_content_id),
        detected_content        varchar(4000),
        is_flagged              varchar(5),         -- true , false
)

create table processed_video
(
    processed_video_id      bigint      primary key,
    input_content_id        bigint      references              input_contents(input_content_id),
    start_frame             bigint,
    end_frame               bigint,
    detected_content        varchar(4000),
    is_flagged              varchar(5)              -- true , false
)

