import logging
import os

import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logger = logging.getLogger(__name__)

BASE_URL = 'https://transkribus.eu/TrpServer/rest'
DEFAULT_TIMEOUT = 30  # seconds; applied to every request


class TrkbsClient:
    def __init__(self, user=None, pw=None, timeout=DEFAULT_TIMEOUT):
        self.user = user or os.environ.get('TRANSKRIBUS_USERNAME')
        self.pw = pw or os.environ.get('TRANSKRIBUS_PASSWORD')
        if not self.user or not self.pw:
            raise ValueError('Transkribus credentials not set. Provide user/pw or set env vars.')
        self.timeout = timeout
        self.session = requests.Session()
        login_creds = {'user': self.user, 'pw': self.pw}
        r = self.session.post(f'{BASE_URL}/auth/login', data=login_creds, timeout=self.timeout)
        if r.status_code == 200:
            logger.info('Transkribus login successful (status %s)', r.status_code)
        else:
            logger.debug('Login failed response body: %s', r.text)
            raise Exception(f'Login failed with status {r.status_code}')

    def get_col_ids(self):
        url = f'{BASE_URL}/collections'
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        col_dict = {c['colName']: c['colId'] for c in response.json()['trpCollection']}
        return col_dict

    def get_doc_ids(self, coll_id):
        url = f'{BASE_URL}/collections/{coll_id}/list'
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        doc_dict = {d['title']: d['docId'] for d in response.json()}
        return doc_dict

    def get_page(self, coll_id, doc_id, page_nr, param=None):
        url = f'{BASE_URL}/collections/{coll_id}/{doc_id}/{page_nr}/text'
        if param: url += f'?{param}'
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        return response.text

    def get_pages_stream(self, coll_id, doc_id, page_start, page_end):  # TODO add default for page_start=1
        if page_start > page_end:
            raise ValueError(f'Invalid page range: start ({page_start}) must be <= end ({page_end})')
        for page_nr in range(page_start, page_end + 1):
            yield page_nr, self.get_page(coll_id, doc_id, page_nr)

    def get_page_transcript_ids(self, coll_id, doc_id, page_nr, param=None):
        url = f'{BASE_URL}/collections/{coll_id}/{doc_id}/{page_nr}/list'
        if param: url += f'?{param}'
        response = self.session.get(url, timeout=self.timeout)  # list
        response.raise_for_status()
        return response.json()

    def get_metadata(self, coll_id, doc_id, param=None):
        url = f'{BASE_URL}/collections/{coll_id}/{doc_id}/metadata'
        if param: url += f'?{param}'
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def get_page_nr(self, coll_id, doc_id, param=None):  # TODO refactor as get_page_total
        metadata = self.get_metadata(coll_id, doc_id, param)
        page_nr = metadata.get('nrOfPages')
        return page_nr

    def post_page(self, xml, coll_id, doc_id, page_nr, param=None):
        url = f'{BASE_URL}/collections/{coll_id}/{doc_id}/{page_nr}/text'
        if param: url += f'?{param}'
        xml_bytes = xml.encode('utf-8')
        response = self.session.post(url, data=xml_bytes, timeout=self.timeout)
        response.raise_for_status()
        return response
