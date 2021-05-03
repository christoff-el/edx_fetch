import re
import time

from selenium.webdriver.support.ui import WebDriverWait

HEAD = '\n'.join(["<head>",
                  "<script src='https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.4/MathJax.js?config=TeX-MML-AM_CHTML' async></script>",
                  "</head>",
                  "<body>\n"])
TAIL = "</body>"

def get_driver():
    from selenium import webdriver
    options = webdriver.ChromeOptions()
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.125 Safari/537.36"
    )
    driver = webdriver.Chrome(options=options)
    return driver

def get_links(driver):
    # Get boxes for each week in the course
    boxes = driver.find_elements_by_css_selector('div[class="pgn-transition-replace-group position-relative"]')

    # Collect the links for each problem set
    links = []
    for box in boxes:
        #lectures in the week
        items = [el for el in box.find_elements_by_css_selector('li') if 'Problem Set ' in el.text]

        for item in items:
            link = item.find_elements_by_css_selector('a')[0]
            links.append(link.get_attribute('href'))

    return links

def process_link(driver, link):
    driver.get(link)

    # Count how many top pages there are
    button_bar = WebDriverWait(driver, 20).until(lambda d:d.find_elements_by_css_selector('div[class="sequence-navigation-tabs d-flex flex-grow-1"'))[0]
    buttons = button_bar.find_elements_by_css_selector('button')

    # Get the questions from each of the pages
    contents = []
    for nn in range(len(buttons)):
        driver.switch_to.default_content()
        button_bar = WebDriverWait(driver, 20).until(lambda d:d.find_elements_by_css_selector('div[class="sequence-navigation-tabs d-flex flex-grow-1"'))[0]
        buttons = button_bar.find_elements_by_css_selector('button')
        button  = buttons[nn]
        button.click()

        frame = WebDriverWait(driver, 20).until(
            lambda d: d.find_elements_by_css_selector('iframe[id="unit-iframe"]')
        )[0]
        driver.switch_to.frame(frame)

        problems = driver.find_elements_by_css_selector('div[class="problems-wrapper"]')
        for problem in problems:
            # Remove the junk at the bottom, and remove any filled-in answers
            content = problem.get_attribute('data-content')
            content = content.split('<span class="status unanswered" id="',1)[0]
            content = content.split('<span class="status incorrect" id=',1)[0]
            content = content.split('<span class="status correct" id=',1)[0]
            content = content.replace('checked="true"', '')
            repls = []
            for cc in re.findall(r'((?=<input type="text").+(?!\/>))', content):
                vv = re.findall(r'(?:value=").*?(?:")', cc)
                repls.extend(vv)

            for vv in repls:
                content = content.replace(vv, '')

            contents.append(content)

    return contents



COURSES = [
    'MITx+14.100x+1T2021'
]

def do_course(course, driver):
    print ('Processing course %s' % course)
    driver.get('https://learning.edx.org/course/course-v1:%s/home' % course)

    # Wait until logged in
    WebDriverWait(driver, 300).until(lambda d: d.find_elements_by_css_selector('div[class="user-dropdown dropdown"]'))

    # Expand all
    expand = WebDriverWait(driver, 20).until(lambda d: d.find_elements_by_css_selector('button[class="btn btn-outline-primary btn-block"]'))[0]
    expand.click()
    time.sleep(3)

    # Links to the problem sets
    links = get_links(driver)
    print('Got %d problem sets' % len(links))

    # Contents of each set
    contents = []
    for link in links:
        link_contents = process_link(driver, link)
        contents.extend(link_contents)

    # Compile to html
    html = (HEAD + '\n\n'.join(contents) + TAIL).encode()

    # Write to output directory
    os.mkdir('output')
    path = 'output/%s.html' % course
    open(path,'wb').write(html.encode())

    print('Wrote %s problems to %s' % (course, path))


def main():
    driver = get_driver()

    for course in COURSES:
        do_course(course, driver)




if __name__ == "__main__":
    main()

