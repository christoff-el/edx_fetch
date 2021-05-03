# edx_fetch

### Prerequisites
Needs Selenium + Chrome driver, see here to install: https://selenium-python.readthedocs.io/installation.html#drivers

Should be 
- pip install selenium
- download the chrome driver
- add the location of the driver to your PATH


### Setup

In fetcher.py, enter the list of courses to process
e.g.
COURSES = [
    'MITx+14.100x+1T2021'
]

You can get the course name by loading it on the edx site, and taking the MITx... part from the URL,

e.g. https://learning.edx.org/course/course-v1:MITx+14.100x+1T2021/home


### Running it
```bash
python fetcher.py
```

It will open up a chrome window, and stop at the page "you need to be signed in to view this course".
Click sign in and enter your login.

As soon as it is logged in it will start to navigate to each problem set and collect the questions, don't touch anything.

Eventually a html file will be put in the output directory.


