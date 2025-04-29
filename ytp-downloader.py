#!/usr/bin/env python3
import os
import time
import random
import subprocess
import argparse
import re
import sys

def validate_playlist(url):
    """Verify if the playlist exists before proceeding"""
    print("Validating playlist URL...")
    
    # Use --simulate to validate without downloading
    check_cmd = [
        "yt-dlp", 
        "--flat-playlist", 
        "--simulate",
        "--print", "title",
        url
    ]
    
    try:
        # Don't capture output so we can see any warning messages
        result = subprocess.run(check_cmd, capture_output=True, text=True)
        
        # Check for errors in stderr
        if "ERROR:" in result.stderr or "WARNING: [youtube:tab] YouTube said: The playlist does not exist." in result.stderr:
            print(f"❌ Error: {result.stderr.strip()}")
            print("The playlist URL appears to be invalid or the playlist doesn't exist.")
            return False
            
        # Check if we got any video titles
        titles = [t for t in result.stdout.strip().split('\n') if t]
        if not titles:
            print("❌ Error: No videos found in the playlist.")
            return False
            
        return True
    except Exception as e:
        print(f"❌ Error validating playlist: {str(e)}")
        return False

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
        
        # Check for errors in stderr
        if "ERROR:" in result.stderr:
            print(f"⚠️ Warning: {result.stderr.strip()}")
            print("Using default resolutions instead.")
            return [360, 480, 720, 1080]
            
        first_video_id = result.stdout.strip().split('\n')[0]
        
        if not first_video_id:
            print("⚠️ Couldn't extract video ID from playlist. Using default resolutions.")
            return [360, 480, 720, 1080]
            
        first_video_url = f"https://www.youtube.com/watch?v={first_video_id}"
        
        # Get formats for the first video
        formats_cmd = [
            "yt-dlp",
            "-F",
            first_video_url
        ]
        
        formats_result = subprocess.run(formats_cmd, capture_output=True, text=True)
        
        # Check for errors
        if "ERROR:" in formats_result.stderr:
            print(f"⚠️ Warning: {formats_result.stderr.strip()}")
            print("Using default resolutions instead.")
            return [360, 480, 720, 1080]
            
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
        
        # If no resolutions found, return defaults
        if not resolutions:
            print("⚠️ No specific resolutions found. Using default resolutions.")
            return [360, 480, 720, 1080]
            
        return sorted(list(resolutions))
        
    except Exception as e:
        print(f"⚠️ Error getting format info: {str(e)}")
        print("Using default resolutions instead.")
        return [360, 480, 720, 1080]

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
        
        # Check for errors
        if "ERROR:" in result.stderr:
            print(f"❌ Error fetching playlist info: {result.stderr.strip()}")
            return False
            
        video_titles = [t for t in result.stdout.strip().split('\n') if t]
        video_count = len(video_titles)
        
        if video_count > 0:
            print(f"✓ Found {video_count} videos in playlist")
        else:
            print("❌ Error: No videos found in the playlist.")
            return False
            
    except Exception as e:
        print(f"❌ Error fetching playlist info: {str(e)}")
        return False
    
    print(f"\nDownloading {video_count} videos to '{output_dir}' directory")
    print(f"Selected maximum quality: {quality}p")
    print("Press Ctrl+C to stop the download process at any time\n")
    
    # Download command - improved for better quality
    download_cmd = [
        "yt-dlp",
        "--no-warnings",           # Suppress warnings
        # Format selection - prioritize best video+audio in the quality range
        "-f", f"bestvideo[height<={quality}]+bestaudio/best[height<={quality}]/best",
        "--merge-output-format", "mp4",         # Output format
        "-o", f"{output_dir}/%(title)s.%(ext)s",  # Output filename pattern
        "--no-playlist-reverse",                # Keep original order
        "--embed-thumbnail",                    # Embed thumbnail in output file
        "--add-metadata",                       # Add metadata to file
        "--no-overwrites",                      # Don't overwrite files
        "--continue",                           # Resume downloads
        playlist_url
    ]
    
    try:
        # Run without capturing output to show download progress
        process = subprocess.run(download_cmd)
        
        # Verify that files were actually downloaded
        downloaded_files = os.listdir(output_dir)
        if not downloaded_files:
            print("\n❌ Error: No files were downloaded.")
            return False
            
        print("\n🏁 Download completed successfully!")
        print(f"Downloaded {len(downloaded_files)} file(s) to '{output_dir}' directory.")
        return True
        
    except KeyboardInterrupt:
        print("\n⏹️ Download stopped by user")
        return False
    except Exception as e:
        print(f"\n❌ Error during download: {str(e)}")
        return False

if __name__ == "__main__":
    print("🎬 YouTube Playlist Downloader")
    print("----------------------------")
    
    playlist_url = input("Enter playlist URL: ").strip()
    
    # Validate the playlist URL first
    if not validate_playlist(playlist_url):
        print("\n❌ Download cancelled due to invalid playlist.")
        sys.exit(1)
        
    output_dir = input("Output directory [downloads]: ").strip() or "downloads"
    
    # Get and display available quality options
    available_resolutions = list_available_formats(playlist_url)
    
    # Safety check to ensure available_resolutions is not empty
    if not available_resolutions:
        print("⚠️ Couldn't detect available resolutions. Using default options.")
        available_resolutions = [360, 480, 720, 1080]
    
    resolution_str = ", ".join([f"{r}p" for r in available_resolutions])
    print(f"Available quality options: {resolution_str}")
    
    default_quality = max(available_resolutions)
    quality_input = input(f"Maximum video quality [{default_quality}p]: ").strip()
    quality = quality_input.replace("p", "") if quality_input else str(default_quality)
    
    # Download and check if it was successful
    success = download_playlist(playlist_url, output_dir, quality)
    
    if not success:
        print("\n❌ Download process completed with errors.")
        sys.exit(1)
    else:
        sys.exit(0)