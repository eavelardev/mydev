const { Builder, By, until } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');
const cheerio = require('cheerio');
const createCsvWriter = require('csv-writer').createObjectCsvWriter;

function extractMetadata(metadataText) {
    if (!metadataText) return ['', '', ''];
    const parts = metadataText.split(' · ');
    const level = parts[0] || '';
    const type_ = parts[1] || '';
    const duration = parts[2] || '';
    return [level, type_, duration];
}

function convertReviewsToNumeric(reviewsText) {
    if (!reviewsText) return 0;
    const match = reviewsText.match(/(\d+(?:\.\d+)?)(K|M)/);
    if (match) {
        const num = parseFloat(match[1]);
        const unit = match[2];
        if (unit === 'K') return Math.floor(num * 1000);
        if (unit === 'M') return Math.floor(num * 1000000);
    }
    const numMatch = reviewsText.match(/(\d+)/);
    if (numMatch) return parseInt(numMatch[1], 10);
    return 0;
}

function cleanSkills(skillsText) {
    if (skillsText.startsWith("Skills you'll gain:")) {
        return skillsText.slice("Skills you'll gain:".length).trim();
    }
    return skillsText.trim();
}

function extractCourseInfo(htmlContent) {
    const $ = cheerio.load(htmlContent);
    const courses = [];
    const courseCards = $('div.cds-ProductCard-base');
    console.log(`Found ${courseCards.length} course cards`);

    courseCards.each((index, card) => {
        const course = {};

        // Title
        const titleElem = $(card).find('h3.cds-CommonCard-title');
        course.title = titleElem.text().trim() || '';

        // Partner
        const partnerElem = $(card).find('p.cds-ProductCard-partnerNames');
        course.partner = partnerElem.text().trim() || '';

        // Rating
        const ratingElem = $(card).find('span.css-4s48ix');
        course.rating = ratingElem.text().trim() || '-';

        // Reviews
        let reviews = '';
        if (ratingElem.length) {
            const nextElem = ratingElem.next('div.css-vac8rf');
            if (nextElem.length && nextElem.text().toLowerCase().includes('reviews')) {
                reviews = nextElem.text().trim();
            }
        }
        course.reviews = convertReviewsToNumeric(reviews);

        // Skills
        const skillsDiv = $(card).find('div.cds-CommonCard-bodyContent');
        let skills = '';
        if (skillsDiv.length) {
            const skillsP = skillsDiv.find('p.css-vac8rf');
            if (skillsP.length) {
                skills = skillsP.text().trim().replace("Skills you'll gain: ", "");
            }
        }
        course.skills = cleanSkills(skills);

        // Metadata (level, type, duration)
        const metadataDiv = $(card).find('div.cds-CommonCard-metadata');
        let metadata = '';
        if (metadataDiv.length) {
            const metadataP = metadataDiv.find('p');
            if (metadataP.length) {
                metadata = metadataP.text().trim();
            }
        }
        const [level, type_, duration] = extractMetadata(metadata);
        course.level = level;
        course.type = type_;
        course.duration = duration;

        // URL
        const linkElem = $(card).find('a.cds-CommonCard-titleLink');
        if (linkElem.length && linkElem.attr('href')) {
            const href = linkElem.attr('href');
            course.url = 'https://www.coursera.org' + href;
        } else {
            course.url = '';
        }

        // Coursera Plus
        const plusElem = $(card).find('div[data-testid="product-card-coursera-plus"]');
        course.plus = plusElem.length ? 'plus' : '-';

        // Degree
        const degreeElem = $(card).find('p.css-ls7ln4');
        course.degree = (degreeElem.length && degreeElem.text().includes('Build toward a degree')) ? 'degree' : '-';

        courses.push(course);
    });

    return courses;
}

function saveToCsv(courses, outputFile, uniqueSkills) {
    if (!courses.length) {
        console.log('No courses found.');
        return;
    }

    const fieldnames = ['partner', 'title', 'plus', 'level', 'type', 'duration', 'degree', 'rating', 'reviews', 'url', ...uniqueSkills];

    const csvWriter = createCsvWriter({
        path: outputFile,
        header: fieldnames.map(name => ({ id: name, title: name }))
    });

    const records = courses.map(course => {
        const courseSkills = course.skills ? course.skills.split(',').map(s => s.trim()) : [];
        const record = { ...course };
        uniqueSkills.forEach(skill => {
            record[skill] = courseSkills.includes(skill) ? skill : '';
        });
        delete record.skills;
        return record;
    });

    csvWriter.writeRecords(records).then(() => {
        console.log(`Extracted ${courses.length} courses and saved to ${outputFile}`);
    });
}

async function main() {
    const options = new chrome.Options();
    options.addArguments('--headless=new', '--window-size=1080,1920', '--no-sandbox', '--disable-dev-shm-usage');

    const driver = await new Builder().forBrowser('chrome').setChromeOptions(options).build();

    try {
        await driver.get('https://www.coursera.org/search?productTypeDescription=Professional%20Certificates');

        // Wait for initial content to load
        await driver.wait(until.elementsLocated(By.className('cds-ProductCard-base')), 10000);

        // Scroll to load all courses
        let lastHeight = await driver.executeScript('return document.body.scrollHeight');
        while (true) {
            await driver.executeScript('window.scrollTo(0, document.body.scrollHeight);');
            await driver.sleep(1000);
            const newHeight = await driver.executeScript('return document.body.scrollHeight');
            if (newHeight === lastHeight) break;
            lastHeight = newHeight;
        }

        const htmlContent = await driver.getPageSource();

        const courses = extractCourseInfo(htmlContent);

        // Collect unique skills
        const uniqueSkills = new Set();
        courses.forEach(course => {
            if (course.skills) {
                course.skills.split(',').forEach(skill => uniqueSkills.add(skill.trim()));
            }
        });
        const uniqueSkillsArray = Array.from(uniqueSkills).sort();

        const outputFile = 'coursera_courses.csv';
        saveToCsv(courses, outputFile, uniqueSkillsArray);

    } finally {
        await driver.quit();
    }
}

if (require.main === module) {
    main().catch(console.error);
}

module.exports = { extractMetadata, convertReviewsToNumeric, cleanSkills, extractCourseInfo, saveToCsv };