import os  # For file and directory operations
import time  # To handle download timing
import shutil  # To move downloaded files
import validators  # To validate URL format
import json  # To parse Chrome DevTools logs

from selenium import webdriver  # Main Selenium WebDriver module
from selenium.webdriver.chrome.options import Options  # For configuring Chrome
from selenium.webdriver.chrome.service import Service  # To manage ChromeDriver service
from selenium.webdriver.chrome.webdriver import WebDriver  # WebDriver type hint
from webdriver_manager.chrome import (
    ChromeDriverManager,
)  # Automatically manage driver version

# Suppress TensorFlow logs if they exist in the environment
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"


# ---------- UTILITY FUNCTIONS ----------


def is_valid_url(url: str) -> bool:
    """Check if a given string is a valid URL."""
    return validators.url(url)


def file_already_exists(file_path: str) -> bool:
    """Return True if the specified file exists on disk."""
    return os.path.isfile(file_path)


def extract_pdf_filename_from_url(url: str) -> str | None:
    """Extract the filename from a URL if it's a PDF."""
    _, filename = os.path.split(url)
    return filename.lower() if filename else None


def wait_until_pdf_downloaded(
    download_dir: str, original_files: set[str], timeout_seconds: int = 60
) -> str:
    """
    Wait for a new PDF to appear in the folder.
    Returns the path to the new PDF file.
    """
    deadline_time = time.time() + timeout_seconds
    while time.time() < deadline_time:
        current_files = set(os.listdir(download_dir))
        new_files = current_files - original_files  # Detect any new files

        for file_name in new_files:
            if file_name.endswith(".pdf") and not file_name.endswith(".crdownload"):
                full_path = os.path.join(download_dir, file_name)
                if os.path.exists(full_path):
                    return full_path

        time.sleep(0.5)  # Pause briefly before checking again

    raise TimeoutError("⏳ PDF download timed out.")


def initialize_chrome_driver_with_download_settings(download_dir: str) -> WebDriver:
    """Set up the Chrome WebDriver with PDF download preferences and DevTools logging enabled."""
    chrome_options = Options()
    # chrome_options.add_argument("--headless=new")  # Uncomment to run in headless mode
    chrome_options.add_argument("--disable-gpu")  # Disable GPU acceleration
    chrome_options.add_argument("--no-sandbox")  # Required in some environments
    chrome_options.add_argument("--log-level=3")  # Suppress console logs
    chrome_options.add_experimental_option(
        "excludeSwitches", ["enable-logging"]
    )  # Hide automation logs

    # Set Chrome preferences for PDF download behavior
    chrome_options.add_experimental_option(
        "prefs",
        {
            "download.default_directory": download_dir,  # Set download directory
            "download.prompt_for_download": False,  # Disable download prompts
            "plugins.always_open_pdf_externally": True,  # Disable in-browser PDF viewer
        },
    )

    # Enable performance logging (needed to get HTTP status)
    chrome_options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

    # Start ChromeDriver with WebDriver Manager
    chrome_service = Service(ChromeDriverManager().install(), log_path=os.devnull)
    return webdriver.Chrome(service=chrome_service, options=chrome_options)


def get_http_status_code_from_browser(driver: WebDriver, target_url: str) -> int | None:
    """
    Use Chrome DevTools logs to find the HTTP status code for a given URL.
    Returns the status code (e.g., 200) or None if not found.
    """
    driver.get("about:blank")  # Reset previous network logs
    driver.get(target_url)  # Load the target URL

    browser_logs = driver.get_log("performance")

    for log_entry in browser_logs:
        try:
            message = json.loads(log_entry["message"])["message"]

            if message["method"] == "Network.responseReceived":
                response = message["params"]["response"]
                if response["url"] == target_url:
                    return response["status"]
        except Exception:
            continue

    return None  # Status not found


def download_pdf_if_valid(
    pdf_url: str, driver: WebDriver, download_directory: str
) -> None:
    """
    Attempt to download a PDF from the given URL using Selenium.
    Skips if the file exists or if the HTTP status is not 200.
    """
    if not is_valid_url(pdf_url):
        print(f"❌ Invalid URL format: {pdf_url}")
        return

    pdf_filename = extract_pdf_filename_from_url(pdf_url)
    if not pdf_filename or not pdf_filename.endswith(".pdf"):
        print(f"❌ Could not extract PDF filename from: {pdf_url}")
        return

    destination_path = os.path.join(download_directory, pdf_filename)

    if file_already_exists(destination_path):
        print(f"⚠️  Skipping (already downloaded): {destination_path}")
        return

    try:
        # Check HTTP status via Chrome DevTools
        status_code = get_http_status_code_from_browser(driver, pdf_url)
        if status_code != 200:
            print(f"⏭️  Skipping {pdf_filename} (HTTP {status_code})")
            return

        # Record files currently in the directory before download starts
        files_before_download = set(os.listdir(download_directory))

        print(f"⬇️  Starting download: {pdf_filename}")
        driver.get(pdf_url)

        downloaded_file_path = wait_until_pdf_downloaded(
            download_directory, files_before_download
        )

        # Move the file to its final destination
        shutil.move(downloaded_file_path, destination_path)
        print(f"✅ Download complete: {destination_path}")

    except Exception as error:
        print(f"❌ Download failed for {pdf_filename}: {error}")


def read_lines_from_file(file_path: str) -> list[str]:
    """Read all non-empty lines from a file and return them as a list."""
    with open(file_path, "r") as file_handle:
        return [line.strip() for line in file_handle.readlines() if line.strip()]


# ---------- ENTRY POINT ----------

if __name__ == "__main__":
    url_list_file = "valid_urls.txt"  # Input file containing one URL per line
    download_folder_path = os.path.abspath("PDFs")  # Folder to store downloaded PDFs
    os.makedirs(
        download_folder_path, exist_ok=True
    )  # Create folder if it doesn't exist

    url_list = read_lines_from_file(url_list_file)  # Read input URLs
    chrome_driver = initialize_chrome_driver_with_download_settings(
        download_folder_path
    )  # Start Chrome

    try:
        for pdf_url in url_list:
            download_pdf_if_valid(pdf_url, chrome_driver, download_folder_path)
    finally:
        chrome_driver.quit()  # Always quit the browser session
