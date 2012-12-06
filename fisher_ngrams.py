# 'frequency' means 'count'

import config
import os
import os.path
import fnmatch

import math

DATA_ROOT = config.FISHER_TOPIC_SEGMENTATION_ROOT

##########################

# returns list of strings matching pattern, with full path name
def get_files_recursive(root_path, pattern='*'):
    filelist = []
    for root, dirs, files in os.walk(root_path):
        for filename in fnmatch.filter(files, pattern):
            filelist.append(os.path.join(root, filename))
    return filelist


# modifies dictionary ngram_topic2tokenfq_docfq
# because it's called over many files
def get_file_ngram_fqs(filename, topic, n, ngram_topic2tokenfq_docfq):

    ngram2tokenfq = {}

    for line in open(filename, 'r'):
        toks = line.split()[1:] # ignore Speaker
        for i in range(len(toks)-n+1):
            ngram = '_'.join(toks[i:i+n])
            ngram2tokenfq[ngram] = ngram2tokenfq.get(ngram, 0) + 1

    for (ngram, freq) in ngram2tokenfq.items():
        tokenfq_docfq = ngram_topic2tokenfq_docfq.get((ngram, topic), [0,0])
        # increase total count for ngram
        tokenfq_docfq[0] += freq
        # increase docfq by 1 because this ngram occurs in this document
        tokenfq_docfq[1] += 1
        ngram_topic2tokenfq_docfq[(ngram,topic)] = tokenfq_docfq

# input a key:int dictionary,
# output a key:prob dictionary
def get_key_prob_dict(d):
    denom = 1.0*sum(d.values())
    return dict([(k,v/denom) for (k,v) in d.items()])

# 1. p(ngram|topic), by #tokens
def get_p_ngram_given_topic(ngram_topic2tokenfq_docfq):

    topic2ngram2fq = {}
    for ((ngram, topic), [tokenfq, docfq]) in ngram_topic2tokenfq_docfq.items():
        ngram2fq = topic2ngram2fq.get(topic, {})
        ngram2fq[ngram] = ngram2fq.get(ngram,0) + tokenfq
        topic2ngram2fq[topic] = ngram2fq

    topic2ngram2prob = {}
    for (topic, ngram2fq) in topic2ngram2fq.items():
        ngram2fq = topic2ngram2fq[topic]
        ngram2prob = get_key_prob_dict(ngram2fq)
        topic2ngram2prob[topic] = ngram2prob

    return topic2ngram2prob


# 2. p(topic|ngram), by #tokens
def get_p_topic_given_ngram(ngram_topic2tokenfq_docfq):

    ngram2topic2fq = {}
    for ((ngram, topic), [tokenfq, docfq]) in ngram_topic2tokenfq_docfq.items():
        topic2fq = ngram2topic2fq.get(ngram, {})
        topic2fq[topic] = topic2fq.get(topic,0) + tokenfq
        ngram2topic2fq[ngram] = topic2fq

    ngram2topic2prob = {}
    for (ngram, topic2fq) in ngram2topic2fq.items():
        topic2fq = ngram2topic2fq[ngram]
        topic2prob = get_key_prob_dict(topic2fq)
        ngram2topic2prob[ngram] = topic2prob

    return ngram2topic2prob


# 3. topic entropy given ngram, by #tokens
def get_topic_entropy_given_ngram(ngram2topic2prob):

    ngram2topic_entropy = {}
    for (ngram, topic2prob) in ngram2topic2prob.items():
        ngram2topic_entropy[ngram] = entropy(topic2prob.values())
        
    return ngram2topic_entropy
    
def entropy(a):
    
    if sum(a) > 1.0001:
        print 'WHOOPS SUM GREATER THAN 1'
        raise Exception

    h = 0
    for i in range(len(a)): # should be same length!
        if a[i]!=0:
            h += -1 * a[i] * math.log(a[i], 2)
    return h

# 4. pointwise mutual information between ngram and topic,
# (i.e., for some particular ngram and some particular topic)
# only computed for ngram/topic pairs that are nonzero
#
# I(ngram;topic) = p(ngram,topic) * log(p(ngram,topic)/p(ngram)p(topic))
# (mutual information between ngram and topic random var would sum over pointwise)
def get_pointwise_mi(ngram_topic2prob, ngram2prob, topic2prob):

    ngram_topic2mi = {}
    for (ngram, topic) in ngram_topic2prob.keys():

        joint_p = ngram_topic2prob[(ngram,topic)]
        marg_p1 = ngram2prob[ngram]
        marg_p2 = topic2prob[topic]

        mi = joint_p * math.log((joint_p/(marg_p1*marg_p2)), 2) # base 2
        ngram_topic2mi[(ngram,topic)] = mi

    return ngram_topic2mi



