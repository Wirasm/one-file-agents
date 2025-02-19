import os
import subprocess


def download_yt_script(url: str) -> str:
    """
    Download and extract script from YouTube video

    Credit:
      Original Code: https://github.com/davidgasquez/dotfiles/blob/bb9df4a369dbaef95ca0c35642de491c7dd41269/shell/zshrc#L75
      Simonw Blog: https://simonwillison.net/2024/Dec/19/

    """
    try:
        # Use yt-dlp to download subtitles directly to a file
        subtitle_cmd = [
            "yt-dlp",
            "--quiet",
            "--skip-download",
            "--write-sub",
            "--sub-langs",
            "en",
            "--write-auto-sub",
            "--convert-subs",
            "vtt",
            "--output",
            "temp_subtitle",
            url,
        ]

        subprocess.run(subtitle_cmd, check=True)

        # Find the subtitle file
        subtitle_files = [
            f
            for f in os.listdir(".")
            if f.startswith("temp_subtitle") and f.endswith(".vtt")
        ]

        if not subtitle_files:
            raise RuntimeError("No subtitle file found")

        # Read and process the subtitle file
        with open(subtitle_files[0], "r", encoding="utf-8") as f:
            content = f.read()

        # Clean up the subtitle file
        for file in subtitle_files:
            os.remove(file)

        # Process the content - remove WEBVTT headers and timing
        lines = []
        for line in content.split("\n"):
            line = line.strip()
            if line and not line.startswith(("WEBVTT", "Kind:", "Language:", "-->")):
                if not any(c.isdigit() for c in line):  # Skip timestamp lines
                    lines.append(line)

        processed_content = " ".join(lines)

        if not processed_content:
            raise RuntimeError("No transcript content found")

        return processed_content

    except (subprocess.CalledProcessError, IOError) as e:
        raise RuntimeError(f"Failed to download YouTube script: {str(e)}")


if __name__ == "__main__":
    video_url = "https://www.youtube.com/watch?v=W6Z0U11nnhA"  # replace with the URL you want to process
    output_folder = "transcripts"
    # take the video url after the / as the filename
    output_filename = video_url.split("/")[-1] + ".md"

    try:
        transcript = download_yt_script(video_url)

        # Create the 'transcripts' folder if it doesn't exist
        os.makedirs(output_folder, exist_ok=True)

        # Construct the full file path
        output_filepath = os.path.join(output_folder, output_filename)

        # Save the transcript to a Markdown file
        with open(output_filepath, "w", encoding="utf-8") as md_file:
            md_file.write(transcript)

        print(f"Transcript saved to: {output_filepath}")

    except RuntimeError as e:
        print(f"Error: {e}")
