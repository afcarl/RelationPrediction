import numpy as np

class Summary():

    calculate_hits_at = [1,3,10]
    results = {'Raw':{}, 'Filtered':{}}
    
    def __init__(self, raw_ranks, filtered_ranks):
        self.results['Raw'][self.mrr_string()] = self.get_mrr(raw_ranks)
        self.results['Filtered'][self.mrr_string()] = self.get_mrr(filtered_ranks)

        for h in self.calculate_hits_at:
            self.results['Raw'][self.hits_string(h)] = self.get_hits_at_n(raw_ranks,h)
            self.results['Filtered'][self.hits_string(h)] = self.get_hits_at_n(filtered_ranks,h)

    def mrr_string(self):
        return 'MRR'

    def hits_string(self, n):
        return 'H@'+str(n)
            
    def pretty_print(self):
        print('\tRaw\tFiltered')

        items = [self.mrr_string()]
        for h in self.calculate_hits_at:
            items.append(self.hits_string(h))

        for item in items:
            print(item, end='\t')
            print(str(round(self.results['Raw'][item],3)), end='\t')
            print(str(round(self.results['Filtered'][item],3)))
            
    def get_mrr(self, ranks):
        mean_reciprocal_rank = 0.0
        for rank in ranks:
            mean_reciprocal_rank += 1/rank
        return mean_reciprocal_rank / len(ranks)

    def get_hits_at_n(self, ranks, n):
        hits = 0.0
        for rank in ranks:
            if rank <= n:
                hits += 1
        return hits / len(ranks)

    
class Score():

    raw_ranks = []
    filtered_ranks = []
    predicted_probabilities = []
    pointer = 0
    
    def __init__(self, dataset):
        self.raw_ranks = [None]*len(dataset)*2
        self.filtered_ranks = [None]*len(dataset)*2
        self.predicted_probabilities = [None]*len(dataset)*2

    def append_line(self, evaluations, gold_idx, filter_idxs):
        score_gold = evaluations[gold_idx]
        self.predicted_probabilities[self.pointer] = score_gold
        self.raw_ranks[self.pointer] = np.sum(evaluations >= score_gold)
        self.filtered_ranks[self.pointer] = np.sum(evaluations >= score_gold) - (np.sum(evaluations[filter_idxs] >= score_gold)) + 1
        self.pointer += 1
        
    def print_to_file(self, filename):
        outfile = open(filename, 'w+')

        for raw, filtered, prob in zip(self.raw_ranks, self.filtered_ranks, self.predicted_probabilities):
            print(str(raw) +
                  '\t'+ str(filtered) +
                  '\t'+ str(prob),
                  file=outfile)

    def get_summary(self):
        return Summary(self.raw_ranks, self.filtered_ranks)

    def summarize(self):
        summary = self.get_summary()
        summary.pretty_print()
        
        
class Scorer():

    known_subject_triples = {}
    known_object_triples = {}
    
    def __init__(self):
        pass

    def extend_triple_dict(self, dictionary, triplets, object_list=True):
        for triplet in triplets:
            if object_list:
                key = (triplet[0], triplet[1])
                value = triplet[2]
            else:
                key = (triplet[2],triplet[1])
                value = triplet[0]
        
            if key not in dictionary:
                dictionary[key] = [value]
            elif value not in dictionary[key]:
                dictionary[key].append(value)

    def register_data(self, triples):
            self.extend_triple_dict(self.known_subject_triples, triples, object_list=False)
            self.extend_triple_dict(self.known_object_triples, triples)

    def register_model(self, model):
        self.model = model

    def compute_scores(self, triples, verbose=False):
        score = Score(triples)

        if verbose:
            print("Evaluating subjects...")
            i = 1
            
        pred_s = self.model.score_all_subjects(triples)

        for evaluations, triplet in zip(pred_s, triples):
            if verbose:
                print("Computing ranks: "+str(i)+" of "+str(len(triples)), end='\r')
                i += 1
            
            known_subject_idxs = self.known_subject_triples[(triplet[2],triplet[1])]
            gold_idx = triplet[0]            
            score.append_line(evaluations, gold_idx, known_subject_idxs)

        if verbose:
            print("\nEvaluating objects...")
            i = 1
            
        pred_o = self.model.score_all_objects(triples)

        for evaluations, triplet in zip(pred_o, triples):
            if verbose:
                print("Computing ranks: "+str(i)+" of "+str(len(triples)), end='\r')
                i += 1

            known_object_idxs = self.known_object_triples[(triplet[0],triplet[1])]
            gold_idx = triplet[2]
            score.append_line(evaluations, gold_idx, known_object_idxs)

        print("")
        return score
