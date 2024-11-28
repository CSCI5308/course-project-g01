import math
import sys
import threading
from datetime import datetime
from logging import Logger
from typing import Optional

import git

from MLbackend.src.perspective_analysis import getToxicityPercentage


def author_id_extractor(author: git.Actor):
    id = ""

    if author.email is None:
        id = author.name
    else:
        id = author.email

    id = id.lower().strip()
    return id


def iter_len(obj: iter):
    return sum(1 for _ in obj)


def analyze_sentiments(
    senti, comments, positive_comments, negative_comments, generally_negative, semaphore
):
    with semaphore:
        comment_sentiments = (
            senti.getSentiment(comments, score="scale")
            if len(comments) > 1
            else senti.getSentiment(comments[0])
        )

        comment_sentiments_positive = sum(
            1 for _ in filter(lambda value: value >= 1, comment_sentiments)
        )
        comment_sentiments_negative = sum(
            1 for _ in filter(lambda value: value <= -1, comment_sentiments)
        )

        lock = threading.Lock()
        with lock:
            positive_comments.append(comment_sentiments_positive)
            negative_comments.append(comment_sentiments_negative)

            if comment_sentiments_negative / len(comments) > 0.5:
                generally_negative.append(True)

def get_stats(stat_type: str, logger: Logger, batch_idx: int, batch, batch_participants, senti, batch_comments):
    logger.info(f"Analyzing {stat_type} batch #{batch_idx}")

    # extract data from batch
    count = len(batch)
    participants = list(
        entity["participants"] for entity in batch if len(entity["participants"]) > 0
    )
    batch_participants.append(participants)

    all_comments = list()
    positive_comments = list()
    negative_comments = list()
    generally_negative = list()

    semaphore = threading.Semaphore(15)
    threads = []

    for pr in batch:

        comments = list(
            comment for comment in pr["comments"] if comment and comment.strip()
        )

        # split comments that are longer than 20KB
        split_comments = []
        for comment in comments:

            # calc number of chunks
            byte_chunks = math.ceil(sys.getsizeof(comment) / (20 * 1024))
            if byte_chunks > 1:

                # calc desired max length of each chunk
                chunk_length = math.floor(len(comment) / byte_chunks)

                # divide comment into chunks
                chunks = [
                    comment[i * chunk_length : i * chunk_length + chunk_length]
                    for i in range(0, byte_chunks)
                ]

                # save chunks
                split_comments.extend(chunks)

            else:
                # append comment as-is
                split_comments.append(comment)

        # re-assign comments after chunking
        comments = split_comments

        if len(comments) == 0:
            positive_comments.append(0)
            negative_comments.append(0)
            continue

        all_comments.extend(comments)

        thread = threading.Thread(
            target=analyze_sentiments,
            args=(
                senti,
                comments,
                positive_comments,
                negative_comments,
                generally_negative,
                semaphore,
            ),
        )
        threads.append(thread)


    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    # save comments
    batch_comments.append(all_comments)

    # get comment length stats
    comment_lengths = [len(c) for c in all_comments]

    return generally_negative, count, all_comments, participants, comment_lengths, positive_comments, negative_comments

def get_comment_stats(all_comments, senti, config, logger, batch):
    durations = [(entity["closed_at"] - entity["created_at"]).days for entity in batch]

    comment_sentiments = []
    comment_sentiments_positive = 0
    comment_sentiments_negative = 0

    if len(all_comments) > 0:
        comment_sentiments = senti.getSentiment(all_comments)
        comment_sentiments_positive = sum(
            1 for _ in filter(lambda value: value >= 1, comment_sentiments)
        )
        comment_sentiments_negative = sum(
            1 for _ in filter(lambda value: value <= -1, comment_sentiments)
        )

    toxicity_percentage = getToxicityPercentage(config, all_comments, logger)
    return durations, comment_sentiments, comment_sentiments_positive, comment_sentiments_negative, toxicity_percentage

def create_analysis_batches(batches_pre, created_at: datetime, delta, entity, current_time: datetime):
    batch_date: Optional[datetime] = None

    for date in batches_pre.keys():
        batch_date = date
        if date <= created_at < date + delta:
            # This means we have exceeded the range by 1
            break

    if batch_date is not None:
        batches_pre[batch_date].append(entity)
    else:
        if current_time not in batches_pre.keys():
            batches_pre[current_time] = []
        batches_pre[current_time].append(entity)
    return batches_pre