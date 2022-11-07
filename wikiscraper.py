import requests
from bs4 import BeautifulSoup
import logging
from urllib.parse import urljoin
from itertools import chain

from concurrent.futures import ThreadPoolExecutor

from db import WikiDB

class PageCrawler:
    '''
    Page crawler class is responsable for crawling a individual wikipedia page,
    getting the paragraph contents, storing it and then searching the next links to crawl.
    '''

    # Class attribute to keep track of total number of crawled pages
    total_pages_crawled = 0

    # Class attribute to keep track of total number of paragraphs collected
    total_paragraphs = 0

    
    @classmethod
    def get_class_logger(cls):
        
        # If logger is already defined for class returns it
        if hasattr(cls, 'logger'):
            return cls.logger
        
        # Name of class will be use to identify logger, in order to not affect other loggers that may already exist.
        logger_name = cls.__name__
        
        FORMAT = f'{logger_name} %(asctime)s Thread-%(thread)d:\n%(message)s\n'
        logging.basicConfig(format=FORMAT)
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)
        
        cls.logger = logger
    
    def __init__(self, link: str, tag: str) -> None:
        '''
        link: Link of the page that will be crawled
        tag: Category that the paragraph will be stored as
        '''
        
        self.link = link
        self.tag = tag
        
        # domain of wikipedia, will be use to form absolute url's with relative url's in the page
        self.domain = 'https://en.wikipedia.org'
        
        # This is the id of the div that the main content of wikipedia page is in
        self.id_content_div = 'mw-content-text'
        
        self.get_class_logger()
    
    def get_page_content(self) -> None:
        '''
        Receive link of wikipedia page as argument, then collect the content of the page
        returning a BeautifulSoup object
        '''
        
        self.logger.debug(f'Getting content of page {self.link}')
        response = requests.get(self.link)
        
        if response.ok:
            self.logger.debug(f'Content collected with success: {self.link}')
        else:
            code = response.status_code
            self.logger.error(f'Error ({code}) getting content: {self.link}')
            self.logger.debug(response.text)
            return
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Store soup as instance attribute
        self.soup = soup
        
        
    def get_content_paragraphs(self) -> list:
        '''
        Get all paragraphs (p tags) in the main content div of the page (id = mw-content-text')
        Returns a list containing the text for each paragraph
        '''
        
        # Getting content div as BS tag
        self.content_div = self.soup.find_all("div", {"id": self.id_content_div})[0]
        
        p_tags = self.content_div.find_all('p')
        
        paragraphs = [p.text for p in p_tags]
        
        self.logger.debug(f'{len(paragraphs)} paragraphs found: {self.link}')
        
        return paragraphs
    
    def filter_new_urls(self, urls):
        
        # Remove None and empty strings
        urls = [url for url in urls if url]
        
        # Check if it is a wikipedia url, since all articles have wiki/ in the url
        urls = [url for url in urls if 'wiki/' in url]
        
        # The collon after the wiki/ indicates another kind of resource, like Files, Categories, but not articles
        urls = [url for url in urls if ':' not in url.split('wiki/')[-1]]
        
        # Add domain to the relatives urls to make them absolute
        urls = [urljoin(self.domain, url) for url in urls]
        
        return urls
        
    def get_links_to_crawl(self) -> list[tuple]:
        
        #
        a_tags = self.content_div.find_all('a')
        
        next_urls = [a.get('href') for a in a_tags]
        
        next_urls = self.filter_new_urls(next_urls)
        
        # Add tag to links
        next_urls_tags = [(url, self.tag) for url in next_urls]
    
        return next_urls_tags

    def filter_paragraphs(self, paragraphs: list) -> list:
        '''
        Methods to select and discard unwanted paragraphs
        '''

        # Remove paragraphs with less than 10 characters
        # This will include empty and single character paragraphs.
        paragraphs = [p for p in paragraphs if len(p) >= 10]

        # Remove paragraphs with less than 3 words
        paragraphs = [p for p in paragraphs if len(p.split(' ')) >= 3]

        return paragraphs


    def save_paragraphs_on_db(self, paragraphs: list) -> None:
        db_conn = WikiDB()

        for paragraph in paragraphs:
            infos = {
            'paragraph':paragraph,
            'url': self.link,
            'tag': self.tag,
            }

            db_conn.add_record(infos)
    
    def crawl(self) -> list[tuple]:
        '''
        Function that executes pipeline of collecting the paragraphs
        '''
        
        self.get_page_content()
        
        paragraphs = self.get_content_paragraphs()

        paragraphs = self.filter_paragraphs(paragraphs)
        
        self.save_paragraphs_on_db(paragraphs)
        
        next_urls_tags = self.get_links_to_crawl()

        # Update class level information about crawled pages and paragraphs
        PageCrawler.total_pages_crawled += 1
        PageCrawler.total_paragraphs += len(paragraphs)

        return next_urls_tags

