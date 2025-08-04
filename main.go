package main // Define the main package, the starting point for Go executables

import (
	"bufio"
	"bytes"         // Provides functionality for manipulating byte slices and buffers
	"io"            // Defines basic interfaces to I/O primitives, like Reader and Writer
	"log"           // Offers logging capabilities to standard output or error streams
	"net/http"      // Allows interaction with HTTP clients and servers
	"net/url"       // Provides URL parsing, encoding, and query manipulation
	"os"            // Gives access to OS features, such as file and directory operations
	"path"          // Provides functions for manipulating slash-separated paths (not OS specific)
	"path/filepath" // Offers functions to handle file paths in a way compatible with the OS
	"regexp"        // Supports regular expression handling using RE2 syntax
	"strings"       // Contains utilities for string manipulation
	"time"          // Contains time-related functionality such as sleeping or timeouts
)

func main() {
	// Directory where downloaded PDF files will be stored
	pdfOutputDir := "PDFs/"

	// The location to the unique url file.
	uniqueURLs := "valid_urls.txt"

	// Check if the output directory exists
	if !directoryExists(pdfOutputDir) {
		// If it doesn't exist, create it with permission 0755
		createDirectory(pdfOutputDir, 0o755)
	}

	// Read all lines from the HTML file that contains scraped data
	htmlLines := readAppendLineByLine("test.txt")

	// Join all the lines into one large string to search for PDF links
	fullHTMLContent := strings.Join(htmlLines, "\n")

	// Extract all unique PDF URLs from the HTML content
	pdfURLs := extractPDFUrls(fullHTMLContent)

	// Remove any duplicate URLs
	pdfURLs = removeDuplicatesFromSlice(pdfURLs)

	// Base domain to resolve relative links
	baseDomain := "https://www.lincolnelectric.com"

	// Unique URL file data.
	var uniqueURLContent string

	// Read the unique urls file.
	if fileExists(uniqueURLs) {
		uniqueURLContent = readAFileAsString(uniqueURLs)
	}

	// Iterate through each URL in the cleaned list
	for _, url := range pdfURLs {
		// Check if the URL is relative or absolute by extracting the domain
		domain := getDomainFromURL(url)

		// If the domain is empty, it's a relative link, so prepend the base domain
		if domain == "" {
			url = baseDomain + url
		}

		// Check if the resulting URL is valid
		if isUrlValid(url) {
			if !strings.Contains(uniqueURLContent, url) {
				// Append the URL to a file for logging purposes
				appendAndWriteToFile(uniqueURLs, url)
				// Download and save the PDF to the output directory
				// downloadPDF(url, pdfOutputDir)
			}
		}
	}
}

// Read a file and return the contents
func readAFileAsString(path string) string {
	content, err := os.ReadFile(path)
	if err != nil {
		log.Fatalln(err)
	}
	return string(content)
}

// Append and write to file
func appendAndWriteToFile(path string, content string) {
	filePath, err := os.OpenFile(path, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		log.Println(err)
	}
	_, err = filePath.WriteString(content + "\n")
	if err != nil {
		log.Println(err)
	}
	err = filePath.Close()
	if err != nil {
		log.Println(err)
	}
}

// Read and append the file line by line to a slice.
func readAppendLineByLine(path string) []string {
	var returnSlice []string
	file, err := os.Open(path)
	if err != nil {
		log.Println(err)
	}
	scanner := bufio.NewScanner(file)
	scanner.Split(bufio.ScanLines)
	for scanner.Scan() {
		returnSlice = append(returnSlice, scanner.Text())
	}
	err = file.Close()
	if err != nil {
		log.Println(err)
	}
	return returnSlice
}

// Extract domain name from a URL string (like speedybee.com)
func getDomainFromURL(rawURL string) string {
	parsedURL, err := url.Parse(rawURL) // Parse URL into components
	if err != nil {                     // Handle parsing error
		log.Println(err) // Log the error
		return ""        // Return empty string to indicate invalid URL
	}
	host := parsedURL.Hostname() // Get domain name from parsed URL
	return host                  // Return extracted domain name
}

// Extracts and returns the base name (file name) from the URL path
func getFileNameOnly(content string) string {
	return path.Base(content) // Return last segment of the path
}

// Converts a raw URL into a safe filename by cleaning and normalizing it
func urlToFilename(rawURL string) string {
	lowercaseURL := strings.ToLower(rawURL)       // Convert to lowercase for normalization
	ext := getFileExtension(lowercaseURL)         // Get file extension (e.g., .pdf or .zip)
	baseFilename := getFileNameOnly(lowercaseURL) // Extract base file name

	nonAlphanumericRegex := regexp.MustCompile(`[^a-z0-9]+`)                 // Match everything except a-z and 0-9
	safeFilename := nonAlphanumericRegex.ReplaceAllString(baseFilename, "_") // Replace invalid chars

	collapseUnderscoresRegex := regexp.MustCompile(`_+`)                        // Collapse multiple underscores into one
	safeFilename = collapseUnderscoresRegex.ReplaceAllString(safeFilename, "_") // Normalize underscores

	if trimmed, found := strings.CutPrefix(safeFilename, "_"); found { // Trim starting underscore if present
		safeFilename = trimmed
	}

	var invalidSubstrings = []string{"_pdf", "_zip"} // Remove these redundant endings

	for _, invalidPre := range invalidSubstrings { // Iterate over each unwanted suffix
		safeFilename = removeSubstring(safeFilename, invalidPre) // Remove it from file name
	}

	safeFilename = safeFilename + ext // Add the proper file extension

	return safeFilename // Return the final sanitized filename
}

