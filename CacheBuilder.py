#!/usr/bin/env python3

# imports
from array import array
from operator import itemgetter
from shutil import rmtree
from os import mkdir, \
               scandir
from datetime import datetime, \
                     timedelta
from functools import reduce
import sys
import threading
import pickle

# 'constants'
DATA_PATH = './data/'
EID = 'cat3263'


def all_avg_movie_ratings():
    """
    return an array of the average rating for all movies
    movie_id is the array index
    """
    print('Calculating average rating for each movie...')
    avg_ratings = array('f',[0])
    for movie_id in range(1, 17771):
        ratings = fetch_ratings_for_movie(movie_id)
        avg_ratings.append(avg_movie_rating(ratings))
    return avg_ratings


def avg_movie_rating(ratings):
    """
    return the average rating from a movie rating dict
    """
    s = 0.0
    for c in ratings:
        s += ratings[c]
    return s / len(ratings)


def fetch_ratings_for_movie(movie_id):
    """
    read and return all ratings for a given movie as {customer_id:(r,d)}
    """
    with open(DATA_PATH + 'training_set/mv_' + str(movie_id).zfill(7)
              + '.txt','r') as mv:
        ratings = {}
        lines = iter(mv.readlines())
        next(lines)
        for l in lines:
            c, r, d = l.strip().split(',')
            ratings[int(c)] = int(r)
        return ratings


def convert_training_set():
    """
    converts training_set files into an analog version organized by customer_id
    """
    # fair warning - guard against my.self
    print('Converting movie data to customer data...')
    print('This will take a long time and will start by removing any'
          + 'customer_data directory in the DATA_PATH.')
    really = input('Continue? [yn]: ')
    if really != 'y':
        print('Canceled.')
        return

    rmtree(DATA_PATH + 'customer_data/')
    mkdir(DATA_PATH + 'customer_data/')

    threads = [threading.Thread(target=convert_range, args=(1, 1000,))]
    for start in range (1000, 18000, 1000):
        threads.append(threading.Thread(target=convert_range,
                       args=(start, start + 1000)))
    threads.append(threading.Thread(target=convert_range, args=(17000, 17771)))
    for t in threads:
        t.start()
    for t in threads:
        t.join()


def convert_range(start, stop):
    """
    start, stop two ints
    used by convert_training_set to divide up full range for threading
    """
    for movie_id in range(start, stop):
        this_movies_ratings = fetch_ratings_for_movie(movie_id)
        print('--Processing movie_id: ' + str(movie_id) + ', length: '
              + str(len(this_movies_ratings)))
        for c in this_movies_ratings.keys():
            with open(DATA_PATH + 'customer_data/c_' + str(c).zfill(7)
                      + '.txt','a') as f:
                r, d = this_movies_ratings[c]
                print(str(movie_id) + ',' + str(r) + ',' + d, file=f)


def all_avg_customer_ratings():
    """
    ratings a dict: {customer_id:{movie_id:(rating, date))}
    return average rating by each customer: {customer_id:avg_rating}
    """
    avg_ratings = {}
    for entry in scandir(DATA_PATH + '/customer_data'):
        print(entry.name)
        c = int(entry.name[2:9])
        avg_ratings[c] = avg_customer_rating(c)
    return avg_ratings


def avg_customer_rating(customer_id):
    """
    ratings a dict: {movie_id:(rating, date)}
    return the average rating from a customer rating dict
    """
    r_sum = 0.0
    ratings = fetch_ratings_for_customer(customer_id)
    for rating, _ in ratings.items():
        r_sum += rating
    return r_sum / len(ratings)


def fetch_ratings_for_customer(customer_id):
    """
    read and return all ratings for a given customer as {movie_id:(r,d)}
    """
    with open(DATA_PATH + 'customer_data/c_' + str(customer_id).zfill(7)
              + '.txt','r') as cf:
        ratings = {}
        for l in cf.readlines():
            movie_id, rating, date = l.strip().split(',')
            ratings[int(movie_id)] = (int(rating), date)
    return ratings


def sort_all_customer_files():
    '''
    sorts all customer files in customer_data directory
    '''
    for entry in scandir(DATA_PATH + '/customer_data'):
        c = int(entry.name[2:9])
        sort_customer_file(c)


def sort_customer_file(customer_id):
    '''
    customer_id an int
    sorts ratings in a customer file by date
    '''
    ratings = fetch_ratings_for_customer(customer_id)
    # sort by date
    ratings = sorted(ratings.items(), key=lambda r: r[1][1])
    with open(DATA_PATH + 'customer_data/c_' + str(customer_id).zfill(7)
              + '.txt','w') as cf:
        for m, r in ratings:
            print(str(m) + ',' + str(r[0]) + ',' + r[1], file=cf)


