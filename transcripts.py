from os.path import join 
from itertools import groupby
import config

def transcript_path_for_id(transcript_id):
    """produces the path to the LDC data for a given transcript_id"""
    if transcript_id is int:
        transcript_id = "%05d" % transcript_id
    prefix_folder = str(transcript_id)[:3]
    return join(config.FISHER_ROOT, 'data', 'trans', prefix_folder, 'fe_03_%s.txt' % transcript_id)

def transcript_lines(transcript_text):
    """splits raw transcript text into lines and returns a list of (speaker, utterance)"""
    lines = []
    for line in transcript_text.splitlines():
        if line.strip() and line.strip()[0] != '#':
            split = line.split(':')
            speaker = split[0][-1]
            utterance = ' '.join(split[1:]).strip()
            lines.append((speaker, utterance))
    return lines

def read_transcript(transcript_id):
    """given a transcript_id, returns the (speaker, utterance) list for that transcript"""
    with open(transcript_path_for_id(transcript_id)) as f:
        return transcript_lines(f.read())

def join_utterances(transcript_lines):
    """joins adjacent utterances in a list of (speaker, utterance) by the same speaker, returns a list of joined utterances"""
    lines = []
    for _, group in groupby(transcript_lines, lambda n: n[0]):
        lines.append(' '.join((utt for (speaker, utt) in group)).strip())
    return lines

def utterances(transcript_id):
    return join_utterances(read_transcript(transcript_id))