def get_mi_probs(ngram_topic2tokenfq_docfq):

    total_tokenfq = 1.0*sum([fq for (_,[fq,__]) in ngram_topic2tokenfq_docfq.items()])
    #print 'total_tokenfq:', total_tokenfq

    ngram_topic2fq = {}
    ngram2fq = {}
    topic2fq = {}
    for ((ngram, topic), [tokenfq, docfq]) in ngram_topic2tokenfq_docfq.items():
        ngram_topic2fq[(ngram,topic)] = ngram_topic2fq.get((ngram,topic),0) + 1
        ngram2fq[ngram] = ngram2fq.get(ngram,0) + 1
        topic2fq[topic] = topic2fq.get(topic,0) + 1

    ngram_topic2prob = get_key_prob_dict(ngram_topic2fq)
    ngram2prob = get_key_prob_dict(ngram2fq)
    topic2prob = get_key_prob_dict(topic2fq)

    return (ngram_topic2prob, ngram2prob, topic2prob)

   
##########################


# 0. total word frequency for each topic
def topic_word_fq():

    ngram_topic2tokenfq_docfq = {}

    # iterate over files to compute
    # (ngram, topic, #tokens, #docs) for some value of n
    # CURRENTLY NOT MAKING USE OF #docs
    for fi in files:
        # topic is last subdir in path
        # topic = fi[fi.rfind('\\',0,fi.rfind('\\')-1)+1:fi.rfind('\\')]
        topic = topic_from_path(fi)
        #print topic
        get_file_ngram_fqs(fi, topic, 1, ngram_topic2tokenfq_docfq)

    topic2fq = {}
    for ((ngram, topic), [tokenfq, docfq]) in ngram_topic2tokenfq_docfq.items():
        topic2fq[topic] = topic2fq.get(topic,0) + tokenfq

    for (topic,fq) in topic2fq.items():
        print topic, fq


#topic_word_fq()


# NUM WORDS PER TOPIC:
##Issues in the Middle East 227908
##Arms Inspections in Iraq 302912
##Hypothetical Situations. Opening your own busines 374137
##US Public Schools 227044
##Corporate Conduct in the US 205498
##Minimum Wage 612578
##September 11 342932
##Pets 658965
##Terrorism 99603
##Comedy 498310
##Outdoor Activities 147396
##Airport Security 184537
##Professional Sports on TV 530031
##Reality TV 406965
##Bioterrorism 186654
##Televised Criminal Trials 73999
##Holidays 266392
##Health and Fitness 203607
##Censorship 166095
##Smoking 145911
##Personal Habits 292488
##Family Values 42429
##Friends 112891
##Current Events 131104
##Hypothetical Situations. Perjury 143943
##Affirmative Action 125831
##Movies 133462
##Education 283083
##Computer games 85401
##Foreign Relations 237071
##Hypothetical Situations. An Anonymous Benefacto 270593
##Illness 326465
##Family 291337
##Life Partners 518591
##Food 267481
##Hypothetical Situations. Time Travel 413636
##Hobbies 153855
##Hypothetical Situations. One Million Dollars to leave the US 57225
##Strikes by Professional Athletes 208216
##Drug testing 51111
 
##########################

def topic_from_path(path):
    topic_path = os.path.split(path)[0]
    return os.path.split(topic_path)[1]


# main entry point
def process_ngrams():
    files = get_files_recursive(DATA_ROOT, '*.txt')
    print len(files)

    for n in [1,2,3]: # order of n-gram: unigram, bigram, trigram
        print 'n:', n
        
        # key: (ngram, topic)
        # value: (total token fquency, number of documents it occurs in)
        ngram_topic2tokenfq_docfq = {}

        # iterate over files to compute
        # (ngram, topic, #tokens, #docs) for some value of n
        # CURRENTLY NOT MAKING USE OF #docs
        for fi in files:
            # topic is last subdir in path
            # topic = fi[fi.rfind('\\',0,fi.rfind('\\')-1)+1:fi.rfind('\\')]
            topic = topic_from_path(fi)
            get_file_ngram_fqs(fi, topic, n, ngram_topic2tokenfq_docfq)

        # 1. p(ngram|topic), by #tokens
        topic2ngram2prob = get_p_ngram_given_topic(ngram_topic2tokenfq_docfq)

        # 2. p(topic|ngram), by #tokens
        ngram2topic2prob = get_p_topic_given_ngram(ngram_topic2tokenfq_docfq)

        # 3. topic entropy given ngram, by #tokens
        # high entropy = ngram is not particular to topic
        ngram2topic_entropy = get_topic_entropy_given_ngram(ngram2topic2prob)

        # 4. pointwise mutual information between ngram and topic
        # (i.e., for some particular ngram and some particular topic)
        (ngram_topic2prob, ngram2prob, topic2prob) = get_mi_probs(ngram_topic2tokenfq_docfq)
        ngram_topic2mi = get_pointwise_mi(ngram_topic2prob, ngram2prob, topic2prob)

        # 5. write all of the above to files; include value of n in file name

        # Example: outfilename = 'topic2ngram2prob.' + str(n) + '.txt'

        #ngram_topic2tokenfq_docfq
        #topic2ngram2prob
        #ngram2topic2prob
        #ngram2topic_entropy
        #ngram2prob
        #topic2prob

# only run if invoked from the command line, to allow importing without running
if __name__ == "__main__":
    process_ngrams()
