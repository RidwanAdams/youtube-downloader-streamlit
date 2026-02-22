import streamlit as st
import os
import subprocess
from pytubefix import YouTube
from src.downloader import YouTubeDownloader, StreamOption


st.set_page_config(
    page_title="YouTube Downloader",
    page_icon="🎬",
    layout="centered"
)


def get_available_resolutions(streams: list[StreamOption]) -> list[str]:
    """Extract unique resolutions from available streams."""
    resolutions = set()
    for s in streams:
        if s.resolution:
            resolutions.add(s.resolution)
    
    # Sort by resolution number (highest first)
    def res_key(r):
        import re
        m = re.search(r"(\d+)", r)
        return int(m.group(1)) if m else 0
    
    return sorted(resolutions, key=res_key, reverse=True)


def get_available_formats(streams: list[StreamOption]) -> list[str]:
    """Extract unique MIME types from available streams."""
    formats = set()
    for s in streams:
        if s.mime_type:
            fmt = s.mime_type.split("/")[-1].upper()
            formats.add(fmt)
    return sorted(formats)


def main():
    st.title("🎬 YouTube Video Downloader")
    st.markdown("Download high-resolution videos from YouTube easily!")
    
    # URL Input
    url = st.text_input("🔗 Enter YouTube URL", placeholder="https://www.youtube.com/watch?v=...")
    
    if url:
        try:
            # Initialize downloader
            downloader = YouTubeDownloader(url)
            
            # Fetch streams
            with st.spinner("Fetching video information..."):
                streams = downloader.fetch_streams()
            
            if not streams:
                st.error("No streams available for this video.")
                return
            
            # Get video info
            yt = YouTube(url)
            
            # Display video thumbnail and info
            col1, col2 = st.columns([1, 2])
            with col1:
                st.image(yt.thumbnail_url, width=200)
            with col2:
                st.subheader(yt.title)
                st.write(f"**Author:** {yt.author}")
                st.write(f"**Duration:** {yt.length // 60}:{yt.length % 60:02d}")
                st.write(f"**Views:** {yt.views:,}")
            
            st.divider()
            
            # Resolution and Format Selection
            col1, col2 = st.columns(2)
            
            with col1:
                available_resolutions = get_available_resolutions(streams)
                resolution = st.selectbox(
                    "📺 Resolution",
                    options=available_resolutions,
                    index=0 if available_resolutions else 0
                )
            
            with col2:
                available_formats = get_available_formats(streams)
                video_format = st.selectbox(
                    "📁 Format",
                    options=["MP4", "WEBM", "MKV"] + available_formats,
                    index=0
                )
            
            # Download type
            download_type = st.radio(
                "⬇️ Download Type",
                ["Video", "Audio Only"],
                horizontal=True
            )
            
            # Download Button
            if st.button("🚀 Prepare Download", type="primary", use_container_width=True):
                try:
                    # Find best matching stream
                    chosen_stream = downloader.select_stream_for_resolution(streams, resolution)
                    
                    if not chosen_stream:
                        st.error("No suitable stream found for the selected resolution.")
                        return
                    
                    # Progress bar
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # Download function with progress
                    def on_progress(stream, chunk, bytes_remaining):
                        total_size = stream.filesize
                        downloaded = total_size - bytes_remaining
                        percent = int((downloaded / total_size) * 100)
                        progress_bar.progress(percent)
                        status_text.text(f"Downloading... {percent}%")
                    
                    # Perform download to a temporary location
                    status_text.text("Starting download...")
                    temp_dir = "temp_downloads"
                    os.makedirs(temp_dir, exist_ok=True)
                    
                    if download_type == "Video":
                        file_path = downloader.download(
                            chosen_stream.itag,
                            output_path=temp_dir,
                            progress_cb=on_progress
                        )
                    else:
                        file_path = downloader.download_audio_only(
                            output_path=temp_dir,
                            progress_cb=on_progress
                        )
                    
                    progress_bar.progress(100)
                    status_text.text("✅ Downloaded to server. Ready for browser download!")
                    
                    # Read the file and provide download button
                    with open(file_path, "rb") as f:
                        file_data = f.read()
                        
                    st.download_button(
                        label="📥 Click here to save to your device",
                        data=file_data,
                        file_name=os.path.basename(file_path),
                        mime=chosen_stream.mime_type if download_type == "Video" else "audio/mpeg",
                        use_container_width=True
                    )
                    
                    # Clean up the temp file after reading
                    try:
                        os.remove(file_path)
                    except:
                        pass
                        
                except Exception as e:
                    st.error(f"❌ Download failed: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())
        
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
    
    # Footer
    st.divider()
    st.markdown(
        "<div style='text-align: center; color: gray;'>"
        "⚠️ Please respect YouTube's Terms of Service. "
        "Use responsibly."
        "</div>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
