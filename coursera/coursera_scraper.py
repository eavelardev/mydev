import re
import csv
from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
import time

def extract_metadata(metadata_text):
    if not metadata_text:
        return '', '', ''
    parts = metadata_text.split(' · ')
    level = parts[0] if len(parts) > 0 else ''
    type_ = parts[1] if len(parts) > 1 else ''
    duration = parts[2] if len(parts) > 2 else ''
    return level, type_, duration

def convert_reviews_to_numeric(reviews_text):
    if not reviews_text:
        return 0

    match = re.search(r'(\d+(?:\.\d+)?)(K|M)', reviews_text)
    if match:
        num = float(match.group(1))
        unit = match.group(2)
        if unit == 'K':
            return int(num * 1000)
        elif unit == 'M':
            return int(num * 1000000)

    match = re.search(r'(\d+)', reviews_text)
    if match:
        return int(match.group(1))
    return 0

def clean_skills(skills_text):
    if skills_text.startswith("Skills you'll gain:"):
        return skills_text[len("Skills you'll gain:"):].strip()
    return skills_text.strip()

def extract_course_info(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    courses = []
    course_cards = soup.select('ul.cds-9.css-5t8l4v.cds-10 li')
    print(f"Found {len(course_cards)} course cards")
    
    for card in course_cards:
        course = {}
        
        # Title
        title_elem = card.find('h3', class_='cds-CommonCard-title')
        course['title'] = title_elem.get_text(strip=True) if title_elem else ''
        
        # Partner
        partner_elem = card.find('p', class_='cds-ProductCard-partnerNames')
        course['partner'] = partner_elem.get_text(strip=True) if partner_elem else ''
        
        # Rating
        rating_elem = card.find('span', class_='css-4s48ix')
        course['rating'] = rating_elem.get_text(strip=True) if rating_elem else '-'
        
        # Reviews
        rating_elem = card.find('span', class_='css-4s48ix')
        if rating_elem:
            # Find the next div with css-vac8rf after the rating
            next_elem = rating_elem.find_next('div', class_='css-vac8rf')
            if next_elem and 'reviews' in next_elem.get_text().lower():
                course['reviews'] = next_elem.get_text(strip=True)
            else:
                course['reviews'] = ''
        else:
            course['reviews'] = ''

        course['reviews'] = convert_reviews_to_numeric(course['reviews'])
        
        # Skills
        skills_div = card.find('div', class_='cds-CommonCard-bodyContent')
        if skills_div:
            skills_p = skills_div.find('p', class_='css-vac8rf')
            if skills_p:
                course['skills'] = skills_p.get_text(strip=True).replace("Skills you'll gain: ", "")
            else:
                course['skills'] = ''
        else:
            course['skills'] = ''

        course['skills'] = clean_skills(course['skills'])
        
        # Metadata (level, type, duration)
        metadata_div = card.find('div', class_='cds-CommonCard-metadata')
        if metadata_div:
            metadata_p = metadata_div.find('p')
            metadata = metadata_p.get_text(strip=True) if metadata_p else ''
        else:
            metadata = ''

        level, type_, duration = extract_metadata(metadata)
        course['level'] = level
        course['type'] = type_
        course['duration'] = duration

        # URL (from the link)
        link_elem = card.find('a', class_='cds-CommonCard-titleLink')
        if link_elem and 'href' in link_elem.attrs:
            href = str(link_elem['href'])
            course['url'] = '=HYPERLINK("' + 'https://www.coursera.org' + href + '", "url")'
        else:
            course['url'] = ''

        # Degree
        degree_elem = card.find('p', class_='css-ls7ln4')
        course['degree'] = 'degree' if degree_elem and 'Build toward a degree' in degree_elem.get_text() else '-'

        # AI Skills
        elems = card.find_all('span', class_='css-1ast7yb')
        course['AI skills'] = 'AI skills' if elems and any('AI skills' in elem.get_text() for elem in elems) else '-'

        # New
        course['new'] = 'new' if elems and any('New' in elem.get_text() for elem in elems) else '-'
        courses.append(course)
    
    return courses

def save_to_csv(courses, output_file, unique_skills):
    if not courses:
        print("No courses found.")
        return

    fieldnames = ['partner', 'title', 'plus', 'level', 'type', 'duration', 'degree', 'AI skills', 'new', 'rating', 'reviews', 'url'] + unique_skills

    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for course in courses:
            # Add skill columns
            course_skills = set(skill.strip() for skill in course['skills'].split(',')) if course['skills'] else set()
            for skill in unique_skills:
                course[skill] = skill if skill in course_skills else ''

            del course['skills']
            writer.writerow(course)


def get_html_content(url):
    print(url)

    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    # options.add_argument("--window-size=1920,1080")
    # options.add_argument("--window-size=1280,720")
    options.add_argument("--window-size=1080,1920")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)
    driver.get(url)

    WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'cds-ProductCard-base')))

    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(0.5)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    html_content = driver.page_source
    driver.quit()

    return html_content

if __name__ == "__main__":

    language = "English"
    url_format = 'https://www.coursera.org/search?'
    url_format += f'language={language}&'
    url_format += 'isPartOfCourseraPlus={}&'
    url_format += 'productTypeDescription=Professional%20Certificates&'
    url_format += 'productTypeDescription=Specializations&'
    url_format += 'sortBy=NEW'

    output_file = 'coursera_courses.csv'

    plus = 'true'
    html_content = get_html_content(url_format.format(plus))
    courses_plus = extract_course_info(html_content)
    for course in courses_plus:
        course['plus'] = 'plus'

    plus = 'false'
    html_content = get_html_content(url_format.format(plus))
    courses_non_plus = extract_course_info(html_content)
    for course in courses_non_plus:
        course['plus'] = '-'

    courses = courses_plus + courses_non_plus
    
    # Collect unique skills
    unique_skills = set()
    for course in courses:
        if course['skills']:
            skills_list = [skill.strip() for skill in course['skills'].split(',')]
            unique_skills.update(skills_list)
    
    unique_skills = sorted(list(unique_skills))
    
    save_to_csv(courses, output_file, unique_skills)
    
    print(f"Extracted {len(courses)} courses and saved to {output_file}")