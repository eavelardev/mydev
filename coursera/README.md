# Coursera Scraper (JavaScript)

This is a JavaScript equivalent of the Python `coursera_scraper.py` script. It scrapes course information from Coursera's Professional Certificates search page using Selenium WebDriver and Cheerio for HTML parsing.

## Features

- Scrapes course details including title, partner, rating, reviews, skills, level, type, duration, URL, Coursera Plus status, and degree information.
- Handles dynamic content loading by scrolling to the bottom of the page.
- Exports data to a CSV file with skills as separate columns.

## Prerequisites

- Node.js (version 14 or higher)
- Google Chrome browser
- ChromeDriver (automatically managed by selenium-webdriver)

## Installation

1. Clone or download the repository.
2. Navigate to the project directory.
3. Install dependencies:

   ```bash
   npm install
   ```

## Usage

Run the scraper:

```bash
npm start
```

This will generate a `coursera_courses.csv` file in the current directory with the scraped course data.

## Dependencies

- `selenium-webdriver`: For browser automation
- `cheerio`: For HTML parsing
- `csv-writer`: For CSV file generation

## Notes

- The script runs in headless mode for performance.
- It may take some time to load all courses as it scrolls through the page.
- Ensure you have a stable internet connection as it fetches data from Coursera's website.