class CrawlingManager:
    '''
    This class is responsable for handling the crawling process, by getting 
    '''
    
    def __init__(self, base_links_and_tags: list[tuple, tuple]) -> None:
        self.base_links_and_tags = base_links_and_tags

        # Create logger

        logger_name = __name__
        FORMAT = f'{logger_name} %(asctime)s :\n%(message)s\n'
        logging.basicConfig(format=FORMAT)
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)

        self.logger = logger

        # This attribute will store url already crawled, in order to avoid repeated information
        self.crawled_urls = []

    def filter_urls(self, links_and_tags: list[tuple, tuple]) -> list[tuple, tuple]:
        '''
        Remove already crawled urls, and repeated ones
        '''

        initial_length = len(links_and_tags)

        links_and_tags = [
            link_and_tag for link_and_tag in links_and_tags if link_and_tag[0] not in self.crawled_urls
            ]

        links_and_tags = list(set(links_and_tags))

        num_of_removed_urls = initial_length - len(links_and_tags)

        self.logger.info(f'{num_of_removed_urls} URL were filtered for having already being crawled or being repeated')
        
        return links_and_tags


        
    @staticmethod
    def crawl_page(link_tag: tuple) -> list:
        '''
        Functions that will be used in the thread pool, it instantiates the page crawler
        and returns the result (links of the next level).
        '''
        crawler = PageCrawler(link_tag[0], link_tag[1])

        crawler.logger.setLevel(logging.INFO)
        
        next_crawls = crawler.crawl()
        
        return next_crawls
    
    def start_crawling(self, max_level: int = 2) -> None:
        '''
        This method start the process of crawling the url's specified in the init method.
        The level of the page refers to how many pages were navigated to get to the page,
        for example, a base url is level 0, a page crawled for having a link in the base url
        has level 1, etc...
        '''
        links_tags = self.base_links_and_tags
        
        with ThreadPoolExecutor(max_workers=50) as executor:
            
            # This loop will update the links and run until the max level specified in the parameter
            for i in range(max_level):
                self.logger.info(f'Starting level {i}...')

                # Removing repeated urls
                links_tags = self.filter_urls(links_tags)

                self.logger.info(f'{len(links_tags)} urls to be crawled')

                # Generator with next links to be crawled
                result = executor.map(self.crawl_page, links_tags)

                # Keeping record of already crawled urls
                self.crawled_urls += [link_tag[0] for link_tag in links_tags]
                
                # Convert to list to be able to chain inner lists
                result = list(result)
                
                # Chain inner list to make one flat iterator
                links_tags = list(chain(*result))

                self.logger.info(f'Level {i} finished.')
        
        self.logger.info(f'Total pages crawled: {PageCrawler.total_pages_crawled}')
        self.logger.info(f'Total paragraphs collected: {PageCrawler.total_paragraphs}')
        
    
if __name__ == '__main__':
    base_links_and_tags = [
        ('https://en.wikipedia.org/wiki/Mathematics', 'math'),
        ('https://en.wikipedia.org/wiki/History', 'hist'),
        ('https://en.wikipedia.org/wiki/Geography', 'geo')
        ]
    
    c_manager = CrawlingManager(base_links_and_tags)
    
    c_manager.start_crawling(3)