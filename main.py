import os
import pathlib
import urllib.parse
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver


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


def setup_browser(download_dir: str) -> webdriver.Chrome:
    """
    Set up Chrome WebDriver with the necessary options for automation and downloading.
    """
    os.makedirs(name=download_dir, exist_ok=True)

    chrome_options = Options()
    # chrome_options.add_argument(argument="--headless=new")  # use new headless mode
    chrome_options.add_argument(argument="--disable-gpu")
    chrome_options.add_argument(argument="--no-sandbox")

    # Set download behavior
    prefs: dict[str, str | bool] = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "plugins.always_open_pdf_externally": True,  # Prevent Chrome from previewing PDFs
    }
    chrome_options.add_experimental_option(name="prefs", value=prefs)

    # Enable performance logging
    chrome_options.set_capability(
        name="goog:loggingPrefs", value={"performance": "ALL"}
    )

    # Launch Chrome
    driver = webdriver.Chrome(options=chrome_options)
    return driver


def get_http_status_code_from_browser(
    driver: webdriver.Chrome, target_url: str
) -> int | None:
    """
    Use Chrome DevTools logs to find the HTTP status code for a given URL.
    Returns the status code (e.g., 200) or None if not found.
    """
    driver.get(url="about:blank")
    driver.get(url=target_url)

    browser_logs = driver.get_log(log_type="performance")

    for log_entry in browser_logs:
        try:
            message = json.loads(s=log_entry["message"])["message"]
            if message["method"] == "Network.responseReceived":
                response = message["params"]["response"]
                if response["url"] == target_url:
                    return response["status"]
        except Exception:
            continue

    return None


def download_pdf_if_valid(driver: webdriver.Chrome, pdf_url: str) -> bool:
    """
    Check the HTTP status of the PDF URL and download it if the status code is 200.
    Returns True if download is triggered, False otherwise.
    """
    status_code: int | None = get_http_status_code_from_browser(
        driver=driver, target_url=pdf_url
    )

    if status_code == 200:
        return True
    else:
        return False


def main() -> None:
    # The valid urls file.
    valid_urls_path: str = "valid_urls.txt"
    # Check if the valid urls file exists.
    if not check_file_exists(system_path=valid_urls_path):
        print("Error URLS file not found.")
        return
    # The output directory
    output_directory: str = str(object=pathlib.Path(__file__).resolve().parent / "PDFs")
    # Check if the output directory exists.
    if not check_directory_exists(system_path=output_directory):
        # Create the directory.
        create_directory_at_path(system_path=output_directory)
    # Read the file line by line.
    valid_urls_content_lines: list[str] = read_file_by_line(file_name=valid_urls_path)
    # Set up the chrome driver
    driver: WebDriver = setup_browser(download_dir=output_directory)
    # Loop though the urls.
    for pdf_url in valid_urls_content_lines:
        download_pdf_if_valid(driver=driver, pdf_url=pdf_url)
    # Quit the Chrome
    driver.quit()


if __name__ == "__main__":
    # Run the main function.
    main()
