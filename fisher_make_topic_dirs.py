from os.path import join, basename
from os import makedirs
import transcripts
import calldata
import config

OUT_ROOT = config.FISHER_TOPIC_SEGMENTATION_ROOT

# get topic ids
topic_info = calldata.get_topic_info()
topic_id2info = dict([(topic_id, (title, sentence)) for (topic_id, title, sentence) in topic_info])
##for (topic_id, title, sentence) in topic_info:
##    print topic_id, title
##    print sentence


# get transcript ids for each topic id
topic_id2transcript_ids = {}
for (topic_id, _, _) in topic_info:
    topic_id2transcript_ids[topic_id] = calldata.transcript_ids_for_topic(topic_id)


# create directories whose names are topic titles
# put processed transcript in directory according to topic
for (topic_id, transcript_ids) in topic_id2transcript_ids.items():

    title = topic_id2info[topic_id][0]
                          
    for transcript_id in transcript_ids:

        transcript_path = transcripts.transcript_path_for_id(transcript_id)
        filename = basename(transcript_path)
        out_dir = join(OUT_ROOT, title)
        try:
            makedirs(out_dir)
        except:
            pass

        #print 'write', join(out_dir, filename)
        print transcript_id
        of = open(join(out_dir, filename), 'w')

        # OPTION 1: write both speaker and utterance
        # example:
        #  A   hello how are you
        #  B   i am fine
        utt = transcripts.read_transcript(transcript_id)
        for (sp, ut) in utt:
            of.write('%s\t%s\n' % (sp, ut))

        # OPTION 2: write just the utterances
        # example:
        #  hello how are you
        #  i am fine
        # utt = transcripts.utterances(transcript_id)
        #for ut in utt:
        #    of.write(ut+'\n')

        of.close()
