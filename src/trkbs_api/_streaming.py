"""Shared batch-processing helper for the ``*_stream`` drivers.

Every stream driver pages through a document, applies a per-page transform,
logs each change to a timestamped CSV, and POSTs modified pages back. This
module holds that loop once so the individual drivers only supply their
transform and log columns.
"""

import csv
import logging
import os
from datetime import datetime

from tqdm import tqdm

logger = logging.getLogger(__name__)


def run_stream(client, coll_id, doc_id, page_start, page_end,
               transform, fieldnames, output_log_path):
    """Page through a document and apply ``transform`` to each page.

    Args:
        client:          authenticated ``TrkbsClient``.
        coll_id, doc_id: Transkribus collection / document IDs.
        page_start, page_end: inclusive page range.
        transform:       callable ``xml -> (updated_xml, diffs)`` where
                         ``diffs`` is a list of dicts (one per changed line).
        fieldnames:      CSV columns; must include ``'page'``. Each diff is
                         augmented with the current page number before writing.
        output_log_path: directory for the changelog CSV (created if missing).

    Returns:
        The full path of the written changelog CSV.
    """
    os.makedirs(output_log_path, exist_ok=True)
    date_str = datetime.now().strftime('%d-%m_%H%M%S')
    logfile_full = os.path.join(output_log_path, f'changelog_{date_str}.csv')

    with open(logfile_full, 'w', newline='', encoding='utf-8') as logfile:
        writer = csv.DictWriter(logfile, fieldnames=fieldnames)
        writer.writeheader()

        for page_number, xml in tqdm(client.get_pages_stream(coll_id, doc_id, page_start, page_end)):
            updated_xml, diffs = transform(xml)
            if diffs:
                for diff in diffs:
                    diff['page'] = page_number
                    writer.writerow(diff)
                client.post_page(updated_xml, coll_id, doc_id, page_number)

    logger.info('Changelog written to %s', logfile_full)
    return logfile_full
