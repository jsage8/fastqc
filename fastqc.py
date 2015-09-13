#!/usr/bin/python

import sys
import os
import re
import gzip
import argparse
import subprocess

def processFiles(files, args):
  """------------------------------------------------------------------- 
  processFiles()
  Process the input files and pass them and the command line arguments
  on to the java fastqc file.
  Expects a list of files to process.
  If a file ends in .gz it is uncompressed as a temp file and passed.
  -------------------------------------------------------------------"""
  readyFiles = []
  tempFiles = []
  for inputFile in files:
    # Check to see if the file exists
    if os.path.isfile(inputFile):
      # Verify that passed in file names are fastq files
      isFastQ = re.search(r'.fastq$|.fq$|.fastq.gz$|.fq.gz$', inputFile)
      if isFastQ:
        # Check if the file is a compressed .gz file and uncompress to a
        # temp file is so
        isCompressed = re.search(r'(.+).gz$', inputFile)
        if isCompressed:
          print 'Extracting ' + inputFile + ' to temp file ' + isCompressed.group(1)
          copyUncompress(inputFile, isCompressed.group(1))
          tempFiles.append(isCompressed.group(1))
        else:
          readyFiles.append(inputFile)
      else:
        print 'WARNING: ' + inputFile + ' is not a recognized format!'
      
    # If the file does not exist print a warning 
    else:
      print 'WARNING: ' + inputFile + ' does not exist!'
  # Run the fastqc java file
  executeJava(args, "uk.ac.babraham.FastQC.FastQCApplication", readyFiles + tempFiles)
  # Delete the uncompressed temp files
  for filename in tempFiles:
    os.remove(filename)
  
def copyUncompress(filename,tempName):
  """------------------------------------------------------------------- 
  copyUncompress()
  Open a gzip file and write the extracted version to a temp file name.
  Expects the name of the file to be extracted and the name of the temp
  file to be written to.
  -------------------------------------------------------------------"""
  fileHandle = gzip.open(filename, 'rt')
  tempHandle = open(tempName, 'w')
  for line in fileHandle:
    tempHandle.write(line)
  fileHandle.close()
  tempHandle.close()
    
def executeJar(javaFile, javaArgs):
  """------------------------------------------------------------------- 
  executeJar()
  Execute a Java .jar file.
  Expects a Java .jar file name and a list of arguments passed into that
  .jar.
  Note: This function is not used as only .class files needed to be
  executed, but I have left it in case it may be useful in the future.
  -------------------------------------------------------------------"""
  processArguments = ['java', '-jar', javaFile] + javaArgs
  subprocess.call(processArguments)
  
def executeJava(javaArgs, javaClass, fileArgs):
  """------------------------------------------------------------------- 
  executeJava()
  Execute a Java .class file
  Expects a Java .class file name (not the extension) and a list of 
  arguments passed into that .class
  -------------------------------------------------------------------"""
  processArguments = ['java'] + javaArgs + [javaClass] + fileArgs
  subprocess.call(processArguments)

