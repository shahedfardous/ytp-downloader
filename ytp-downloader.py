#!/usr/bin/env python3
import os
import time
import random
import subprocess
import argparse
import re

def list_available_formats(url):
    """Get available formats for a sample video in the playlist"""
    print("Checking available quality options...")
    
    # Get the first video from the playlist
    playlist_info_cmd = [
        "yt-dlp", 
        "--flat-playlist", 
        "--print", "id",
        "--playlist-items", "1",
        url
    ]
    
    try:
        result = subprocess.run(playlist_info_cmd, capture_output=True, text=True)
        first_video_id = result.stdout.strip().split('\n')[0]
        first_video_url = f"https://www.youtube.com/watch?v={first_video_id}"
        
        # Get formats for the first video
        formats_cmd = [
            "yt-dlp",
            "-F",
            first_video_url
        ]
        
        formats_result = subprocess.run(formats_cmd, capture_output=True, text=True)
        format_text = formats_result.stdout
        
        # Extract available resolutions
        resolutions = set()
        for line in format_text.split('\n'):
            # Look for resolution info in format lines
            match = re.search(r'(\d+)x(\d+)', line)
            if match:
                height = int(match.group(2))
                if height >= 360:  # Only include reasonably good resolutions
                    resolutions.add(height)
        
        return sorted(list(resolutions))
    except Exception as e:
        print(f"Error getting format info: {str(e)}")
        # Return default resolutions if we can't get actual ones
        return [360, 480, 720, 1080, 1440, 2160]

def download_playlist(playlist_url, output_dir="downloads", quality="1080"):
    """Download a YouTube playlist using yt-dlp with best quality"""
    os.makedirs(output_dir, exist_ok=True)
    
    # First, get video count
    print("Fetching playlist information...")
    count_cmd = [
        "yt-dlp", 
        "--flat-playlist", 
        "--print", "title",
        playlist_url
    ]
    
    try:
        result = subprocess.run(count_cmd, capture_output=True, text=True)
        video_count = len(result.stdout.strip().split('\n'))
        print(f"✓ Found {video_count} videos in playlist")
    except Exception as e:
        print(f"Error getting playlist info: {str(e)}")
        print("Continuing with download anyway...")
        video_count = "unknown number of"
    
    print(f"\nDownloading {video_count} videos to '{output_dir}' directory")
    print(f"Selected maximum quality: {quality}p")
    print("Press Ctrl+C to stop the download process at any time\n")
    
    # Download command - improved for better quality
    download_cmd = [
        "yt-dlp",
        # Format selection - prioritize best video+audio in the quality range
        "-f", f"bestvideo[height<={quality}]+bestaudio/best[height<={quality}]/best",
        "--merge-output-format", "mp4",         # Output format
        "-o", f"{output_dir}/%(title)s.%(ext)s",  # Output filename pattern
        "--no-playlist-reverse",                # Keep original order
        "--embed-thumbnail",                    # Embed thumbnail in output file
        "--add-metadata",                       # Add metadata to file
        "--no-overwrites",                      # Don't overwrite files
        "--continue",                           # Resume downloads
        # "--verbose",                          # Uncomment for debugging
        playlist_url
    ]
    
    try:
        subprocess.run(download_cmd)
        print("\n🏁 Download completed successfully!")
    except KeyboardInterrupt:
        print("\n⏹️ Download stopped by user")
    except Exception as e:
        print(f"\n❌ Error during download: {str(e)}")

if __name__ == "__main__":
    print("🎬 YouTube Playlist Downloader")
    print("----------------------------")
    
    playlist_url = input("Enter playlist URL: ").strip()
    output_dir = input("Output directory [downloads]: ").strip() or "downloads"
    
    # Get and display available quality options
    available_resolutions = list_available_formats(playlist_url)
    resolution_str = ", ".join([f"{r}p" for r in available_resolutions])
    print(f"Available quality options: {resolution_str}")
    
    quality_input = input(f"Maximum video quality [{max(available_resolutions)}p]: ").strip()
    quality = quality_input.replace("p", "") if quality_input else str(max(available_resolutions))
    
    download_playlist(playlist_url, output_dir, quality)