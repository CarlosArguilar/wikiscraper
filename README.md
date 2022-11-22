# wikiscraper

This project features a web crawler to get text from wikipedia articles. Given initial urls, the crawler gets the paragraphs from the page,
store them in a postgres data base, and then get the links in the main content div. This process is repeated concurrently for the links gathered, and for the sake of storing the data
the paragraphs of pages originated from the same source are considered to be from the same subject. The maximum level of the scrapping (the level is how many pages did the scraper had to navigate to get to the current page) is also a parameter.

---------------

## wikiscraper.py
This is the main file and it's the file to be executed to start the script. It contains the classes that have the methods to execute the tasks of the crawler.

### class PageCrawler
This class contains the functionalities to scrap a single page, making the requests, parsing the content, getting the necessary information, and storing it.

### class CrawlingManager
This class is designed to handle the concurrency of the crawling, by storing urls already visited, creating a thread pool to crawl simultaneous pages at the same time, etc.

## **db**
The **db** folder contains the files to make the communication with the database, the connection information and credentials are in the *settings.py* file, 
the class to creating the engine and session to communicate with the db are in the *connection.py* file, and the functionalities regarding the Object Relational Mapper (ORM) from sqlalchemy are in the *orm.py* file.
