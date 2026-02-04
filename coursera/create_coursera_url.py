url_search = 'https://www.coursera.org/search?'
language = 'English'
plus = 'true'
sort_by = 'NEW'

educators = [
    "IBM",
    "Google",
    "Google Cloud",
    "Microsoft",
    "Amazon Web Services",
    "Meta",
    "Alberta Machine Intelligence Institute",
    "Anthropic"
]

product_type_description = [
    "Professional Certificates",
    "Specializations"
]

educators_query = '&'.join([f'partners={e.replace(" ", "%20")}' for e in educators])
product_type_description_query = '&'.join([f'productTypeDescription={p.replace(" ", "%20")}' for p in product_type_description])

url_parts = [
    f'language={language}',
    f'isPartOfCourseraPlus={plus}',
    product_type_description_query,
    f'sortBy={sort_by}',
    educators_query
]
url = url_search + '&'.join(url_parts)

print(url)