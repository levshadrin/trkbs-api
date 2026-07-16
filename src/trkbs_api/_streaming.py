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

import requests
from tqdm import tqdm

logger = logging.getLogger(__name__)


def run_stream(client, coll_id, doc_id, page_start, page_end,
               transform, fieldnames, output_log_path, continue_on_error=False):
    """Page through a document and apply ``transform`` to each page.

    Args:
        client:          authenticated ``TrkbsClient``.
        coll_id, doc_id: Transkribus collection / document IDs.
        page_start, page_end: inclusive page range; ``page_end=None`` streams to
                         the end of the document.
        transform:       callable ``xml -> (updated_xml, diffs)`` where
                         ``diffs`` is a list of dicts (one per changed line).
        fieldnames:      CSV columns; must include ``'page'``. Each diff is
                         augmented with the current page number before writing.
        output_log_path: directory for the changelog CSV (created if missing).
        continue_on_error: if False (default), a failed page POST aborts the run
                         (fail-fast). If True, the failure is logged and recorded
                         and the run continues to the next page.

    Returns:
        The full path of the written changelog CSV.

    Note:
        With the default fail-fast behaviour, pages processed before a failure
        are already committed to Transkribus and logged in the CSV. Fix the cause
        and resume by re-running with ``page_start`` set to the failed page.
    """
    os.makedirs(output_log_path, exist_ok=True)
    date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    logfile_full = os.path.join(output_log_path, f'changelog_{date_str}.csv')

    pages_changed = 0
    lines_changed = 0
    failures = []

    with open(logfile_full, 'w', newline='', encoding='utf-8') as logfile:
        writer = csv.DictWriter(logfile, fieldnames=fieldnames)
        writer.writeheader()

        for page_number, xml in tqdm(client.get_pages_stream(coll_id, doc_id, page_start, page_end)):
            updated_xml, diffs = transform(xml)
            if not diffs:
                continue
            try:
                client.post_page(updated_xml, coll_id, doc_id, page_number)
            except requests.HTTPError:
                failures.append(page_number)
                logger.warning('Page %s failed to upload', page_number)
                if not continue_on_error:
                    raise
                continue
            for diff in diffs:
                writer.writerow({**diff, 'page': page_number})
            pages_changed += 1
            lines_changed += len(diffs)

    logger.info(
        'Stream complete: %s pages changed, %s lines changed, %s failed. Changelog: %s',
        pages_changed, lines_changed, len(failures), logfile_full,
    )
    return logfile_full
