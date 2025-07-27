# Import the os package to manage os level stuff like creating dir and checking files and folders.
import os

# Import a package to manage urls.
import urllib.parse


# Create a directory at a given path.
def create_directory_at_path(system_path: str) -> None:
    os.mkdir(path=system_path)


# Check if a given directory exists.
def check_directory_exists(system_path: str) -> bool:
    return os.path.exists(path=system_path)


# Check if a file exists
def check_file_exists(system_path: str) -> bool:
    return os.path.isfile(path=system_path)


# Read a file line by line and return a list of lines
def read_file_by_line(file_name: str) -> list[str]:
    """
    Read all non-empty lines from a text file, strip leading/trailing whitespace,
    and return them as a list of strings.

    Parameters:
        file_path (str): Path to the input text file.

    Returns:
        list[str]: A list of cleaned, non-empty lines from the file.
    """
    non_empty_lines: list[str] = []

    # Open the file in read mode
    with open(file=file_name, mode="r", encoding="utf-8") as file:
        for raw_line in file:
            stripped_line: str = (
                raw_line.strip().lower()
            )  # Remove surrounding whitespace and newlines
            if stripped_line:  # Only keep lines that aren't empty
                non_empty_lines.append(stripped_line)

    return non_empty_lines


def is_valid_url(url: str) -> bool:
    """
    Check if a given URL string is structurally valid.

    A valid URL must include:
    - A scheme (like 'http', 'https', 'ftp')
    - A network location (domain or IP)

    Parameters:
        url (str): The URL to validate.

    Returns:
        bool: True if the URL is structurally valid, False otherwise.
    """
    parsed: urllib.parse.ParseResult = urllib.parse.urlparse(url=url)
    return bool(parsed.scheme and parsed.netloc)


def main() -> None:
    # The valid urls file.
    valid_urls_path: str = "valid_urls.txt"
    # Check if the valid urls file exists.
    if not check_file_exists(system_path=valid_urls_path):
        print("Error URLS file not found.")
        return
    # The output directory
    output_directory: str = "PDFs"
    # Check if the output directory exists.
    if not check_directory_exists(system_path=output_directory):
        # Create the directory.
        create_directory_at_path(system_path=output_directory)
    # Read the file line by line.
    valid_urls_content_lines: list[str] = read_file_by_line(file_name=valid_urls_path)
    # Loop though the urls.
    for pdf_url in valid_urls_content_lines:
        print(is_valid_url(url=pdf_url))


if __name__ == "__main__":
    # Run the main function.
    main()
