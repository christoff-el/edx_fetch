import logging
import os
import re
import time
import uuid

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

def get_links(driver, tag):
    # Get boxes for each week in the course
    boxes = driver.find_elements_by_css_selector('div[class="pgn-transition-replace-group position-relative"]')

    # Collect the links for each problem set
    links = []
    for box in boxes:
        #lectures in the week
        items = [el for el in box.find_elements_by_css_selector('li') if tag in el.text]

        for item in items:
            link = item.find_elements_by_css_selector('a')[0]
            links.append(link.get_attribute('href'))

    return links

def get_image(driver, img_url):
    '''Given an images url, return a binary screenshot of it in png format.'''

    driver.get(img_url)

    # Get the dimensions of the browser and image.
    orig_h = driver.execute_script("return window.outerHeight")
    orig_w = driver.execute_script("return window.outerWidth")
    margin_h = orig_h - driver.execute_script("return window.innerHeight")
    margin_w = orig_w - driver.execute_script("return window.innerWidth")
    new_h = driver.execute_script('return document.getElementsByTagName("img")[0].height')
    new_w = driver.execute_script('return document.getElementsByTagName("img")[0].width')

    # Resize the browser window.
    logging.info("Getting Image: orig %sX%s, marg %sX%s, img %sX%s - %s"%(
      orig_w, orig_h, margin_w, margin_h, new_w, new_h, img_url))
    driver.set_window_size(new_w + margin_w, new_h + margin_h)

    # Get the image by taking a screenshot of the page.
    img_val = driver.get_screenshot_as_png()
    # Set the window size back to what it was.
    driver.set_window_size(orig_w, orig_h)

    # Go back to where we started.
    #driver.back()
    return img_val


def process_link(driver, link):
    driver.get(link)

    # Count how many top pages there are
    button_bar = WebDriverWait(driver, 20).until(lambda d:d.find_elements_by_css_selector('div[class="sequence-navigation-tabs d-flex flex-grow-1"'))[0]
    buttons = button_bar.find_elements_by_css_selector('button')

    # Get the questions from each of the pages
    contents = ['<h2>%s</h2>' % driver.title]
    images   = {}
    for nn in range(len(buttons)):
        driver.switch_to.default_content()
        button_bar = WebDriverWait(driver, 20).until(lambda d:d.find_elements_by_css_selector('div[class="sequence-navigation-tabs d-flex flex-grow-1"'))[0]
        buttons = button_bar.find_elements_by_css_selector('button')
        button  = buttons[nn]

        try:
            button.click()
        except Exception as e:
            print(e)
            dropdown = WebDriverWait(driver, 20).until(lambda d:d.find_elements_by_css_selector('div[class="sequence-navigation-dropdown dropdown"]'))[0]
            dropdown.find_elements_by_css_selector('button')[0].click()
            button_bar = WebDriverWait(driver, 20).until(lambda d:d.find_elements_by_css_selector('div[class="w-100 dropdown-menu show"]'))[0]
            buttons = button_bar.find_elements_by_css_selector('button')
            button  = buttons[nn]
            button.click()

        frame = WebDriverWait(driver, 20).until(
            lambda d: d.find_elements_by_css_selector('iframe[id="unit-iframe"]')
        )[0]
        driver.switch_to.frame(frame)

        problems = driver.find_elements_by_css_selector('div[class="problems-wrapper"]')
        for problem in problems:
            content = problem.get_attribute('data-content')

            # Fetch any images
            for img in problem.find_elements_by_css_selector('img'):
                uimg = img.get_attribute('src')
                nimg = '%s.png' % str(uuid.uuid4())
                images[nimg] = uimg
                content = content.replace(uimg.split('courses.mitxonline.mit.edu',1)[-1], nimg)

            # Remove the junk at the bottom, and remove any filled-in answers
            content = content.split('<div class="solution-span">',1)[0]
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

    return contents, images



COURSES = [
    #'MITxT+14.73x+3T2021',
    'MITxT+JPAL102x+3T2021'
]

def do_course(course, driver):
    print ('Processing course %s' % course)
    driver.get('https://courses.mitxonline.mit.edu/learn/course/course-v1:%s/home' % course)

    # Wait until logged in
    WebDriverWait(driver, 300).until(lambda d: d.find_elements_by_css_selector('div[class="user-dropdown dropdown"]'))

    # Expand all
    expand = WebDriverWait(driver, 25).until(lambda d: [
        e for e in d.find_elements_by_css_selector('button[class="btn btn-outline-primary btn-block"]')
        if 'Expand all' in e.text
    ])[0]
    expand.click()
    time.sleep(3)

    # Links to the problem sets
    links = get_links(driver, tag='Problem Set')
    print('Got %d problem sets' % len(links))

    # Links to the exams
    exams = get_links(driver, tag='Exam ')
    print('Got %d exams' % len(exams))

    # Links to Questions
    quest = [l for l in get_links(driver, tag='Questions)') if l not in links and l not in exams]
    print('Got %d question pages' % len(quest))

    # Contents of each set
    contents = []
    images   = {}
    for link in links+quest:
        link_contents, link_images = process_link(driver, link)
        contents.extend(link_contents)
        images.update(link_images)

    exam_contents = []
    for link in exams:
        link_contents, link_images = process_link(driver, link)
        exam_contents.extend(link_contents)
        images.update(link_images)

    for n,d in images.items():
        img = get_image(driver, d)
        open('output/%s' % n, 'wb').write(img)

    # Compile to html
    html_problems = (HEAD + '\n\n'.join(contents) + TAIL).encode()
    html_exams    = (HEAD + '\n\n'.join(exam_contents) + TAIL).encode()

    # Write to output directory
    if not os.path.exists('output'):
        os.mkdir('output')

    for tag, html in zip(['problems','exams'], [html_problems,html_exams]):
        path = 'output/%s-%s.html' % (course, tag)
        open(path,'wb').write(html)
        print('Wrote %s %s to %s' % (course, tag, path))


def main():
    driver = get_driver()

    for course in COURSES:
        do_course(course, driver)




if __name__ == "__main__":
    main()

