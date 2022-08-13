import httpx
from bs4 import BeautifulSoup
import pandas as pd

class Scraper:
    def __init__(self) -> None:
        self.url = "https://g12.emis.gov.eg/"
        self.client = httpx.Client()
        self.results_df = pd.DataFrame()

    def getToken(self) -> str:
        r = self.client.get(self.url)
        soup = BeautifulSoup(r, "html.parser")
        token = soup.find("input", type="hidden")
        return token["value"]

    def getResult(self, seat_no: int) -> pd.DataFrame:
        token = self.getToken()
        data = {
            "__RequestVerificationToken": token,
            'SeatingNo': seat_no,
        }
        r = self.client.post(self.url, data=data)
        soup = BeautifulSoup(r, "html.parser")
        result_table = soup.find("div", class_="row no-gutter mb-5")
        parsed_table = pd.read_html(str(result_table))
        return parsed_table
    
    def storeResult(self, seat_no: int) -> None:
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

    def saveToDisk(self):
        pd.to_pickle(self.results_df, "results.pkl")

    def loadFromDisk(self):
        self.results_df = pd.read_pickle("results.pkl")
        return self.results_df
    
    def run(self):
        pass


s = Scraper()
s.storeResult(540017)