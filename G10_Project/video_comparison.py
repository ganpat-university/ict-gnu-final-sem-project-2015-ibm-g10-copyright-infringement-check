import os
import cv2
import sys
import imagehash
from PIL import Image
from skimage.metrics import structural_similarity as ssim
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

videos_folder = "/home/poseidon/Databases/Video_Database/"

def video_avg_hash(video_path):
    video = cv2.VideoCapture(video_path)
    total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    hashes = []

    for frame_index in range(0, total_frames, 10): # Skipping 10 frames at a time
        video.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        ret, frame = video.read()
        if ret:
            image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            frame_hash = imagehash.average_hash(image)
            hashes.append(frame_hash)

    video.release()
    avg_hash = sum(hashes) / len(hashes)
    return avg_hash

width = 640
height = 480

def compare_video_frames(args):
    global width, height
    frame1, frame2 = args
    frame1 = cv2.resize(frame1, (width, height))
    frame2 = cv2.resize(frame2, (width, height))
    gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
    return ssim(gray1, gray2, full=True)[0]


def compare_video(video_path, progress_callback=None):
    global width, height
    video1 = cv2.VideoCapture(video_path)
    # video1_avg_hash = video_avg_hash(video_path)

    unique = True

    # hash_db = defaultdict(set)

    # for filename in os.listdir(videos_folder):
    #     if filename.endswith('.mp4') or filename.endswith('.avi'):
    #         filepath = os.path.join(videos_folder, filename)
    #         file_avg_hash = video_avg_hash(filepath)
    #         hash_db[file_avg_hash].add(filename)

    hash_match_found = False
    # for stored_hash, file_set in hash_db.items():
    #     if video1_avg_hash - stored_hash < 10: # Threshold value for hash difference
    #         for file in file_set:
    #             print("Similar Video Found (using hash)!!!")
    #             print("Video Name:", file)
    #             print("Hash Similarity:", 100 - (video1_avg_hash - stored_hash) / 64 * 100, "%")
    #             unique = False
    #             hash_match_found = True
    #             break

    #     if hash_match_found:
    #         break

    if not hash_match_found:
        v1_total_frames = int(video1.get(cv2.CAP_PROP_FRAME_COUNT))

        # Get the frames per second (fps) of the videos
        video1_fps = video1.get(cv2.CAP_PROP_FPS)
        video1_total_frames = int(video1.get(cv2.CAP_PROP_FRAME_COUNT))
        video1_length = video1_total_frames / video1_fps

        filename_ls = list(filter(lambda filename : filename.endswith('.mp4') or filename.endswith('.avi'), os.listdir(videos_folder)))
        total = len(filename_ls)
        # print(total)
        vid_count = 0
        total_frame_count = total * v1_total_frames
        frame_count_now = 0

        # Loop through all the videos in the folder
        for filename in filename_ls:
            vid_count += 1

            video2 = cv2.VideoCapture(videos_folder + filename)
            
            video2_fps = video2.get(cv2.CAP_PROP_FPS)
            video2_total_frames = int(video2.get(cv2.CAP_PROP_FRAME_COUNT))
            video2_length = video2_total_frames / video2_fps

            if video1_length < 180 and video2_length < 180:
                # 480p Resolution
                width = 640 
                height = 480
            else:
                # 96p Resolution
                width = 128
                height = 96

            # Initialize the frame counters
            frame_count1 = 0
            frame_count2 = 0

            # Initialize the frame similarity scores
            similarity_scores = []

            # Reset the file pointer to the beginning of the first video
            video1.set(cv2.CAP_PROP_POS_FRAMES, 0)

            with ThreadPoolExecutor() as executor:
            # Loop through the frames of the videos
                while True:
                    # Read a frame from each video
                    ret1, frame1 = video1.read()
                    ret2, frame2 = video2.read()

                    # If either video has reached the end, break the loop
                    if not ret1 or not ret2:
                        break

                    # Increment the frame counters
                    frame_count1 += 1
                    frame_count2 += 1
                    frame_count_now += 1

                    # Skip every other frame
                    if frame_count1 % 2 == 0 and frame_count2 % 2 == 0:
                        continue

                    
                    # Calculate the structural similarity index (SSIM) between the frames
                    ssim_score = executor.submit(compare_video_frames, (frame1, frame2)).result()

                    # Append the similarity score to the list
                    similarity_scores.append(ssim_score)

                    # progress_percent = int(frame_count1 / total_frames * 100)
                    # print("Video {}/{}  Progress: {}% \n".format(vid_count, total, progress_percent), end="\r")

                    total_progress = int(vid_count / total * 100)
                    total_progress = int(frame_count_now / total_frame_count * 100)    
                    if progress_callback:
                        progress_callback(total_progress)

            # Calculate the average similarity score
            avg_similarity_score = sum(similarity_scores) / len(similarity_scores)

            # Print the average similarity score
            # print("The average similarity score between the two videos is:", avg_similarity_score)
            # print("The similarity between the two videos is:", avg_similarity_score*100, "%")
            video2.release()
            if (avg_similarity_score * 100) > 80 :
                print("Similar Video Found!!!")
                print("Video Name: {}".format(filename))
                print(f"Similarity = {(avg_similarity_score * 100):.2f}%")
                unique = False
                break

        if unique:
            print("No Match Found.")
            print("This is a Unique Video")


        # Release the video capture objects
        video1.release()

        if (avg_similarity_score * 100) > 65:
            return {
                "unique": False,
                "filename": filename,
                "similarity": avg_similarity_score * 100
            }

    video1.release()

    return {
        "unique": True
    }
