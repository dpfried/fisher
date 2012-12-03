from csv import DictReader
from os.path import join
import config

table = None

table_path = join(config.FISHER_ROOT, 'doc', 'fe_03_p%s_calldata.tbl' % config.FISHER_DISC)

def load_table():
    """ call this function to load the calldata.tbl csv file into a list of transcript dictionaries"""
    global table
    table = []
    with open(table_path) as table_file:
        reader = DictReader(table_file)
        for record in reader:
            table.append(record)

def transcript_ids(query_fn=lambda _: True):
    """return a list of transcript ids that match the given query. query_fn is a function on a dictionary with the fields defined by the calldata.tbl csv file"""
    global table
    if not table:
        load_table()
    return [record['CALL_ID'] for record in table if query_fn(record)]

def transcript_ids_for_topic(topic_id):
    """returns a list of ids of transcripts about a given topic_id (e.g. "ENG01")"""
    return transcript_ids(lambda record: record['TOPICID'] == topic_id)
