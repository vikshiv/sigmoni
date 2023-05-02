from sigmoni import utils 
from sigmoni import run_spumoni as sig
from sigmoni.Bins import *
from sigmoni.shred_docs import shred
from sigmoni.build_reference import build_reference

import argparse
import os, sys

def parse_arguments():
    '''
    Required args: 
    fast5 input
    at least one positive ref
    at least one negative ref

    Optional args:
    spumoni path
    output path
    threads
    ref prefix
    read prefix

    Ref args:
    shred size
    revcomp
    '''

    parser = argparse.ArgumentParser(description="Maps and classifies nanopore signal against a positive and negative database")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-pl', dest='pos_filelist', help='list of positive ref fasta files')
    group.add_argument('-p', dest='pos_filelist', nargs='+', help='positive reference fasta file(s)')
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-nl', dest='null_filelist', help='list of null ref fasta files')
    group.add_argument('-n', dest='null_filelist', nargs='+', help='null reference fasta file(s)')
    # Required args
    parser.add_argument('-i', dest='fast5', help='path to input fast5 directory (searches recursively)', required=True)
    
    parser.add_argument(("-b", '--nbins'), dest='nbins', default=6, type=int, help="Number of bins to discretize signal")
    # ref build args
    parser.add_argument("--shred", dest='shred_size', default=int(1e5), type=int, help="Size of shredded documents, i.e. resolution of mapping, in bp")
    parser.add_argument("--no-rev-comp", action="store_false", default=True, dest="rev_comp", help="Do not map reads to the reverse complement of references")

    # options args
    parser.add_argument("--spumoni-path", dest='spumoni_path', default='spumoni', help="alternate path to spumoni installation (by default uses PATH variable)")
    parser.add_argument("-o", default='./', dest="output_path", help="output path and working directory")
    parser.add_argument("-t", default=1, dest="threads", help="number of threads", type=int)
    parser.add_argument("--read-prefix", dest="read_prefix", help="read output prefix", default='reads')
    parser.add_argument("--ref-prefix", dest="ref_prefix", help="reference output prefix", default='ref')
    args = parser.parse_args()
    return args

def format_args(args):
    if type(args.pos_filelist) == str:
        args.pos_filelist = open(args.pos_filelist, 'r').read().splitlines()
    if type(args.null_filelist) == str:
        args.null_filelist = open(args.null_filelist, 'r').read().splitlines()
    args.bins = HPCBin(nbins=args.nbins, poremodel=model_6mer, clip=False)

def main(args):
    '''
    Build the reference index by shredding the input 
    sequences, binning, and building the r-index
    '''
    print('Building reference')
    build_reference(args)
    print('Querying reads')
    query_reads(args)

def query_reads(args):
    seq_signal = unc.Fast5Reader(args.fast5)
    readfile = os.path.join(args.output_path, 'refs', args.ref_prefix + '.fa')
    if not os.path.exists(readfile):
        sig.write_read(seq_signal, args.bins, evdt=utils.SIGMAP_EVDT, fname=readfile, reverse=False)
    else:
        print('Using binned query found in: %s'%readfile)

    proc.call([args.spumoni_path, 'run', '-t', args.threads, '-r', os.path.join(args.output_path, 'refs', args.ref_prefix), '-p', readfile, '-P', '-n', '-d'])

if __name__ == '__main__':
    args = parse_arguments()
    format_args(args)
    main()