import os
import csv
import googleapiclient.discovery
import googleapiclient.errors

# API configuration
api_service_name = "youtube"
api_version = "v3"
api_key = "AIzaSyCOeyrZMmYxhuqEkk9oyhfGAZa8rmgoe4s"

# Create a resource object
youtube = googleapiclient.discovery.build(api_service_name, api_version, developerKey=api_key)

# Function to get video details
def get_videos(channel_id):
    videos = []
    page_token = None

    while True:
        request = youtube.search().list(
            part="snippet",
            channelId=channel_id,
            maxResults=50,
            order="date",
            publishedAfter="2022-01-01T00:00:00Z",
            publishedBefore="2024-06-30T23:59:59Z",
            pageToken=page_token
        )

        try:
            response = request.execute()
        except googleapiclient.errors.HttpError as e:
            print(f"An error occurred: {e}")
            break

        for item in response.get('items', []):
            if item['id']['kind'] != 'youtube#video':
                continue
            video_id = item['id'].get('videoId')
            if not video_id:
                continue
            try:
                video_details = youtube.videos().list(
                    part="snippet,statistics",
                    id=video_id
                ).execute()
            except googleapiclient.errors.HttpError as e:
                print(f"An error occurred: {e}")
                continue

            comments = []
            try:
                # Fetch comments for the video
                comment_request = youtube.commentThreads().list(
                    part="snippet,replies",
                    videoId=video_id,
                    maxResults=100
                )
                comment_response = comment_request.execute()

                for comment_item in comment_response.get('items', []):
                    top_comment = comment_item['snippet']['topLevelComment']['snippet']
                    comment_data = {
                        'Comment': top_comment['textDisplay'],
                        'Likes': top_comment.get('likeCount', 'N/A'),
                        'PublishedAt': top_comment.get('publishedAt', 'N/A')
                    }
                    # Fetch replies to the comment
                    replies = []
                    if 'replies' in comment_item:
                        for reply in comment_item['replies']['comments']:
                            reply_data = {
                                'Reply': reply['snippet']['textDisplay'],
                                'Likes': reply['snippet'].get('likeCount', 'N/A'),
                                'PublishedAt': reply['snippet'].get('publishedAt', 'N/A')
                            }
                            replies.append(reply_data)
                    comment_data['Replies'] = replies
                    comments.append(comment_data)
            except googleapiclient.errors.HttpError as e:
                if "commentsDisabled" in str(e):
                    print(f"Comments are disabled for video ID {video_id}. Skipping...")
                    continue
                else:
                    print(f"An error occurred while fetching comments: {e}")
                    continue

            for video in video_details.get('items', []):
                title = video['snippet']['title']
                description = video['snippet']['description']
                likes = video['statistics'].get('likeCount', 'N/A')
                views = video['statistics'].get('viewCount', 'N/A')
                comments_count = len(comments)
                videos.append({
                    'Title': title,
                    'Description': description,
                    'Likes': likes,
                    'Views': views,
                    'Comments': comments_count,
                    'All_Comments': comments  # Append all comments to the dictionary
                })

        page_token = response.get('nextPageToken')
        if not page_token:
            break

    return videos

# Save data to CSV
def save_to_csv(data, filename):
    if not data:
        print("No data to save.")
        return

    keys = data[0].keys()
    with open(filename, 'w', newline='', encoding='utf-8') as output_file:
        dict_writer = csv.DictWriter(output_file, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(data)
    print(f"Data saved to {filename}")

# Channel ID for Logan Paul
channel_id = "UCG8rbF3g2AMX70yOd8vqIZg"

# Fetch video details
video_details = get_videos(channel_id)

# Check if data is fetched and save it
save_to_csv(video_details, 'logan_paul_videos_with_comments_and_reactions.csv')
