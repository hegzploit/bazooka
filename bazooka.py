import atexit
import contextlib
from tqdm import tqdm
import httpx
from bs4 import BeautifulSoup
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
import pandas as pd
import multiprocessing.dummy as mp

class Scraper:
    def __init__(self) -> None:
        self.url = "https://g12.emis.gov.eg/"
        self.client = httpx.Client()
        self.results_df = pd.DataFrame()
        self.failed_numbers = []
        self.token = self.getToken()
        self.status = 0
        self.current_seat_no = 123456
        self.load()


    def getToken(self) -> str:
        r = self.client.get(self.url)
        soup = BeautifulSoup(r, "html.parser")
        token = soup.find("input", type="hidden")
        return token["value"]

    def getResult(self, seat_no: int) -> pd.DataFrame:
        data = {
            "__RequestVerificationToken": self.token,
            'SeatingNo': seat_no,
        }
        r = self.client.post(self.url, data=data)
        self.status = r.status_code
        soup = BeautifulSoup(r, "html.parser")
        result_table = soup.find("div", class_="row no-gutter mb-5")
        parsed_table = pd.read_html(str(result_table))
        return parsed_table
    
    def storeResult(self, seat_no: int) -> None:
        self.current_seat_no = seat_no
        r = self.getResult(seat_no)
        r[0] = r[0].transpose()
        r[0] = r[0].rename(columns=r[0].iloc[0]).drop(r[0].index[0])
        r[0] = r[0].set_index("رقم الجلوس")
        r[1] = r[1].transpose()
        r[1] = r[1].rename(columns=r[1].iloc[0]).drop(r[1].index[0]).set_index(r[0].index)
        r[2] = r[2].transpose()
        r[2] = r[2].rename(columns=r[2].iloc[0]).drop(r[2].index[0]).set_index(r[0].index)
        r_f = pd.concat([r[0], r[1], r[2]], axis=1)
        self.results_df = self.results_df.append(r_f)

    def saveToDisk(self) -> None:
        pd.to_pickle(self.results_df, "results.pkl")
        pd.to_pickle(self.failed_numbers, "failed_numbers.pkl")
        pd.to_pickle(self.current_seat_no, "current_seat_no.pkl")

    def loadFromDisk(self) -> None:
        self.results_df = pd.read_pickle("results.pkl")
        self.failed_numbers = pd.read_pickle("failed_numbers.pkl")
        self.current_seat_no = pd.read_pickle("current_seat_no.pkl")

    # load pickle file if it exists otherwise create a new one
    def load(self):
        try:
            self.loadFromDisk()
        except FileNotFoundError:
            self.saveToDisk()

    def run(self, i):
        seat_num = str(i).zfill(6)
        with contextlib.suppress(Exception):
            self.storeResult(seat_num)
            if self.status == 403:
                self.client.close()
                self.client = httpx.Client()
                self.token = s.getToken()


if __name__ == "__main__":
    s = Scraper()

    @atexit.register
    def exithandler():
        print("saving to disk")
        s.saveToDisk()

    scraping_range = range(int(s.current_seat_no), 999999)
    range_length = len(scraping_range)
    with mp.Pool(500) as p:
        try:
            list(tqdm(p.imap_unordered(s.run, scraping_range, chunksize=16), total=range_length))
            p.close()
            p.join()
            s.saveToDisk()
        except:
            p.terminate()
            p.join()
            s.saveToDisk()
            raise
        