import json
import psycopg2
import requests
import configparser

class NytApi:
    """
    This class handles the api requests to the NewYork Times Apis as well as storing the results in a PosgreSQL Table.
    Currently, it is only tested for the Most Popular and Top Stories API. Others might result in unknown errors.
    Make sure to set up the config.ini properly before running this script.
    """

    # read config.ini
    config = configparser.ConfigParser()
    config.read("config.ini")

    def __init__(self) -> None:
        """
        The class is instantiated by the defined paths in the config.ini.
        """

        # get list of paths to iterate through
        self.request_urls = []
        for request_path in self.config.get("Api", "paths").split("\n"):
            self.request_urls.append(f"https://api.nytimes.com/svc/{request_path}.json?api-key={self.config.get('Api', 'key')}")

    def run(self):
        for self.request_url in self.request_urls:
            self.get_data()
            self.store_data()
            self.store_data()

    def get_data(self):
        """
        This method grabs the data and saves the object containing the server response.
        """
        # get response
        response = requests.get(self.request_url)

        # no return in case of error
        if response.status_code != 200:
            print(f"Data could not be fetched!\nUrl: {self.request_url}\nStatus Code: {response.status_code}")

        self.response = response

    def store_data(self):
        """
        This method stores the response data in the PosgreSQL Table.
        """
        # create db connection

        if self.response.status_code != 200:
            print("There is no stored response!")
            return

        conn = psycopg2.connect(host=self.config.get('Database', 'host'),
                                port=self.config.get('Database', 'port'),
                                database=self.config.get('Database', 'db'),
                                user=self.config.get('Database', 'user'),
                                password=self.config.get('Database', 'pass'),
                                connect_timeout=3)
        cur = conn.cursor()

        # create result table if it not already exists
        create_result_table = f"CREATE TABLE if NOT EXISTS ds22m029_nyt ("f"url VARCHAR(2048), " \
                                                                          f"id SERIAL, " \
                                                                          f"result JSONB, " \
                                                                          f"created_at TIMESTAMPTZ NOT NULL DEFAULT NOW());"
        cur.execute(create_result_table)
        conn.commit()

        # drop historical results if not defined otherwise
        if self.config.get("Database", "drop_history"):
            cur.execute(f"DELETE FROM ds22m029_nyt WHERE url = '{self.request_url.split('?')[0]}';")
            conn.commit()

        # store newest results
        body = self.response.json()
        for result in body["results"]:
            insert_result = f"INSERT INTO ds22m029_nyt (url, result, created_at) VALUES (%s, %s, NOW());"
            cur.execute(insert_result, (self.request_url.split("?")[0], json.dumps(result)))

        # reset sequence so that next time the first result of another api url request gets 1
        cur.execute("ALTER SEQUENCE ds22m029_nyt_id_seq RESTART WITH 1;")
        conn.commit()
        conn.close()

if __name__ == "__main__":
    api = NytApi().run()