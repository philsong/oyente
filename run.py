import shlex
import subprocess
import os
import re
import sys
import global_params
import argparse

try:
	import z3
	import z3util
except:
	print "Error: Z3 is not available. Please install z3 from https://github.com/Z3Prover/z3."
	exit(0)

def cmd_exists(cmd):
    return subprocess.call("type " + cmd, shell=True, 
        stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("source", type=str, help="Solidity file name.")
	parser.add_argument("-e", "--evm", help="Do not remove the .evm file.", action="store_true")
	parser.add_argument("-p", "--paths", help="Print path condition information.", action="store_true")
	parser.add_argument("--error", help="Enable exceptions and print output. Monsters here.", action="store_true")
	parser.add_argument("-t", "--timeout", type=int, help="Timeout for Z3.")
	parser.add_argument("-d", "--debug", help="Enable debug .log file.", action="store_true")
	parser.add_argument("-v", "--verbose", help="Verbose output, print everything.", action="store_true")
	parser.add_argument("-r", "--report", help="Create .report file.", action="store_true")
	args = parser.parse_args()

	if args.timeout:
		global_params.TIMEOUT = args.timeout

	global_params.PRINT_PATHS = 1 if args.paths else 0
	global_params.PRINT_MODE = 1 if args.verbose else 0
	global_params.REPORT_MODE = 1 if args.report else 0
	global_params.DEBUG_MODE = 1 if args.debug else 0
	global_params.IGNORE_EXCEPTIONS = 1 if args.error else 0

	# print("Source is %s, contract is %s"% (args.source, args.contract))

	if not cmd_exists("disasm"):
		print "disasm is missing. Please install go-ethereum and make sure disasm is in the path."
		return

	if not cmd_exists("solc"):
		print "solc is missing. Please install the solidity compiler and make sure solc is in the path."
		return

	# Compile first

	solc_cmd = "solc --optimize --bin-runtime %s"

	FNULL = open(os.devnull, 'w')

	solc_p = subprocess.Popen(shlex.split(solc_cmd % args.source), stdout = subprocess.PIPE, stderr=FNULL)
	solc_out = solc_p.communicate()

	bin_str = ""
	try:
		bin_str = re.search(r"part: \n(.*?)\n", solc_out[0]).groups()[0]
	except:
		print("Compilation failed. Please fix any errors in the source code and ensure that compiling with your global solc produces a valid binary.")
		return

	bin_str += "\0"

	disasm_out = ""
	try:
		disasm_p = subprocess.Popen(shlex.split('disasm'), stdout=subprocess.PIPE, stdin=subprocess.PIPE)
		disasm_out = disasm_p.communicate(input=bin_str)[0]

	except:
		print "Disassembly failed."

	# Run symExec

	with open(args.source+'.evm', 'w') as of:
		of.write(disasm_out)

	# TODO: Do this as an import and run, instead of a shell call

	os.system('python symExec.py %s.evm' % (args.source))

	if not args.evm:
		os.system('rm %s.evm' % (args.source))


if __name__ == '__main__':
	main()