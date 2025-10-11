# pocket_assist_backend

Backend of PocketAssist

## Run (development mode)
$ python main.py

## Deployment
$ bash bash/deploy_source_to_cloud_run.sh

## Start ngrok service
$ ngrok start --all 

## Directory structure
work: Working directory. <br>
tools: Commandline tools developed with python. <br>
scripts: Useful shell scripts for data processing. <br>
trained_models: Pretrained models. <br>

## bash
start_avatar_service.sh: Start Avatar service. <br>
bash bash/audio_to_avatar_video.sh: Convert audio to avatar video. <br>
start_mocap_studio.sh: Start MocapStudio. <br>
start_micro_services.sh: Start AvatarCast service. <br>
start_render_images.sh: Render images with blender. <br>

image_to_video.sh: Combine images into a video. <br>
video_to_images.sh: Split a video into images. <br>

## Packages 
Please refer the requirements.txt

## Aotomatic tests
$ pytest

# Google login
$ gcloud auth application-default login

## Deploy from source to Cloud Run
$ bash bash/deploy_source_to_cloud_run.sh

## Run Jupyter Notebook
$ jupyter notebook