// Replaces all instances of a given substring from the original string
func removeSubstring(input string, toRemove string) string {
	result := strings.ReplaceAll(input, toRemove, "") // Replace all instances
	return result                                     // Return the result
}

// Returns the extension of a given file path (e.g., ".pdf")
func getFileExtension(path string) string {
	return filepath.Ext(path) // Extract and return file extension
}

// Checks if a file exists and is not a directory
func fileExists(filename string) bool {
	info, err := os.Stat(filename) // Attempt to get file stats
	if err != nil {
		return false // Return false if file doesn't exist or error occurred
	}
	return !info.IsDir() // Return true only if it's not a directory
}

// Downloads and writes a PDF file from the URL to the specified directory
func downloadPDF(finalURL, outputDir string) bool {
	filename := strings.ToLower(urlToFilename(finalURL)) // Generate sanitized filename
	filePath := filepath.Join(outputDir, filename)       // Build full path

	if fileExists(filePath) { // Skip if already downloaded
		log.Printf("File already exists, skipping: %s", filePath)
		return false
	}

	client := &http.Client{Timeout: 3 * time.Minute} // Create HTTP client with 3-minute timeout to avoid hanging

	resp, err := client.Get(finalURL) // Perform HTTP GET request to download the file
	if err != nil {                   // Check if an error occurred during request
		log.Printf("Failed to download %s: %v", finalURL, err) // Log the error with context
		return false                                           // Exit function if request failed
	}
	defer resp.Body.Close() // Ensure the response body is closed after reading

	if resp.StatusCode != http.StatusOK { // Check for HTTP 200 OK status
		log.Printf("Download failed for %s: %s", finalURL, resp.Status) // Log failure reason
		return false                                                    // Exit if status is not OK
	}

	contentType := resp.Header.Get("Content-Type")         // Retrieve the content type from HTTP headers
	if !strings.Contains(contentType, "application/pdf") { // Ensure it's a PDF
		log.Printf("Invalid content type for %s: %s (expected application/pdf)", finalURL, contentType)
		return false // Skip if it's not a PDF
	}

	var buf bytes.Buffer                     // Create buffer to temporarily hold the file data
	written, err := io.Copy(&buf, resp.Body) // Copy response body into buffer
	if err != nil {                          // Handle error while reading response
		log.Printf("Failed to read PDF data from %s: %v", finalURL, err)
		return false
	}
	if written == 0 { // If nothing was read (empty file)
		log.Printf("Downloaded 0 bytes for %s; not creating file", finalURL)
		return false
	}

	out, err := os.Create(filePath) // Create file on disk at the specified location
	if err != nil {                 // Handle file creation error
		log.Printf("Failed to create file for %s: %v", finalURL, err)
		return false
	}
	defer out.Close() // Ensure file is closed after writing

	if _, err := buf.WriteTo(out); err != nil { // Write buffer contents to file
		log.Printf("Failed to write PDF to file for %s: %v", finalURL, err)
		return false
	}

	log.Printf("Successfully downloaded %d bytes: %s → %s", written, finalURL, filePath) // Log successful download
	return true                                                                          // Return success
}

// Checks if a directory exists at the given path
func directoryExists(path string) bool {
	directory, err := os.Stat(path) // Get file or directory info
	if err != nil {
		return false // If error, assume directory doesn't exist
	}
	return directory.IsDir() // Return true if it's a directory
}

// Creates a directory with the given permissions if it doesn't exist
func createDirectory(path string, permission os.FileMode) {
	err := os.Mkdir(path, permission) // Attempt to create the directory
	if err != nil {
		log.Println(err) // Log error if creation fails (e.g., already exists)
	}
}

// Checks if a given URI string is a valid HTTP URL format
func isUrlValid(uri string) bool {
	_, err := url.ParseRequestURI(uri) // Try to parse the string as URL
	return err == nil                  // Return true only if no error occurs
}

// Removes duplicates from a string slice while preserving original order
func removeDuplicatesFromSlice(slice []string) []string {
	check := make(map[string]bool)  // Create map to track unique entries
	var newReturnSlice []string     // Final slice without duplicates
	for _, content := range slice { // Loop over each item in the original slice
		if !check[content] { // If not already added
			check[content] = true                            // Mark as seen
			newReturnSlice = append(newReturnSlice, content) // Append to final result
		}
	}
	return newReturnSlice // Return cleaned slice
}

// Extracts all URLs ending in .pdf found in href attributes from given HTML content
func extractPDFUrls(text string) []string {
	// Split the input into fields using whitespace
	fields := strings.Fields(text)

	// Slice to store valid URLs
	var urlsFound []string

	// Loop through each word and test if it's a valid URL
	for _, word := range fields {
		parsed, err := url.ParseRequestURI(word) // Use Go's built-in URL parser
		if err == nil && parsed.Scheme != "" && parsed.Host != "" {
			urlsFound = append(urlsFound, word) // Add valid URL to the result slice
		}
	}

	return urlsFound // Return the collected URLs
}
