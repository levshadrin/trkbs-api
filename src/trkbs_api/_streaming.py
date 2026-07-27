"""Shared page-iteration helpers for the batch drivers.

Every stream driver pages through a document, applies a per-page transform,
logs each change to a timestamped CSV, and POSTs modified pages back. This
module holds that loop once so the individual drivers only supply their
transform and log columns.

It also holds ``iter_pages``, the single progress-bar-wrapped page iterator
shared by every function that walks a page range (read-only queries included).
"""

import csv
import logging
import os
from datetime import datetime

import requests
# tqdm.auto picks the ipywidgets bar in Jupyter/Colab and the terminal bar
# otherwise. The plain tqdm.std bar writes \r to stderr, which notebook
# front-ends render as a new line per update.
from tqdm.auto import tqdm
from tqdm.contrib.logging import logging_redirect_tqdm

logger = logging.getLogger(__name__)


def iter_pages(client, coll_id, doc_id, page_start=1, page_end=None,
               desc=None, progress=True):
    """Yield ``(page_nr, xml)`` over a page range behind a progress bar.

    Resolves ``page_end=None`` to the document length *before* iterating, so the
    bar knows its total and can show a percentage and ETA instead of a bare
    counter. This costs no extra request: ``get_pages_stream`` would otherwise
    make the same ``get_num_pages`` call itself.

    Args:
        client:          authenticated ``TrkbsClient``.
        coll_id, doc_id: Transkribus collection / document IDs.
        page_start, page_end: inclusive page range; ``page_end=None`` runs to the
                         end of the document.
        desc:            progress-bar label.
        progress:        set False to suppress the bar (scripts, CI, nested loops).
    """
    if page_end is None:
        page_end = client.get_num_pages(coll_id, doc_id)

    yield from tqdm(
        client.get_pages_stream(coll_id, doc_id, page_start, page_end),
        total=page_end - page_start + 1,
        desc=desc,
        unit='page',
        disable=not progress,
    )


def run_stream(client, coll_id, doc_id, page_start, page_end,
               transform, fieldnames, output_log_path, continue_on_error=False,
               progress=True):
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
        progress:        set False to suppress the progress bar.

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

        # This loop logs per page; without the redirect each record would break
        # the bar and force it to redraw on a new line.
        with logging_redirect_tqdm():
            pages = iter_pages(client, coll_id, doc_id, page_start, page_end,
                               desc=f'Processing {coll_id}/{doc_id}',
                               progress=progress)
            for page_number, xml in pages:
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
