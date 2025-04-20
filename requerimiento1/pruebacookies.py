from selenium import webdriver

driver = webdriver.Chrome()
driver.get('https://research-ebsco-com.crai.referencistas.com/c/q46rpe/search/results?q=computational+thinking&autocorrect=y&expanders=thesaurus&expanders=concept&limiters=FT%3AY%2CFT1%3AY&resetPageNumber=true&searchMode=all&searchSegment=all-results')

# Esperar a que cargue, si es necesario
driver.implicitly_wait(10)

# Obtener cookies
cookies = driver.get_cookies()

for cookie in cookies:
    print(cookie['name'], cookie['value'])

driver.quit()

