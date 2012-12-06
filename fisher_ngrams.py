# 'frequency' means 'count'

import config
import os
import os.path
import fnmatch

import math

DATA_ROOT = config.FISHER_TOPIC_SEGMENTATION_ROOT
OUT_DIR = '/home/dfried/fisher_ngrams'

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
#
# pointwise is: log(p(ngram,topic)/p(ngram)p(topic))
def get_pointwise_mi(ngram_topic2prob, ngram2prob, topic2prob):

    ngram_topic2mi = {}
    for (ngram, topic) in ngram_topic2prob.keys():

        joint_p = ngram_topic2prob[(ngram,topic)]
        marg_p1 = ngram2prob[ngram]
        marg_p2 = topic2prob[topic]

        mi = math.log((joint_p/(marg_p1*marg_p2)), 2) # base 2
        ngram_topic2mi[(ngram,topic)] = mi

    return ngram_topic2mi



def get_mi_probs(ngram_topic2tokenfq_docfq):

    total_tokenfq = 1.0*sum([fq for (_,[fq,__]) in ngram_topic2tokenfq_docfq.items()])
    #print 'total_tokenfq:', total_tokenfq

    ngram_topic2tokenfq = {}
    ngram2tokenfq = {}
    topic2tokenfq = {}
    for ((ngram, topic), [tokenfq, docfq]) in ngram_topic2tokenfq_docfq.items():
        ngram_topic2tokenfq[(ngram,topic)] = ngram_topic2tokenfq.get((ngram,topic),0) + tokenfq
        ngram2tokenfq[ngram] = ngram2tokenfq.get(ngram,0) + tokenfq
        topic2tokenfq[topic] = topic2tokenfq.get(topic,0) + tokenfq

    ngram_topic2prob = get_key_prob_dict(ngram_topic2tokenfq)
    ngram2prob = get_key_prob_dict(ngram2tokenfq)
    topic2prob = get_key_prob_dict(topic2tokenfq)

    return (ngram_topic2tokenfq, ngram2tokenfq, topic2tokenfq,
            ngram_topic2prob, ngram2prob, topic2prob)

   
##########################

# num_top_vals: don't print all
def write_a2b2c(a2b2c, dname, n, num_top_vals=0, freq_filter=False, abbrev=False):
    fname = os.path.join(OUT_DIR, dname+'.'+str(n)+'.txt')
    print 'write', fname
    of = open(fname, 'w')
    for a in sorted(a2b2c.keys()):
        b2c = a2b2c[a]

        s = a

        # topics begin with Upper case
        if freq_filter==True and a[0].islower() and a not in freq_ngrams:
            continue

        # sort by decreasing prob
        if num_top_vals==0:
            num_top_vals = len(b2c)
        i = 0
        
        for (c,b) in reversed(sorted([(v,k) for (k,v) in b2c.items()])):
            if i==num_top_vals:
                break
            i += 1

            if freq_filter==True and b[0].islower() and b not in freq_ngrams: continue
            
            # abbreviate topic by 1st 3 chars, e.g. 'Education' -> 'Educ'
            if abbrev:
                if b.startswith('Hypothetical'):
                    b = 'HS.' + b[len('Hypothetical Situations._'):][:4]
                    s += '\t' + b + ':' + '%.5f'%c
                else:
                    s += '\t' + b[:4] + ':' + '%.5f'%c
            else:
                s += '\t' + b + ':' + '%.5f'%c
        of.write(s+'\n')
    of.close()

def write_sorted_dict(d, dname, n, freq_filter=False):
    fname = os.path.join(OUT_DIR, dname+'.'+str(n)+'.txt')
    print 'write', fname
    of = open(fname, 'w')
    for (v,k) in reversed(sorted([(v,k) for (k,v) in d.items()])):
        if isinstance(k, tuple): # ngram_topic2tokenfq
            (ngram, topic) = k
            if freq_filter==True and ngram not in freq_ngrams: continue
            of.write('%.5f\t%s\t%s\t\n' % (v, ngram, topic))
        else:
            if freq_filter==True and k not in freq_ngrams: continue
            of.write('%s\t%.5f\n' % (k, v))
    of.close()


def write_topic2mi_ngrams(topic2mi_ngrams, dname, n, num_top_vals=0, freq_filter=True):
    fname = os.path.join(OUT_DIR, dname+'.'+str(n)+'.txt')
    print 'write', fname
    of = open(fname, 'w')

    for topic in sorted(topic2mi_ngrams.keys()):
        mi_ngrams = topic2mi_ngrams[topic]

        s = topic
        if num_top_vals==0:
            num_top_vals = len(mi_ngrams)
        i = 0
        
        for (mi, ngram) in reversed(sorted(mi_ngrams)):
            if freq_filter==True and ngram not in freq_ngrams:
                continue
            
            if i==num_top_vals:
                break
            i += 1

            s += '\t' + '%.5f:%s' % (mi, ngram)
        of.write(s+'\n')
        of.write('\n') # separate topics
            
    of.close()

