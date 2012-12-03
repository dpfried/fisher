from csv import DictReader
from os.path import join
import config

table = None

table_path = join(config.FISHER_ROOT, 'doc', 'fe_03_p%s_calldata.tbl' % config.FISHER_DISC)

def load_table():
    global table
    table = []
    with open(table_path) as table_file:
        reader = DictReader(table_file)
        for record in reader:
            table.append(record)

def transcript_ids(query_fn=lambda _: True):
    global table
    if not table:
        load_table()
    return [record['CALL_ID'] for record in table if query_fn(record)]

def transcript_ids_for_topic(topic_id):
    return transcript_ids(lambda record: record['TOPICID'] == topic_id)
