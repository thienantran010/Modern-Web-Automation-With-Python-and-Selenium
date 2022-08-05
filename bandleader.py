from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from time import sleep, ctime
from collections import namedtuple
from threading import Thread
from os.path import isfile
import csv

BANDCAMP_FRONTPAGE = 'https://bandcamp.com'

class BandLeader():

    TrackRec = namedtuple('TrackRec', [
    'title', 
    'artist',
    'artist_url', 
    'album',
    'album_url', 
    'timestamp'  # When you played it
])
    def __init__(self, cvspath=None):

        # Create a headless browser
        opts = Options()
        #opts.headless = True
        self.driver = Firefox(options = opts)
        self.driver.get(BANDCAMP_FRONTPAGE)

        # Track list related state
        self._current_track_number = 1
        self.track_list = []
        self.tracks()

        # State for the database
        self.database = []
        self._current_track_record = None

        # Database csv file path
        self.database_path = cvspath
        
        # Load database from disk if possible
        if self.database_path and isfile(self.database_path):
            with open(self.database_path, newline='') as dbfile:
                dbreader = csv.reader(dbfile)
                next(dbreader)   # To ignore the header line
                self.database = [BandLeader.TrackRec._make(rec) for rec in dbreader]
        else:
            self.database_path = '/home/ttran/web_scraping_bandcamp/record_log.csv'

        # Database maintenance thread
        self.thread = Thread(target=self._maintain)
        self.thread.daemon = True   # Kills the thread with the main process
        self.thread.start()

        self.tracks()

    # A new save_db() method
    def save_db(self):
        with open(self.database_path,'w',newline='') as dbfile:
            dbwriter = csv.writer(dbfile)
            dbwriter.writerow(list(BandLeader.TrackRec._fields))
            for entry in self.database:
                dbwriter.writerow(list(entry))
            
    def _maintain(self):
        while True:
            self._update_db()
            sleep(5)   # Check every 20 seconds
    
    def _update_db(self):
        try:
            check = (self._current_track_record is not None and
                    (len(self.database) == 0 or 
                    self.database[-1] != self._current_track_record) and BandLeader.playing_item(self.driver))
            
            if check:
                self.database.append(self._current_track_record)
                self.save_db()
        
        except Exception as e:
            print('error while updating the db: {}'.format(e))

    def print_db(self):
        with open(self.database_path, newline='') as dbfile:
            dbreader = csv.reader(dbfile)
            next(dbreader)   # To ignore the header line
            for rec in dbreader:
                print(rec)
    # When there is no difference in x-position, the animation has stopped.
    def animation_finished(driver):
        on_screen_item = driver.find_element(By.CSS_SELECTOR, '.result-current .discover-item')
        previous_x = on_screen_item.location['x']
        current_x = None

        while current_x != previous_x:
            previous_x = current_x
            current_x = on_screen_item.location['x']
        
        return True

    def tracks(self):

        # uses wait instead of time.sleep
        WebDriverWait(self.driver, timeout=10).until(BandLeader.animation_finished)
        discover_items = self.driver.find_elements(By.CLASS_NAME, 'discover-item')
        self.track_list = [item for item in discover_items if item.is_displayed()]

        #prints tracks
        for (i,track) in enumerate(self.track_list):
            print('[{}]'.format(i+1))
            lines = track.text.split('\n')
            print('Album  : {}'.format(lines[0]))
            print('Artist : {}'.format(lines[1]))
            if len(lines) > 2:
                print('Genre  : {}'.format(lines[2]))
        
        #for testing purposes. separates multiple calls to tracks
        print('---------------------------------------------------')
    
    #clicks to next page, which has 8 other tracks
    def next_page(self):
        next_btn = self.driver.find_element(By.LINK_TEXT, 'next')
        next_btn.click()
        self.tracks()

    # prints all page buttons (?)
    def catalog_pages(self):
        print('PAGES')
        for btn in self.driver.find_elements(By.CLASS_NAME, 'item-page'):
            print(btn.text)
        print('')
    
    # to go to tracks on other pages
    def more_tracks(self, page='next'):
        tracks_page_btn = self.driver.find_element(By.LINK_TEXT, str(page))

        if tracks_page_btn:
            tracks_page_btn.click()
            self.tracks()
    
    # play song
    def play(self, track=None):

        # makes sure we don't stop a playing song
        if BandLeader.playing_item(self.driver):
            print("There is already a song playing! Use pause to stop the song.")
        
        elif track is None:
            self.driver.find_element(By.CLASS_NAME, 'playbutton').click()
        elif type(track) is int and track <= len(self.track_list) and track >= 1:

            self._current_track_number = track
            self.track_list[self._current_track_number - 1].click()
    
        # using wait instead of time.sleep
        WebDriverWait(self.driver, timeout=5).until(BandLeader.playing_item)
        self._current_track_record = self.playing_item_packaged()

    # play next track
    def play_next(self):
        if self._current_track_number < len(self.track_list):
            self.play(self._current_track_number + 1)
        else:
            self.more_tracks()
            self.play(1)
    
    # get the song that's currently playing
    def playing_item(driver):
        try:
            return driver.find_element(By.CLASS_NAME, 'playing')
        except:
            return None

    # currently_playing function but named as playing_item_packaged
    def playing_item_packaged(self):
        try:
            if self.playing_item:
                title = self.driver.find_element(By.CLASS_NAME, 'title').text
                album_detail = self.driver.find_element(By.CSS_SELECTOR,'.detail-album > a')
                album_title = album_detail.text
                album_url = album_detail.get_attribute('href').split('?')[0]
                artist_detail = self.driver.find_element(By.CSS_SELECTOR,'.detail-artist > a')
                artist = artist_detail.text
                artist_url = artist_detail.get_attribute('href').split('?')[0]
                return BandLeader.TrackRec(title, artist, artist_url, album_title, album_url, ctime())
        except Exception as e:
            print('there was an error: {}'.format(e))

        return None

    def pause(self):
        item_playing = BandLeader.playing_item(self.driver)
        if item_playing:
            self.driver.find_element(By.CLASS_NAME, 'playbutton').click()
        else:
            print("There is no song playing. Use play to play a song.")

    #quit driver
    def quit(self):
        self.driver.quit()

# to test
if __name__ == "__main__":
    test_run = BandLeader()
    try:
        test_run.play(1)
        sleep(10)
        test_run.pause()
        test_run.more_tracks(200)
        test_run.play(1)
        sleep(10)
        test_run.print_db()
        test_run.quit()
    except Exception as e:
        print(e)
        test_run.quit()