# 0. total word frequency for each topic
def topic_word_fq():

    ngram_topic2tokenfq_docfq = {}

    # iterate over files to compute
    # (ngram, topic, #tokens, #docs) for some value of n
    # CURRENTLY NOT MAKING USE OF #docs
    for fi in files:
        # topic is last subdir in path
        topic = '_'.join(topic_from_path(fi).split())
        #print topic
        get_file_ngram_fqs(fi, topic, 1, ngram_topic2tokenfq_docfq)

    topic2fq = {}
    for ((ngram, topic), [tokenfq, docfq]) in ngram_topic2tokenfq_docfq.items():
        topic2fq[topic] = topic2fq.get(topic,0) + tokenfq

    for (topic,fq) in topic2fq.items():
        print topic, fq

    print 'total number of words:', sum(topic2fq.values())
 
##########################

def topic_from_path(path):
    topic_path = os.path.split(path)[0]
    return os.path.split(topic_path)[1]

topic_word_fq()

files = get_files_recursive(DATA_ROOT, '*.txt')#[:100]
print 'num files:', len(files)
for n in [1,2,3]: # order of n-gram: unigram, bigram, trigram
##for n in [1,2]: # order of n-gram: unigram, bigram, trigram
##for n in [1]:
    print 'n:', n

    # 0. ngram_topic2tokenfq_docfq
    # key: (ngram, topic)
    # value: (total token fquency, number of documents it occurs in)
    ngram_topic2tokenfq_docfq = {}

    print 0
    # iterate over files to compute
    # (ngram, topic, #tokens, #docs) for some value of n
    # CURRENTLY NOT MAKING USE OF #docs
    for fi in files:
        # topic is last subdir in path
        topic = '_'.join(topic_from_path(fi).split())
        #print topic
        get_file_ngram_fqs(fi, topic, n, ngram_topic2tokenfq_docfq)



    # 1. frequency filter: minimum freq for n-gram to be included in output file
    min_freq = 50
    freq_ngrams = set([ng for ((ng,_),(tf,__)) in ngram_topic2tokenfq_docfq.items() if tf >= min_freq])


    # 2. frequency of (ngram, topic)
    ngram_topic2tokenfq = dict([(k,v[0]) for (k,v) in ngram_topic2tokenfq_docfq.items()])
    write_sorted_dict(ngram_topic2tokenfq, 'ngram_topic2tokenfq', n, freq_filter=True)

    
    # 3. p(ngram|topic), by #tokens
    print 'compute p(ngram|topic)'
    topic2ngram2prob = get_p_ngram_given_topic(ngram_topic2tokenfq_docfq)
    write_a2b2c(topic2ngram2prob, 'topic2ngram2prob', n, num_top_vals=25, freq_filter=True)
    del topic2ngram2prob # use less memory on my old computer

    
    # 4. p(topic|ngram), by #tokens
    # TODO: could use frequency filter early
    print 'compute p(topic|ngram)'
    ngram2topic2prob = get_p_topic_given_ngram(ngram_topic2tokenfq_docfq)
    write_a2b2c(ngram2topic2prob, 'ngram2topic2prob', n, num_top_vals=5, freq_filter=True, abbrev=True, )


    # 5. topic entropy given ngram, by #tokens
    # high entropy = ngram is not particular to topic
    # TODO: could use frequency filter early
    print 'compute topic entropy given ngram'
    ngram2topic_entropy = get_topic_entropy_given_ngram(ngram2topic2prob)
    write_sorted_dict(ngram2topic_entropy, 'ngram2topic_entropy', n, freq_filter=True)
    del ngram2topic2prob # use less memory on my old computer


    # 6. pointwise mutual information between ngram and topic
    # (i.e., for some particular ngram and some particular topic)
    print 'compute pointwise mutual information'
    t = get_mi_probs(ngram_topic2tokenfq_docfq)
    (ngram_topic2tokenfq, ngram2tokenfq, topic2tokenfq) = t[0:3]
    (ngram_topic2prob, ngram2prob, topic2prob) = t[3:6]
    ngram_topic2mi = get_pointwise_mi(ngram_topic2prob, ngram2prob, topic2prob)

    write_sorted_dict(ngram2tokenfq, 'ngram2tokenfq', n, freq_filter=True)
    write_sorted_dict(ngram2prob, 'ngram2prob', n, freq_filter=True)
    write_sorted_dict(topic2prob, 'topic2prob', n, freq_filter=False)
    write_sorted_dict(ngram_topic2mi, 'ngram_topic2mi', n, freq_filter=True)


    # 7. topic2mi2ngram (which is just rearrangement of ngram_topic2mi)
    topic2mi_ngrams = {}
    for ((ngram,topic), mi) in ngram_topic2mi.items():
        mi_ngrams = topic2mi_ngrams.get(topic, [])
        mi_ngrams.append((mi,ngram))
        topic2mi_ngrams[topic] = mi_ngrams
    write_topic2mi_ngrams(topic2mi_ngrams, 'topic2mi_ngrams', n, num_top_vals=100, freq_filter=True)