def main():
  """------------------------------------------------------------------- 
  main()
  Parses command line arguments using argparse. It can accept an 
  unlimited number of file names. It also will parse out several options 
  that get passed to the fastqc java file.
  
  If no files were input on command line process all fastq files in the 
  current working directory.
  
  Calls processFiles to pass in arguments to the fastq java file.
  -------------------------------------------------------------------"""
  # Use argparse to take in input files names from the command line
  parser = argparse.ArgumentParser(description='Process FastQ files with FastQC.')
  parser.add_argument('inputFiles', nargs='*', help="optional input files names")
  parser.add_argument('-v', '--version', help='Print fastqc version information', action='store_true')
  parser.add_argument('-o', '--outdir', help='Specify an output directory')
  parser.add_argument('-c', '--contaminant', help='Specify a contaminant file')
  parser.add_argument('-a', '--adapter', help='Specify an adapter file')
  parser.add_argument('-l', '--limits', help='Specify a limits file')
  parser.add_argument('-temp', '--temp_directory', help='Specify a temp directory')
  parser.add_argument('-t', '--threads', help='Specify the number of threads to use', type=int)
  parser.add_argument('-k', '--kmer_size', help='Specify kmer size', type=int)
  parser.add_argument('-q', '--quiet', help='Hide errors', action='store_true')
  parser.add_argument('-casa', '--casava', help='Use Casava', action='store_true')
  parser.add_argument('-nf', '--nofilter', help='Set no filter to true', action='store_true')
  parser.add_argument('-ng', '--nogroup', help='Set no group to true', action='store_true')
  parser.add_argument('-eg', '--expgroup', help='Set experiment group to true', action='store_true')
  parser.add_argument('-u', '--unzip', help='Set unzip to true', action='store_true')
  parser.add_argument('-f', '--format', help='Set file format', choices=['bam','sam','fastq','sam_mapped','bam_mapped'])
  
  args = parser.parse_args()
  
  # Interpret arguments and prepare to pass them as javaArgs
  javaArgs = []
  if args.version:
    javaArgs.append("-Dfastqc.show_version=true")
  if args.outdir:
    if os.path.isdir(args.outdir):
      javaArgs.append("-Dfastqc.output_dir=" + args.outdir)
    else:
      sys.exit(args.outdir + " is not a directory, or can't be written to\n")
  if args.contaminant:
    if os.path.isfile(args.contaminant):
      javaArgs.append("-Dfastqc.contaminant_file=" + args.contaminant)
    else:
      sys.exit("Contaminant file " + args.contaminant + " does not exist, or can't be read\n")
  if args.adapter:
    if os.path.isfile(args.adapter):
      javaArgs.append("-Dfastqc.adapter_file=" + args.adapter)
    else:
      sys.exit("Adapter file " + args.adapter + " does not exist, or can't be read\n")
  if args.limits:
    if os.path.isfile(args.limits):
      javaArgs.append("-Dfastqc.limits_file=" + args.limits)
    else:
      sys.exit("Limits file " + args.limits + " does not exist, or can't be read\n")
  if args.temp_directory:
    if os.path.isdir(args.temp_directory):
      javaArgs.append("-Djava.io.tmpdir=" + args.temp_directory)
    else:
      sys.exit(args.temp_directory + " is not a directory, or can't be written to\n")
  if args.threads:
    if args.threads < 1:
      sys.exit("Number of threads must be a positive integer\n")
    else:
      javaArgs.append("-Dfastqc.threads=" + str(args.threads))
      memory = 250 * args.threads
      javaArgs.insert(0, "-Xmx" + str(memory) + "m")
  else:
    memory = 250
    javaArgs.insert(0, "-Xmx" + str(memory) + "m")
  if args.kmer_size:
    if args.kmer_size < 2 or args.kmer_size > 10:
      sys.exit("Kmer size must be in the range 2-10\n")
    else:
      javaArgs.append("-Dfastqc.kmer_size=" + str(args.kmer_size))
  if args.quiet:
    javaArgs.append("-Dfastqc.quiet=true")
  if args.casava:
    javaArgs.append("-Dfastqc.casava=true")
  if args.nofilter:
    javaArgs.append("-Dfastqc.nofilter=true")
  if args.nogroup:
    javaArgs.append("-Dfastqc.nogroup=true")
  if args.expgroup:
    if args.nogroup:
      sys.exit("You can't specify both --expgroup and --nogroup in the same run\n")
    else:
      javaArgs.append("-Dfastqc.expgroup=true")
  if args.unzip:
    javaArgs.append("-Dfastqc.unzip=true")
  if args.format:
    javaArgs.append("-Dfastqc.sequence_format=" + args.format)
  
  # Add sam-1.103.jar and jbzip2-0.9.jar to the classpath
  javaPath = ".:./sam-1.103.jar:./jbzip2-0.9.jar"
  os.environ['CLASSPATH'] = javaPath
  
  # If files were input on command line, process those files
  if args.inputFiles:
    processFiles(args.inputFiles, javaArgs)
  # If no files were input on command line, process all fastQ files in 
  # the current directory
  else:
    inputFiles = [f for f in os.listdir('.') if os.path.isfile(f)]
    fastQFiles = []
    for inputFile in inputFiles:
      isFastQ = re.search(r'.fastq$|.fq$|.fastq.gz$|.fq.gz$', inputFile)
      if(isFastQ):
        fastQFiles.append(inputFile)
    processFiles(fastQFiles, javaArgs)
  
if __name__ == '__main__':
  main()
