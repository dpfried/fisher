from csv import DictReader
from os.path import join
from xml.etree import ElementTree
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

# Example:
# <topic id="ENG01" title="Professional Sports on TV." >
# Do either of you have a favorite TV sport? How many hours per week do you spend watching it and other sporting events on TV?
# </topic>
#
# returns list of ('ENG01', 'Professional Sports on TV', sentence)
#
# 'Professional Sports on TV.' -> 'Professional Sports on TV'

#def get_topic_info():
#    topic_path = join(config.FISHER_ROOT, 'doc', 'fe_03_topics.sgm')
#    lines = '<root>\n%s\n</root>' % open(topic_path, 'r').read().replace('<<', '&lt;')
#    root = ElementTree.fromstring(lines)
#    return [(topic.attrib['id'], topic.attrib['title'], topic.text.strip()) for topic in root]

def get_topic_info():
    topic_info = []

    topic_path = join(config.FISHER_ROOT, 'doc', 'fe_03_topics.sgm')

    lines = open(topic_path, 'r').readlines()
    i = 0
    while i < len(lines):
        line = lines[i]

        id_idx = line.find('id=')
        if id_idx!=-1:
            topic_str = line[id_idx+4:id_idx+9]

        title_idx = line.find('title=')
        if title_idx!=-1:
            title_str = line[title_idx+7:line.find('"',title_idx+7)]
            if title_str[-1]=='.':
                title_str = title_str[:-1]
        sentence = lines[i+1].strip()

        topic_info.append((topic_str, title_str, sentence))
        i += 3

    return topic_info