def customer_avg_by_year():
    '''
    returns a dictionary of the average rating from each year for each customer
    {customer_id:{<year>:avg_that_year}}
    '''
    release_years = load_pickle('amry') # all movie release years
    avgs = {}
    for entry in scandir(DATA_PATH + '/customer_data'):
        print(entry.name)
        c = int(entry.name[2:9])
        with open(entry.path,'r') as cf:
            ratings = {}
            for l in cf.readlines():
                movie_id, rating, _ = l.split(',')
                rating = int(rating)
                year = release_years[int(movie_id)]
                if year in ratings:
                    ratings[year].append(rating)
                else:
                    ratings[year] = [rating]
            for year in ratings:
                ratings[year] = reduce(lambda m, n: m + n,
                                    ratings[year]) / len(ratings[year])
            avgs[c] = ratings
    return avgs


def all_movie_release_years():
    '''
    returns movie release years in an array, index with movie_id
    movies with no age in movie_titles.txt have a value of -1
    '''
    with open(DATA_PATH + 'movie_titles.txt', 'r') as f:
        release_years = array('i',[0])
        for l in f.readlines():
            release_year = l.split(',')[1]
            if release_year.isdigit():
                release_years.append(int(release_year))
            else:
                release_years.append(-1)
    return release_years


def coalesce_movie_data():
    '''
    coalesce needed movie caches into a single one for runtime
    '''
    amry = load_pickle('amry') # all movie release years
    avgmr = load_pickle('avgmr') # average movie ratings

    movie_data = {}
    for movie_id in range(1, 17771):
        movie_data[movie_id] = {'year':amry[movie_id],
                                'avgr':avgmr[movie_id]}
    return movie_data


def coalesce_customer_data():
    '''
    coalesce needed customer caches into a single one for runtime
    '''
    avgcr = load_pickle('avgcr') # average customer rating
    caby = load_pickle('caby')

    customer_data = {}
    for c in avgcr:
        customer_data[c] = {'avgr':avgcr[c],
                            'caby':caby[c]}
    return customer_data


def answers():
    """
    returns a dict of actual ratings for reviews in probe.txt
    format: {movie_id:{customer_id:rating)}}
    """
    answers = {}
    with open(DATA_PATH + 'probe.txt') as probe:
        lines = probe.readlines()
        # parse each line in probe.txt
        ratings = {}
        for l in lines:
            l = l.strip()
            if l[-1] == ':': # line is a movie_id
                movie_id = int(l[:-1])
                ratings = fetch_ratings_for_movie(movie_id)
                answers[movie_id] = {}
            else: # line is customer_id, add rating to dict
                customer_id = int(l)
                answers[movie_id][customer_id] = ratings[customer_id]
    return answers


def write_pickle(obj, name):
    '''
    obj an object
    name a string
    writes an object to a pickle file
    '''
    with open(DATA_PATH + EID + '-' + name + '.pickle','wb') as f:
        pickle.dump(obj, f)


def load_pickle(name):
    '''
    name a string
    reads an object from a pickle file
    '''
    with open(DATA_PATH + EID + '-' + name + '.pickle','rb') as f:
        obj = pickle.load(f)
    return obj


def validate_args(args):
    '''
    args list of strings
    validates command line arguments - not implemented
    '''
    return args


if __name__ == '__main__':
    args = validate_args(sys.argv)
    if len(args) > 1:
        if '-m2c' in args:
            convert_training_set()
        if '-scf' in args:
            sort_all_customer_files()
        if '-amry' in args:
            write_pickle(all_movie_release_years(), 'amry')
        if '-avgmr' in args:
            write_pickle(all_avg_movie_ratings(), 'avgmr')
        if '-avgcr' in args:
            write_pickle(all_avg_customer_ratings(), 'avgcr')
        if '-caby' in args:
            write_pickle(customer_avg_by_year(), 'caby')
        if '-com' in args:
            write_pickle(coalesce_movie_data(), 'mov-2')
        if '-coc' in args:
            write_pickle(coalesce_customer_data(), 'cust-2')
        if '-a' in args:
            write_pickle(answers(), 'a')
        if '-test' in args:
            fetch_ratings_for_movie(1)
        print('Done.')
    else:
        print('usage: python3 CacheBuilder.py <-m2c,-scf,-amry,-avgmr,'
              + '-avgcr,-rby,-com,-coc,-a>')
