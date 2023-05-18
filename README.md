# Slideshow Extractor

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

## Description

The Slideshow Extractor is a tool designed to automatically extract slides from lecture videos. It can work with both YouTube video links and local video files, allowing you to conveniently generate PDFs of the slides.

## Features

- Extract slides from lecture videos
- Support for YouTube video links and local video files
- Automatic conversion of slides into PDF format
- Easy-to-use command-line interface

## Installation

1. Make sure you have [Python](https://www.python.org/) installed.
2. Clone this repository:

```bash
git clone https://github.com/TalentedB/Slideshow-Extractor
```

3. Navigate to the project directory:

```bash
cd slideshow-extractor
```

4. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

To extract slides from a YouTube video:

```bash
python main.py --youtube <youtube_link> --threshold <threshold> --output <output_path>
```

To extract slides from a local video file:

```bash
python main.py --file <video_path> --threshold <threshold> --output <output_path>
```

By default, the extracted slides will be saved as a PDF file in the project directory.

## Contributing

Contributions are welcome! If you find any issues or would like to suggest improvements, please open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.




---


