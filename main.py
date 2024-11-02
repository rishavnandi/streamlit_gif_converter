import streamlit as st
import moviepy.editor as mp
import tempfile
import os
from pathlib import Path
import logging
from typing import Optional, Tuple
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure page settings
st.set_page_config(
    page_title="Video to GIF Converter",
    page_icon="🎥",
    layout="centered"
)

# Custom CSS
st.markdown("""
    <style>
        .stAlert {
            margin-top: 1rem;
            margin-bottom: 1rem;
        }
        .stButton>button {
            width: 100%;
        }
    </style>
""", unsafe_allow_html=True)


class GIFConverter:
    """Handle video to GIF conversion operations."""

    QUALITY_SETTINGS = {
        "Best": {"opt": "-lossless"},
        "Good": {"opt": None},
        "Medium": {"opt": None},
        "Low": {"opt": None}
    }

    @staticmethod
    def validate_video(video_file) -> Tuple[bool, str]:
        """Validate the uploaded video file."""
        if video_file is None:
            return False, "Please upload a video file."

        if video_file.size > 200 * 1024 * 1024:  # 200MB limit
            return False, "File size too large. Please upload a video smaller than 200MB."

        return True, ""

    @staticmethod
    def convert_to_gif(
        video_path: str,
        start_time: float,
        duration: float,
        sample_interval: float,
        playback_interval: float,
        quality: str,
        repeat: str
    ) -> Optional[str]:
        """Convert video to GIF with custom sampling and playback intervals."""
        try:
            clip = mp.VideoFileClip(video_path)

            # Validate start time and duration
            if start_time >= clip.duration:
                raise ValueError("Start time exceeds video duration")

            end_time = min(start_time + duration, clip.duration)

            # Calculate sampling times
            sample_times = np.arange(start_time, end_time, sample_interval)

            # Create a sequence of frames at the sampling times
            frames = []
            for t in sample_times:
                frames.append(clip.get_frame(t))

            # Create a new clip from the sampled frames
            sampled_clip = mp.ImageSequenceClip(
                frames, fps=1/playback_interval)

            # Create output directory if it doesn't exist
            output_dir = Path("temp_gifs")
            output_dir.mkdir(exist_ok=True)

            output_path = str(
                output_dir / f"output_{int(start_time)}_{int(duration)}.gif")

            # Apply quality settings
            settings = GIFConverter.QUALITY_SETTINGS[quality]

            # Set loop parameter based on repeat selection
            loop = 0 if repeat == "Repeat" else 1

            sampled_clip.write_gif(
                output_path,
                fps=1/playback_interval,  # Convert interval to fps
                program='ffmpeg',
                opt=settings["opt"],
                loop=loop
            )

            return output_path

        except Exception as e:
            logger.error(f"Error converting video to GIF: {str(e)}")
            return None
        finally:
            if 'clip' in locals():
                clip.close()
            if 'sampled_clip' in locals():
                sampled_clip.close()


def main():
    st.title("🎥 Video to GIF Converter")

    # Sidebar with information
    with st.sidebar:
        st.header("ℹ️ Information")
        st.info("""
        - Supported format: MP4
        - Maximum file size: 200MB
        - Higher quality means larger file size
        - Sampling interval: How often to capture frames
        - Playback interval: How fast to play frames
        """)

        st.header("💡 Tips")
        st.info("""
        - Lower sampling interval = smoother animation but larger file
        - Playback interval controls GIF speed
        - Use 'Medium' quality for a good balance
        """)

    # Main content
    uploaded_file = st.file_uploader(
        "Drop your video file here",
        type=["mp4"],
        help="Upload an MP4 video file to convert to GIF"
    )

    if uploaded_file:
        # Validate uploaded file
        is_valid, error_message = GIFConverter.validate_video(uploaded_file)
        if not is_valid:
            st.error(error_message)
            return

        # Display video preview
        st.video(uploaded_file)

        # Create columns for input controls
        col1, col2 = st.columns(2)

        with col1:
            start_time = st.number_input(
                "Sample video from time (sec)",
                min_value=0.0,
                value=0.0,
                step=0.1,
                help="Starting point of your GIF"
            )

            sample_interval = st.number_input(
                "Sample video at every (sec)",
                min_value=0.1,
                value=0.5,
                step=0.1,
                help="Interval between frame captures"
            )

            quality = st.selectbox(
                "GIF Quality",
                options=list(GIFConverter.QUALITY_SETTINGS.keys()),
                help="Higher quality means larger file size"
            )

        with col2:
            duration = st.number_input(
                "Sample duration (sec)",
                min_value=0.1,
                value=3.0,
                step=0.1,
                help="Total duration of your GIF"
            )

            playback_interval = st.number_input(
                "Playback GIF at every (sec)",
                min_value=0.1,
                value=0.2,
                step=0.1,
                help="Control GIF playback speed"
            )

            repeat = st.selectbox(
                "Repeat playback",
                options=["No repeat", "Repeat"],
                help="Choose if GIF should loop"
            )

        if st.button("🎬 Convert to GIF", use_container_width=True):
            try:
                with st.spinner("Converting... Please wait"):
                    # Save uploaded file temporarily
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
                        temp_file.write(uploaded_file.getbuffer())
                        temp_file_path = temp_file.name

                    # Convert to GIF
                    gif_path = GIFConverter.convert_to_gif(
                        temp_file_path,
                        start_time,
                        duration,
                        sample_interval,
                        playback_interval,
                        quality,
                        repeat
                    )

                    # Clean up temporary video file
                    os.unlink(temp_file_path)

                    if gif_path and os.path.exists(gif_path):
                        st.success("✨ Conversion completed!")

                        # Display the GIF
                        with open(gif_path, "rb") as gif_file:
                            st.image(gif_file.read(),
                                     caption="Your converted GIF")

                        # Add download button
                        with open(gif_path, "rb") as gif_file:
                            st.download_button(
                                label="⬇️ Download GIF",
                                data=gif_file,
                                file_name="converted.gif",
                                mime="image/gif"
                            )

                        # Clean up GIF file
                        os.unlink(gif_path)
                    else:
                        st.error(
                            "Failed to convert video to GIF. Please try again.")

            except Exception as e:
                logger.error(f"Error in conversion process: {str(e)}")
                st.error("An error occurred during conversion. Please try again.")

    st.divider()
    st.markdown("Made with ❤️ using Streamlit")


if __name__ == "__main__":
    main()
